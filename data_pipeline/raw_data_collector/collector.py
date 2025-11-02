import os
import json
import socketio
from pathlib import Path

# --- Configuração ---
BROKER_URL = os.getenv('BROKER_URL', 'http://localhost:3000')
RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', '/data/raw_data'))

print(f"[COLLECTOR] Conectando ao Broker em {BROKER_URL}")
print(f"[COLLECTOR] Salvando dados em {RAW_DATA_PATH}")

current_session_id = None
sio = socketio.Client()

@sio.event
def connect():
    print('[COLLECTOR] Conectado ao Broker')

@sio.event
def disconnect():
    print('[COLLECTOR] Desconectado do Broker')

@sio.on('hasFinished')
def on_race_finished(data):
    """Gatilho para parar a coleta para a sessão atual."""
    global current_session_id
    session_id = data.get('sessionId')
    print(f"[COLLECTOR] Corrida finalizada. Session ID: {session_id}")
    if current_session_id == session_id:
        current_session_id = None
        print(f"[COLLECTOR] Coleta para a sessão {session_id} encerrada.")

@sio.on('gameEvent')
def on_game_event(data):
    """
    Handler para TODOS os eventos de jogo.
    Ele inicia a coleta e salva os eventos em um arquivo.
    """
    global current_session_id
    event_type = data.get('eventType')
    session_id = data.get('sessionId')

    # Se for o evento de início, configura a sessão
    if event_type == 'raceStarted':
        if not session_id:
            print("[COLLECTOR] Erro: evento 'raceStarted' sem 'sessionId'.")
            return
        current_session_id = session_id
        print(f"[COLLECTOR] Nova corrida iniciada. Session ID: {current_session_id}")
        session_path = RAW_DATA_PATH / current_session_id
        session_path.mkdir(parents=True, exist_ok=True)
        print(f"[COLLECTOR] Diretório da sessão criado em: {session_path}")
    
    # Salva TODOS os gameEvents (start, collision, finish, etc.)
    if not current_session_id or session_id != current_session_id:
        return
    try:
        file_name = 'game_events.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception as e:
        print(f"[COLLECTOR] Erro ao salvar evento de jogo: {e}")

@sio.on('eSense')
def on_esense(data):
    """
    Handler para os dados de EEG. Salva no arquivo do jogador correspondente.
    """
    if not current_session_id:
        return
    player_id = data.get('player')
    if not player_id:
        return
    try:
        file_name = f'player_{player_id}_eeg.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception as e:
        print(f"[COLLECTOR] Erro ao salvar dados para o player {player_id}: {e}")

if __name__ == '__main__':
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
    sio.connect(BROKER_URL, wait=True, wait_timeout=10, transports='websocket')
    sio.wait()