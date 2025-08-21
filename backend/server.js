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

let lastData = {};
// DB (SQLite)
let db;
try {
  db = require('./db');
} catch (e) {
  console.warn('DB desabilitado (better-sqlite3 ausente?)');
}

// REST: opcional, receber via HTTP
app.post('/api/data', (req, res) => {
  lastData = req.body;
  io.emit('data', lastData);
  if (db) db.insertReading({ ts: Date.now(), totalLiters: lastData.totalLiters, flowLmin: lastData.flowLmin });
  res.send({ status: 'ok' });
});

// REST: dados atuais
app.get('/api/current', (req, res) => {
  res.json(lastData);
});

// Histórico: /api/history?from=timestamp_ms&to=timestamp_ms&limit=N
app.get('/api/history', (req, res) => {
  if (!db) return res.json({ history: [], note: 'DB indisponível' });
  const { from, to, limit } = req.query;
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
  lastData = JSON.parse(payload.toString());
  if (db) db.insertReading({ ts: Date.now(), totalLiters: lastData.totalLiters, flowLmin: lastData.flowLmin });
    io.emit('data', lastData);
  } catch (e) {
    console.error('Invalid MQTT payload', e);
  }
});

server.listen(PORT, () => {
  console.log(`Backend + Socket.IO em http://localhost:${PORT}`);
});
