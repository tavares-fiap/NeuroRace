import os
import json
import socketio
from pathlib import Path

# --- Configuração ---
BROKER_URL = os.getenv('BROKER_URL', 'http://localhost:3000')
# O caminho DENTRO do container onde os dados serão salvos
RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', '/data'))

print(f"[COLLECTOR] Conectando ao Broker em {BROKER_URL}")
print(f"[COLLECTOR] Salvando dados em {RAW_DATA_PATH}")

# --- Estado da Sessão ---
# Usamos uma variável global simples para rastrear a sessão atual.
# Em um sistema mais complexo, usaríamos um banco de dados de estado como Redis.
current_session_id = None

# --- Cliente Socket.IO ---
sio = socketio.Client()

@sio.event
def connect():
    print('[COLLECTOR] Conectado ao Broker')

@sio.event
def disconnect():
    print('[COLLECTOR] Desconectado do Broker')

@sio.on('raceStarted')
def on_race_started(data):
    """
    Este evento é o GATILHO para começar a coletar.
    Ele nos informa o ID da sessão para que possamos criar os arquivos corretos.
    """
    global current_session_id
    session_id = data.get('sessionId')
    if not session_id:
        print("[COLLECTOR] Erro: evento 'raceStarted' sem 'sessionId'.")
        return

    current_session_id = session_id
    print(f"[COLLECTOR] Nova corrida iniciada. Session ID: {current_session_id}")
    
    # Cria o diretório para a sessão se não existir
    session_path = RAW_DATA_PATH / current_session_id
    session_path.mkdir(parents=True, exist_ok=True)
    print(f"[COLLECTOR] Diretório da sessão criado em: {session_path}")

@sio.on('hasFinished')
def on_race_finished(data):
    """
    Este evento é o GATILHO para parar a coleta para a sessão atual.
    """
    global current_session_id
    session_id = data.get('sessionId')
    print(f"[COLLECTOR] Corrida finalizada. Session ID: {session_id}")
    if current_session_id == session_id:
        current_session_id = None
        print(f"[COLLECTOR] Coleta para a sessão {session_id} encerrada.")

@sio.on('eSense')
def on_esense(data):
    """
    Este é o handler principal. Ele recebe os dados de EEG e os salva
    no arquivo correspondente ao jogador da sessão atual.
    """
    if not current_session_id:
        # Ignora dados se não estivermos em uma sessão de corrida ativa
        return
        
    player_id = data.get('player')
    if not player_id:
        return

    try:
        # Define o nome do arquivo e o caminho completo
        file_name = f'player_{player_id}_eeg.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        
        # Abre o arquivo em modo 'append' e escreve a nova linha JSON
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
            
    except Exception as e:
        print(f"[COLLECTOR] Erro ao salvar dados para o player {player_id}: {e}")

if __name__ == '__main__':
    # Garante que o diretório base exista
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
    
    # Inicia a conexão com o broker e espera por eventos
    sio.connect(BROKER_URL, wait=True, wait_timeout=10, transports='websocket')
    sio.wait()