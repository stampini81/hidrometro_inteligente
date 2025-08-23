from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
import os
from collections import deque
from threading import Lock
import time
import re
import json
import jwt
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from functools import wraps

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# SocketIO (usar eventlet ou gevent no run)
socketio = SocketIO(app, cors_allowed_origins='*')

# Import models
from app.models import cliente_model, dispositivo_model, faturamento_model
from app.models.dispositivo_model import Dispositivo, Leitura

# Histórico em memória
_history = deque(maxlen=app.config.get('HISTORY_LIMIT', 1000))
_last_data = {}
_hist_lock = Lock()

# Config auth
_JWT_SECRET = app.config.get('SECRET_KEY', 'dev')
_JWT_EXP_MIN = 60

# Usuários simples em memória (poderia ser tabela)
_USERS = { 'admin': {'password': os.environ.get('ADMIN_PASSWORD','admin')} }

def create_token(username):
    payload = { 'sub': username, 'exp': datetime.utcnow() + timedelta(minutes=_JWT_EXP_MIN) }
    return jwt.encode(payload, _JWT_SECRET, algorithm='HS256')

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization','')
        if not auth.startswith('Bearer '):
            return jsonify({'error':'missing token'}), 401
        token = auth.split(' ',1)[1]
        try:
            jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])
        except Exception as e:
            return jsonify({'error':'invalid token'}), 401
        return f(*args, **kwargs)
    return wrapper

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    u = data.get('username'); p = data.get('password')
    user = _USERS.get(u)
    if not user or user['password'] != p:
        return jsonify({'error':'invalid credentials'}), 401
    return jsonify({'token': create_token(u)})

# MQTT Setup
_mqtt_client = None

def _normalize_payload(obj):
    o = obj or {}
    total = o.get('totalLiters') or o.get('total') or 0
    flow = o.get('flowLmin') or o.get('flowRate') or 0
    ts = o.get('ts') or int(time.time()*1000)
    serial = o.get('numeroSerie') or o.get('serial') or o.get('numero_serie')
    return { 'ts': int(ts), 'totalLiters': float(total), 'flowLmin': float(flow), 'numero_serie': serial }

# MQTT callbacks
def _on_mqtt_connect(client, userdata, flags, rc):
    topic = app.config['MQTT_TOPIC_DADOS']
    try:
        client.subscribe(topic)
        print(f"[MQTT] Conectado rc={rc} subscrito {topic}")
    except Exception as e:
        print('[MQTT] Erro subscribe', e)

def _persist_leitura(data):
    # tenta correlacionar dispositivo se numero_serie no payload
    dispositivo_id = None
    serial = data.get('numero_serie')
    if serial:
        disp = Dispositivo.query.filter_by(numero_serie=serial).first()
        if disp:
            dispositivo_id = disp.id_dispositivo
    try:
        leitura = Leitura(
            dispositivo_id=dispositivo_id if dispositivo_id else 1, # se None e quiser rejeitar, ajuste
            data_hora=datetime.utcnow(),
            consumo_litros=data['totalLiters'],
            total_liters=data['totalLiters'],
            flow_lmin=data['flowLmin']
        )
        db.session.add(leitura)
        db.session.commit()
    except Exception:
        db.session.rollback()

def _on_mqtt_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
    except Exception:
        print('[MQTT] payload inválido')
        return
    data = _normalize_payload(payload)
    with _hist_lock:
        _last_data.update(data)
        _history.append({'ts': data['ts'], 'totalLiters': data['totalLiters'], 'flowLmin': data['flowLmin']})
    _persist_leitura(data)
    socketio.emit('data', data)

# Inicializa MQTT
def init_mqtt():
    global _mqtt_client
    url = app.config['MQTT_URL']
    # Extrai host e porta de formato mqtt://host:port
    m = re.match(r'mqtt://([^:/]+)(?::(\d+))?', url)
    host = 'broker.hivemq.com'
    port = 1883
    if m:
        host = m.group(1)
        if m.group(2):
            port = int(m.group(2))
    _mqtt_client = mqtt.Client()
    _mqtt_client.on_connect = _on_mqtt_connect
    _mqtt_client.on_message = _on_mqtt_message
    try:
        _mqtt_client.connect(host, port, 60)
        _mqtt_client.loop_start()
    except Exception as e:
        print('[MQTT] Falha ao conectar', e)

# API Blueprint simplificado via rotas diretas
@app.route('/api/current')
def api_current():
    with _hist_lock:
        return jsonify(_last_data)

@app.route('/api/history')
def api_history():
    limit = int(request.args.get('limit', 200))
    with _hist_lock:
        data = list(_history)[-limit:]
    return jsonify({'history': data})

@app.route('/api/data', methods=['POST'])
@require_auth
def api_data():
    payload = request.get_json(silent=True) or {}
    data = _normalize_payload(payload)
    with _hist_lock:
        _last_data.update(data)
        _history.append({'ts': data['ts'], 'totalLiters': data['totalLiters'], 'flowLmin': data['flowLmin']})
    _persist_leitura(data)
    socketio.emit('data', data)
    return jsonify({'status': 'ok'})

@app.route('/api/cmd', methods=['POST', 'GET'])
@require_auth
def api_cmd():
    action = None
    value = None
    if request.method == 'POST':
        j = request.get_json(silent=True) or {}
        action = j.get('action')
        value = j.get('value')
    else:
        action = request.args.get('action')
        value = request.args.get('value')
    cmd = {'action': action}
    if value is not None:
        try:
            cmd['value'] = float(value)
        except ValueError:
            cmd['value'] = value
    try:
        if _mqtt_client and action:
            _mqtt_client.publish(app.config['MQTT_TOPIC_CMD'], json.dumps(cmd))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'sent', 'cmd': cmd})

@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/debug/history-size')
@require_auth
def debug_history_size():
    with _hist_lock:
        size = len(_history)
    return jsonify({'historySize': size, 'limit': _history.maxlen})

# SocketIO evento inicial
@socketio.on('connect')
def on_connect():
    with _hist_lock:
        if _history:
            socketio.emit('history:init', list(_history)[-200:])
        if _last_data:
            socketio.emit('data', _last_data)

# Import controllers html existentes
from app.controllers import cliente_controller, dispositivo_controller, tipo_dispositivo_controller, faturamento_controller

with app.app_context():
    db.create_all()
    init_mqtt()

