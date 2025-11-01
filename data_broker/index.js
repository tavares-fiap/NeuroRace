const io = require('socket.io')(3000);  // abre WS em 3000
console.log("Broker conectado, aguardando conexao...")
io.on('connection', socket => {
  console.log('Cliente conectado:', socket.id);
  const forward = (event) => (payload) => {
    console.log(`[${event}] recebido:`, payload);
    socket.broadcast.emit(event, payload);
  };
  socket.on('blink',   forward('blink'));
  socket.on('eSense',  forward('eSense'));

  socket.on('raceStarted', forward('raceStarted'));
  socket.on('hasFinished',  forward('hasFinished'));
});
