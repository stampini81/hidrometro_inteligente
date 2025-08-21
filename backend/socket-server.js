const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const bodyParser = require('body-parser');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(bodyParser.json());

let lastData = {};

app.post('/api/data', (req, res) => {
  lastData = req.body;
  io.emit('data', lastData); // envia para todos os clientes conectados
  res.send({ status: 'ok' });
});

app.get('/api/current', (req, res) => {
  res.json(lastData);
});

io.on('connection', (socket) => {
  socket.emit('data', lastData);
});

server.listen(3001, () => {
  console.log('Socket.IO server rodando em http://localhost:3001');
});
