from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, session
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
from datetime import datetime, timedelta, timezone
import paho.mqtt.client as mqtt
from functools import wraps
from sqlalchemy import inspect

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# SocketIO (usar eventlet ou gevent no run)
socketio = SocketIO(app, cors_allowed_origins='*')

# Import models
from app.models import cliente_model, dispositivo_model, faturamento_model, usuario_model
from app.models.dispositivo_model import Dispositivo, Leitura
from app.models.usuario_model import Usuario

# Histórico em memória
_history = deque(maxlen=app.config.get('HISTORY_LIMIT', 1000))
_last_data = {}
_hist_lock = Lock()

# Config auth
_JWT_SECRET = app.config.get('SECRET_KEY', 'dev')
_JWT_EXP_MIN = int(os.environ.get('JWT_EXP_MINUTES', '60'))

# Funções de auth persistente

def create_token(username, role):
    payload = { 'sub': username, 'role': role, 'exp': datetime.now(timezone.utc) + timedelta(minutes=_JWT_EXP_MIN) }
    return jwt.encode(payload, _JWT_SECRET, algorithm='HS256')

def _decode_token(token):
    return jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization','')
        if not auth.startswith('Bearer '):
            return jsonify({'error':'missing token'}), 401
        token = auth.split(' ',1)[1]
        try:
            payload = _decode_token(token)
            request.user = payload
        except Exception:
            return jsonify({'error':'invalid token'}), 401
        return f(*args, **kwargs)
    return wrapper

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not getattr(request, 'user', None):
                return jsonify({'error':'unauthorized'}), 401
            user_role = request.user.get('role')
            if roles and user_role not in roles:
                return jsonify({'error':'forbidden'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    u = data.get('username'); p = data.get('password')
    if not u or not p:
        return jsonify({'error':'invalid credentials'}), 401
    user = Usuario.query.filter_by(username=u, active=True).first()
    if not user or not user.check_password(p):
        # Log somente em modo DEBUG para auxiliar diagnóstico de falha de login
        if app.config.get('DEBUG'):
            print(f"[AUTH] Falha login user='{u}' exists={bool(user)} json_keys={list(data.keys())}")
        return jsonify({'error':'invalid credentials'}), 401
    return jsonify({'token': create_token(user.username, user.role), 'role': user.role})

# ------------------ Autenticação para interface web (session) ------------------

def login_required_view(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login_page', next=request.path))
        return f(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Usuario.query.filter_by(username=username, active=True).first()
        if not user or not user.check_password(password):
            flash('Credenciais inválidas', 'danger')
            return render_template('login.html')
        # Armazena sessão simples
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        nxt = request.args.get('next') or url_for('listar_clientes')
        return redirect(nxt)
    # GET
    if session.get('user_id'):
        return redirect(url_for('listar_clientes'))
    return render_template('login.html')

@app.route('/logout')
def logout_page():
    session.clear()
    return redirect(url_for('login_page'))

# MQTT Setup
_mqtt_client = None

def _normalize_payload(obj):
    o = obj or {}
    total = o.get('totalLiters') or o.get('total') or 0
    flow = o.get('flowLmin') or o.get('flowRate') or 0
    ts = o.get('ts') or int(time.time()*1000)
    serial = o.get('numeroSerie') or o.get('serial') or o.get('numero_serie')
    if serial:
        serial = str(serial).strip().upper()
    else:
        # fallback serial default se configurado
        default_serial = app.config.get('DEFAULT_DEVICE_SERIAL')
        if default_serial:
            serial = str(default_serial).strip().upper()
    return { 'ts': int(ts), 'totalLiters': float(total), 'flowLmin': float(flow), 'numero_serie': serial }

# MQTT callbacks
def _on_mqtt_connect(client, userdata, flags, rc):
    # Sempre tenta assinar o tópico configurado e também o padrão esperado pelo firmware
    configured = app.config['MQTT_TOPIC_DADOS']
    default_fw = 'hidrometro/leandro/dados'
    extra_topics = []
    try:
        client.subscribe(configured)
        if configured != default_fw:
            extra_topics.append(default_fw)
        # Fallback wildcard para facilitar debug (pode ser removido em produção)
        base_wildcard = None
        # Se o tópico tiver ao menos 2 segmentos, usa os dois primeiros como base
        parts = configured.split('/')
        if len(parts) >= 2:
            base_wildcard = f"{parts[0]}/{parts[1]}/#"
        for t in extra_topics:
            client.subscribe(t)
        if base_wildcard and base_wildcard not in (configured, default_fw):
            client.subscribe(base_wildcard)
        subscribed = [configured] + extra_topics + ([base_wildcard] if base_wildcard else [])
        print(f"[MQTT] Conectado rc={rc} subscrito: {', '.join(subscribed)}")
    except Exception as e:
        print('[MQTT] Erro subscribe', e)

def _persist_leitura(data):
    dispositivo_id = None
    serial = data.get('numero_serie')
    if serial:
        disp = Dispositivo.query.filter_by(numero_serie=serial).first()
        if disp:
            dispositivo_id = disp.id_dispositivo
    if dispositivo_id is None:
        # Sem dispositivo correspondente: ignorar persistência para evitar FK inválida
        return
    try:
        leitura = Leitura(
            dispositivo_id=dispositivo_id,
            data_hora=datetime.now(timezone.utc),
            consumo_litros=data['totalLiters'],
            total_liters=data['totalLiters'],
            flow_lmin=data['flowLmin']
        )
        db.session.add(leitura)
        db.session.commit()
    except Exception:
        db.session.rollback()

def _on_mqtt_message(client, userdata, msg):
    # Log bruto (limitando tamanho para evitar flood)
    try:
        raw = msg.payload.decode('utf-8', errors='replace')
    except Exception:
        raw = '<decode-error>'
    print(f"[MQTT] RECEBIDO topic={msg.topic} bytes={len(msg.payload)} raw={raw[:200]}")
    try:
        payload = json.loads(raw)
    except Exception as e:
        print('[MQTT] payload inválido (JSON parse falhou):', e)
        return
    data = _normalize_payload(payload)
    with _hist_lock:
        _last_data.update(data)
        _history.append({'ts': data['ts'], 'totalLiters': data['totalLiters'], 'flowLmin': data['flowLmin']})
    _persist_leitura(data)
    print(f"[MQTT] NORMALIZADO ts={data['ts']} total={data['totalLiters']} flow={data['flowLmin']} serial={data.get('numero_serie')}")
    socketio.emit('data', data)

# Inicializa MQTT
def init_mqtt():
    global _mqtt_client
    url = app.config['MQTT_URL']
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
@require_role('admin','user')
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
@require_role('admin')
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
@require_role('admin')
def debug_history_size():
    with _hist_lock:
        size = len(_history)
    return jsonify({'historySize': size, 'limit': _history.maxlen})

@socketio.on('connect')
def on_connect():
    with _hist_lock:
        if _history:
            socketio.emit('history:init', list(_history)[-200:])
        if _last_data:
            socketio.emit('data', _last_data)

from app.controllers import cliente_controller, dispositivo_controller, tipo_dispositivo_controller, faturamento_controller

with app.app_context():
    # Protege criação do admin caso tabelas ainda não existam (fase de migração inicial)
    try:
        insp = inspect(db.engine)
        if 'Usuario' in insp.get_table_names():
            if not Usuario.query.filter_by(username='admin').first():
                admin = Usuario(username='admin', role='admin')
                admin.set_password(os.environ.get('ADMIN_PASSWORD','admin'))
                db.session.add(admin)
                try:
                    db.session.commit()
                    print('[INIT] Usuário admin criado (username=admin, senha=ENV ADMIN_PASSWORD ou "admin" se não definido)')
                except Exception:
                    db.session.rollback()
    except Exception as e:
        print('[INIT] Skip admin creation (tabelas indisponíveis):', e)
    # Log básico das rotas para debug
    try:
        print('[INIT] Rotas registradas:')
        for r in sorted([(list(rule.methods), rule.rule) for rule in app.url_map.iter_rules()], key=lambda x: x[1]):
            methods = ','.join(sorted(m for m in r[0] if m in ('GET','POST','PUT','DELETE')))
            print(f'  {methods:15s} {r[1]}')
    except Exception as _e:
        pass
    init_mqtt()

# Endpoint de debug opcional para inspecionar usuários e validar senha padrão
if os.environ.get('DEBUG_AUTH') == '1':
    @app.route('/api/debug/auth')
    def debug_auth():
        try:
            users = [u.username for u in Usuario.query.all()]
            admin = Usuario.query.filter_by(username='admin').first()
            test_pass = os.environ.get('ADMIN_PASSWORD','admin')
            admin_ok = bool(admin and admin.check_password(test_pass))
            return jsonify({'users': users, 'admin_password_ok_with_ENV_or_default': admin_ok, 'expected_admin_password_env': bool(os.environ.get('ADMIN_PASSWORD'))})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

