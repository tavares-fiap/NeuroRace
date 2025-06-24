const io = require('socket.io')(3000);  // abre WS em 3000
io.on('connection', socket => {
  console.log('Cliente conectado:', socket.id);
  socket.on('attention', data => {
    console.log("\n=-=-=-=-received data=-=-=-=-")
    console.log(data)
    socket.broadcast.emit('attention', data);
  });
});
