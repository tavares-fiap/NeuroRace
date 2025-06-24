const express = require('express');
const http = require('http');
const socketIO = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIO(server);

app.use(express.static('public'));

io.on('connection', (socket) => {
  console.log('Cliente conectado ao broker:', socket.id);

  socket.on('attention', (data) => {
    console.log("\n--- Attention recebido do acquisition.py ---");
    console.log(data);

    // Reenvia o dado para todos os dashboards conectados
    io.emit('attention', data);
  });

  socket.on('disconnect', () => {
    console.log('Cliente desconectado:', socket.id);
  });
});

server.listen(3000, () => {
  console.log('Broker + Dashboard rodando na porta 3000');
});