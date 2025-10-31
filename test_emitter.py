import socketio
import time
import uuid

BROKER_URL = 'http://localhost:3000'

sio = socketio.Client()

@sio.event
def connect():
    print('Conectado ao Broker como "Simulador de Jogo"')

@sio.event
def disconnect():
    print('Desconectado do Broker')

def run_test_session():
    try:
        sio.connect(BROKER_URL, transports='websocket')
        
        # 1. Gerar um ID de sessão único para esta corrida de teste
        session_id = f"test-session-{uuid.uuid4()}"
        print(f"\n--- Iniciando corrida de teste com Session ID: {session_id} ---")
        
        # 2. Emitir o evento de início da corrida
        sio.emit('raceStarted', {'sessionId': session_id})
        print(f"Evento 'raceStarted' enviado.")
        
        # 3. Simular a duração da corrida (esperar os dados de EEG chegarem)
        race_duration_seconds = 10
        print(f"Aguardando {race_duration_seconds} segundos (simulando a corrida)...")
        time.sleep(race_duration_seconds)
        
        # 4. Emitir o evento de fim da corrida
        sio.emit('hasFinished', {'sessionId': session_id})
        print(f"Evento 'hasFinished' enviado.")
        
        print("\n--- Teste finalizado com sucesso! ---")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == '__main__':
    run_test_session()