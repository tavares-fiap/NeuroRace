# broker_client.py
import socketio

class WebSocketBrokerClient:
    def __init__(self, broker_url: str):
        """
        broker_url: ex: 'http://localhost:3000' ou 'http://192.168.15.10:3000'
        """
        self.broker_url = broker_url
        self.sio = socketio.Client()

    def connect_to_broker(self):
        if not self.sio.connected:
            try:
                print(f"Tentando conectar ao Broker em {self.broker_url}...")
                self.sio.connect(self.broker_url)
                print("Conectado ao Broker com sucesso.")
            except socketio.exceptions.ConnectionError as e:
                print(f"Não foi possível conectar ao Broker em {self.broker_url}. Erro: {e}")
                # aqui você pode escolher: ou relança, ou apenas loga
                raise

    def send_event(self, event_type: str, payload: dict | None = None):
        # Garante que está conectado, mas NÃO fecha depois
        self.connect_to_broker()
        try:
            self.sio.emit(event_type, payload)
            print(f"Evento '{event_type}' enviado para o Broker.")
        except Exception as e:
            print(f"Erro ao enviar evento '{event_type}' ao Broker: {e}")

    def close(self):
        if self.sio and self.sio.connected:
            self.sio.disconnect()
            print("Conexão com o Broker encerrada.")

    def __enter__(self):
        self.connect_to_broker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
