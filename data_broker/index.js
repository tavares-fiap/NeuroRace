// server.js
const io = require('socket.io')(3000, {
  cors: {
    origin: ['http://localhost:8080', 'http://127.0.0.1:8080', 'http://localhost:5173', 'http://localhost:8000'],
    methods: ['GET', 'POST'],
    credentials: true
  }
});

console.log('Broker conectado, aguardando conexões em :3000 ...');

io.on('connection', (socket) => {
  console.log('Cliente conectado:', socket.id);

  // Recebe do acquisition service ou de qualquer cliente
  socket.on('attention', (data) => {
    console.log('\n=-=-=-=- attention recebido =-=-=-=-');
    console.log(data);
    // Reenvia para TODOS (inclui quem enviou)
    io.emit('attention', {
      player: data?.player ?? 'unknown',
      attention: Number(data?.attention) ?? 0,
      timestamp: data?.timestamp ?? Date.now()
    });
  });

  socket.on('disconnect', (reason) => {
    console.log('Cliente desconectado:', socket.id, 'motivo:', reason);
  });
});

// ====== (OPCIONAL) gerador de teste ======
// Descomente para validar o frontend mesmo sem o acquisition conectado
// setInterval(() => {
//   io.emit('attention', {
//     player: 'TEST',
//     attention: Math.floor(Math.random() * 101),
//     timestamp: Date.now()
//   });
// }, 1000);
