import socketio
import time
import uuid
import random

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
        
        session_id = f"test-session-{uuid.uuid4()}"
        print(f"\n--- Iniciando corrida de teste com Session ID: {session_id} ---")
        
        # O evento de início agora pode conter metadados, como os jogadores
        sio.emit('raceStarted', {'sessionId': session_id, 'players': [1, 2]})
        print(f"Evento 'raceStarted' enviado.")
        
        # Simula uma corrida de 15 segundos, enviando eventos aleatórios
        race_duration_seconds = 15
        print(f"Simulando corrida de {race_duration_seconds} segundos com eventos...")

        for second in range(race_duration_seconds):
            time.sleep(1)
            # A cada segundo, há uma chance de um evento de jogo acontecer
            if random.random() < 0.2: # 20% de chance de evento por segundo
                event_type = random.choice(['collision', 'overtake'])
                player_id = random.choice([1, 2])
                
                game_event = {
                    'sessionId': session_id,
                    'player': player_id,
                    'eventType': event_type,
                    'timestamp': int(time.time() * 1000)
                }
                sio.emit('gameEvent', game_event)
                print(f"  -> Evento enviado: Jogador {player_id} sofreu '{event_type}'")
        
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