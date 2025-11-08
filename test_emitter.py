import socketio
import time
import random

BROKER_URL = 'http://localhost:3000'

# --- Cenários de Teste ---
# Mude esta variável para testar diferentes configurações de jogadores
# Opções: "REAL_VS_REAL", "REAL_VS_BOT", "REAL_VS_ANONYMOUS"
CENARIO_DE_TESTE = "REAL_VS_REAL"

sio = socketio.Client()

@sio.event
def connect():
    print('Conectado ao Broker como "Simulador de Jogo"')

@sio.event
def disconnect():
    print('Desconectado do Broker')

def get_player_configs():
    """Retorna a configuração dos jogadores com base no cenário de teste."""
    if CENARIO_DE_TESTE == "REAL_VS_BOT":
        return {
            "player1": {"name": "Jogador Real 1", "phoneNumber": "11988888888", "source": "real"},
            "player2": {"name": "Bot Oponente", "phoneNumber": "", "source": "bot"}
        }
    elif CENARIO_DE_TESTE == "REAL_VS_ANONYMOUS":
        return {
            "player1": {"name": "Jogador Real 1", "phoneNumber": "11988888888", "source": "real"},
            "player2": {"name": "Visitante", "phoneNumber": "", "source": "anonymous"}
        }
    # Padrão: REAL_VS_REAL
    else:
        return {
            "player1": {"name": "Jogador Alpha", "phoneNumber": "11988888888", "source": "real"},
            "player2": {"name": "Jogador Beta", "phoneNumber": "11977777777", "source": "real"}
        }

def run_test_session():
    try:
        sio.connect(BROKER_URL, transports='websocket')
        
        print(f"\n--- Iniciando corrida de teste (Cenário: {CENARIO_DE_TESTE}) ---")
        
        # 1. Enviar o evento de configuração (sem sessionId ou timestamp)
        configs = get_player_configs()
        sio.emit('raceConfigure', configs)
        print("Evento 'raceConfigure' enviado.")
        
        # Pequena pausa para simular o tempo entre a configuração e o início
        time.sleep(2)
        
        # 2. Enviar o evento de início da corrida
        sio.emit('raceStarted', {})
        print("Evento 'raceStarted' enviado.")
        
        # 3. Simular uma corrida de 15 segundos, enviando eventos aleatórios
        race_duration_seconds = 15
        print(f"Simulando corrida de {race_duration_seconds} segundos com eventos...")

        for _ in range(race_duration_seconds):
            time.sleep(1)
            if random.random() < 0.2: # 20% de chance de evento por segundo
                event_type = random.choice(['collision', 'overtake', 'handGesture'])
                player_id = random.choice([1, 2])
                
                sio.emit(event_type, {'player': player_id})
                print(f"  -> Evento '{event_type}' enviado para Jogador {player_id}")
        
        # 4. Simular o fim da corrida, com cada jogador terminando em um tempo diferente
        print("Corrida terminando... Enviando tempos finais.")
        
        # Jogador 2 termina primeiro (vencedor)
        sio.emit('hasFinished', {'player': 2, 'raceTimeSeconds': 121.5})
        print("Evento 'hasFinished' enviado para Jogador 2.")
        
        time.sleep(1.5) # Jogador 1 termina um pouco depois
        
        # Jogador 1 termina
        sio.emit('hasFinished', {'player': 1, 'raceTimeSeconds': 123.0})
        print("Evento 'hasFinished' enviado para Jogador 1.")

        # O pipelineTrigger não é mais necessário aqui, pois o coletor cuidará disso.
        
        print("\n--- Teste finalizado com sucesso! ---")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == '__main__':
    run_test_session()