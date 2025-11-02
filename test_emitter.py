# test_emitter.py (versão 3 - com identificação de usuário por email e tempos de corrida)
import socketio
import time
import uuid
import random

BROKER_URL = 'http://localhost:3000'

# --- Simulação de Jogadores ---
# Para cada teste, usaremos estes dois jogadores.
# Você pode mudar os emails para testar a criação de novos perfis.
PLAYER_1_EMAIL = "jogador.alpha@neurorace.com"
PLAYER_2_EMAIL = "jogador.beta@neurorace.com"

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
        
        # 1. Emitir o evento de início da corrida com o mapeamento de usuários
        start_payload = {
            'sessionId': session_id,
            'users': [
                {'playerId': 1, 'email': PLAYER_1_EMAIL},
                {'playerId': 2, 'email': PLAYER_2_EMAIL}
            ],
            'eventType': 'raceStarted', # Adicionamos para consistência com o gameEvent
            'timestamp': int(time.time() * 1000)
        }
        sio.emit('gameEvent', start_payload)
        print(f"Evento 'raceStarted' enviado com mapeamento de usuários.")
        
        # 2. Simular uma corrida de 15 segundos, enviando eventos aleatórios
        race_duration_seconds = 15
        print(f"Simulando corrida de {race_duration_seconds} segundos com eventos de jogo...")

        for second in range(race_duration_seconds):
            time.sleep(1)
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
                print(f"  -> Evento de jogo enviado: Jogador {player_id} sofreu '{event_type}'")
        
        # 3. Simular o fim da corrida, com cada jogador terminando em um tempo diferente
        print("Corrida terminando... Enviando tempos finais.")
        
        # Jogador 2 termina primeiro (vencedor)
        finish_payload_p2 = {
            'sessionId': session_id,
            'player': 2,
            'eventType': 'hasFinished',
            'raceTimeSeconds': 121.5,
            'timestamp': int(time.time() * 1000)
        }
        sio.emit('gameEvent', finish_payload_p2)
        print(f"Evento 'hasFinished' enviado para Jogador 2 com tempo {finish_payload_p2['raceTimeSeconds']}s.")
        
        time.sleep(1.5) # Jogador 1 termina um pouco depois
        
        # Jogador 1 termina
        finish_payload_p1 = {
            'sessionId': session_id,
            'player': 1,
            'eventType': 'hasFinished',
            'raceTimeSeconds': 123.0,
            'timestamp': int(time.time() * 1000)
        }
        sio.emit('gameEvent', finish_payload_p1)
        print(f"Evento 'hasFinished' enviado para Jogador 1 com tempo {finish_payload_p1['raceTimeSeconds']}s.")

        # 4. Enviar o evento final que dispara o pipeline
        # Este evento não precisa de payload, apenas sinaliza o fim da coleta
        sio.emit('hasFinished', {'sessionId': session_id})
        print(f"Evento final 'hasFinished' enviado para disparar o pipeline.")

        print("\n--- Teste finalizado com sucesso! ---")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == '__main__':
    run_test_session()