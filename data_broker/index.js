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
  const forward = (event) => (payload) => {
    console.log(`[${event}] recebido:`, payload);
    socket.broadcast.emit(event, payload);
  };
  socket.on('blink',   forward('blink'));
  socket.on('eSense',  forward('eSense'));

  socket.on('raceStarted', forward('raceStarted'));
  socket.on('hasFinished',  forward('hasFinished'));

  socket.on('gameEvent', forward('gameEvent'));
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
