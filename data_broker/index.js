// data_broker/index.js

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

  // Função genérica para retransmitir qualquer evento que ela receba.
  const forward = (event) => (payload) => {
    console.log(`[${event}] recebido:`, payload);
    socket.broadcast.emit(event, payload);
  };

  // --- Lista de todos os eventos conhecidos que o broker deve retransmitir ---

  // Eventos de Dados de EEG
  socket.on('eSense', forward('eSense'));
  socket.on('blink', forward('blink'));
  
  // Evento de Gesto do MediaPipe
  socket.on('handGesture', forward('handGesture'));

  // Eventos de Estado da Corrida (vindos do Jogo)
  socket.on('raceConfigure', forward('raceConfigure'));
  socket.on('raceStarted', forward('raceStarted'));
  socket.on('collision', forward('collision'));
  socket.on('overtake', forward('overtake'));
  socket.on('hasFinished', forward('hasFinished'));
});