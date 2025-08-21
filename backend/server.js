const express = require('express');
const http = require('http');
const bodyParser = require('body-parser');
const mqtt = require('mqtt');
const { Server } = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

const PORT = process.env.PORT || 3000;
const MQTT_URL = process.env.MQTT_URL || 'mqtt://broker.hivemq.com:1883';
const MQTT_TOPIC = process.env.MQTT_TOPIC || 'hidrometro/leandro/dados';
const MQTT_CMD_TOPIC = process.env.MQTT_CMD_TOPIC || 'hidrometro/leandro/cmd';

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));
// Servir o frontend externo via backend, em /dashboard
app.use('/dashboard', express.static(path.join(__dirname, '..', 'frontend')));

// Healthcheck simples
app.get('/healthz', (req, res) => res.send('ok'));

let lastData = {};
// Histórico em memória (fallback quando DB indisponível)
const memHistory = []; // { ts, totalLiters, flowLmin }
const MEM_HISTORY_LIMIT = 1000;
function pushMemory(ts, totalLiters, flowLmin) {
  memHistory.push({ ts, totalLiters, flowLmin });
  if (memHistory.length > MEM_HISTORY_LIMIT) memHistory.shift();
  // Log detalhado para debug
  if (process.env.DEBUG_HISTORY) {
    console.log(
      '[pushMemory] size=%d last=%o',
      memHistory.length,
      memHistory[memHistory.length - 1]
    );
  }
}
// DB (SQLite)
let db;
try {
  db = require('./db');
} catch (e) {
  console.warn('DB desabilitado (better-sqlite3 ausente?)');
}

// REST: opcional, receber via HTTP
app.post('/api/data', (req, res) => {
  lastData = normalizePayload(req.body || {});
  io.emit('data', lastData);
  const ts = Date.now();
  if (db) db.insertReading({ ts, totalLiters: lastData.totalLiters, flowLmin: lastData.flowLmin });
  else {
    pushMemory(ts, lastData.totalLiters, lastData.flowLmin);
    if (memHistory.length % 10 === 0) console.log('[memHistory]', memHistory.length);
  }
  res.send({ status: 'ok' });
});

// REST: dados atuais
app.get('/api/current', (req, res) => {
  res.json(lastData);
});

// Debug: tamanho do histórico em memória / status DB
app.get('/api/debug/history-size', (req, res) => {
  res.json({ usingDB: !!db, memSize: memHistory.length });
});

// Histórico: /api/history?from=timestamp_ms&to=timestamp_ms&limit=N
app.get('/api/history', (req, res) => {
  const { from, to, limit } = req.query;
  if (!db) {
    // Fallback usa memória (ignora filtros para simplicidade)
    return res.json({ history: memHistory, note: 'mem' });
  }
  let rows = [];
  if (from || to) rows = db.getRange(from, to);
  else rows = db.getRecent(limit || 1000);
  res.json({ history: rows });
});

// REST: publicar comando MQTT
app.post('/api/cmd', (req, res) => {
  try {
    const cmd = req.body || {};
    client.publish(MQTT_CMD_TOPIC, JSON.stringify(cmd));
    res.json({ status: 'sent', topic: MQTT_CMD_TOPIC, cmd });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});
// GET simples via querystring: /api/cmd?action=reset ou setCalibration&value=7.5
app.get('/api/cmd', (req, res) => {
  const action = req.query.action;
  const value = req.query.value ? Number(req.query.value) : undefined;
  const cmd = value !== undefined ? { action, value } : { action };
  client.publish(MQTT_CMD_TOPIC, JSON.stringify(cmd));
  res.json({ status: 'sent', topic: MQTT_CMD_TOPIC, cmd });
});

// Socket.IO: conexão
io.on('connection', (socket) => {
  socket.emit('data', lastData);
  try {
    if (db) {
      const recent = db.getRecent(200);
      if (recent && recent.length) {
        if (process.env.DEBUG_HISTORY)
          console.log('[socket] enviando history:init (db) size=%d', recent.length);
        socket.emit('history:init', recent);
      } else if (process.env.DEBUG_HISTORY) {
        console.log('[socket] banco sem registros recentes');
      }
    } else if (typeof memHistory !== 'undefined' && memHistory.length) {
      const slice = memHistory.slice(-200);
      if (process.env.DEBUG_HISTORY)
        console.log('[socket] enviando history:init (mem) size=%d', slice.length);
      socket.emit('history:init', slice);
    } else if (process.env.DEBUG_HISTORY) {
      console.log('[socket] nenhum histórico disponível');
    }
  } catch (e) {
    console.warn('Falha ao enviar history:init', e);
  }
});

// MQTT: subscribe e bridge para Socket.IO
const client = mqtt.connect(MQTT_URL);
client.on('connect', () => {
  client.subscribe(MQTT_TOPIC, (err) => {
    if (!err) console.log('MQTT subscribed:', MQTT_TOPIC);
  });
});
client.on('message', (topic, payload) => {
  try {
    lastData = normalizePayload(JSON.parse(payload.toString()) || {});
    const ts = Date.now();
    if (db) {
      db.insertReading({ ts, totalLiters: lastData.totalLiters, flowLmin: lastData.flowLmin });
      if (process.env.DEBUG_HISTORY)
        console.log(
          '[mqtt->db] ts=%d total=%.2f flow=%.2f',
          ts,
          lastData.totalLiters,
          lastData.flowLmin
        );
    } else {
      pushMemory(ts, lastData.totalLiters, lastData.flowLmin);
      if (memHistory.length % 10 === 0) console.log('[memHistory]', memHistory.length);
    }
    io.emit('data', lastData);
  } catch (e) {
    console.error('Invalid MQTT payload', e);
  }
});

server.listen(PORT, () => {
  console.log(`Backend + Socket.IO em http://localhost:${PORT}`);
});

// Converte payloads variados para um formato canônico
function normalizePayload(obj) {
  const o = obj || {};
  const totalLiters = o.totalLiters ?? o.total ?? 0;
  const flowLmin = o.flowLmin ?? o.flowRate ?? 0;
  const ts = o.ts ?? Date.now();
  return { ts, totalLiters: Number(totalLiters) || 0, flowLmin: Number(flowLmin) || 0 };
}
