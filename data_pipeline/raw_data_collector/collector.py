import os
import json
import socketio
from pathlib import Path
import logging
import time
import uuid

# ==============================================================================
# SEÇÃO DE CONFIGURAÇÃO DO LOGGING
# ==============================================================================
log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logging.getLogger("engineio.client").setLevel(logging.WARNING)
logging.getLogger("socketio.client").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

# ==============================================================================
# SEÇÃO DE CONFIGURAÇÃO DO SERVIÇO
# ==============================================================================
BROKER_URL = os.getenv('BROKER_URL', 'http://localhost:3000')
RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', '/data/raw_data'))

log.info(f"Coletor iniciado. Conectando ao Broker em {BROKER_URL}")
log.info(f"Diretório de destino para dados brutos: {RAW_DATA_PATH}")

# --- Gerenciamento de Estado da Sessão ---
# Como não há corridas simultâneas, podemos usar variáveis globais simples.
current_session_id = None
# Dicionário para rastrear quais jogadores já terminaram a corrida.
finished_players = {}

sio = socketio.Client()

# ==============================================================================
# SEÇÃO DE HANDLERS DE EVENTOS DO SOCKET.IO
# ==============================================================================

@sio.event
def connect():
    log.info("Conectado ao Broker com sucesso. Aguardando corridas...")

@sio.event
def disconnect():
    log.warning("Desconectado do Broker.")

def save_event_to_file(event_name: str, data: dict):
    """Função auxiliar para salvar qualquer evento no arquivo de eventos do jogo."""
    if not current_session_id:
        return
    
    # Adiciona o sessionId e o timestamp a todos os eventos que salvamos
    data['sessionId'] = current_session_id
    data['serverTimestamp'] = int(time.time() * 1000)
    data['eventType'] = event_name # Garante que o tipo do evento seja salvo
    
    try:
        file_name = 'game_events.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        log.error(f"Erro ao salvar evento '{event_name}' para sessão {current_session_id}", exc_info=True)

@sio.on('raceConfigure')
def on_race_configure(data):
    """
    Gatilho para INICIAR uma nova sessão. Gera o sessionId e prepara o ambiente.
    """
    global current_session_id, finished_players
    
    # Gera um sessionId único no backend
    current_session_id = f"session-{uuid.uuid4()}"
    finished_players = {} # Limpa o estado de jogadores que terminaram
    
    log.info(f"Nova corrida configurada. Gerado Session ID: {current_session_id}")
    session_path = RAW_DATA_PATH / current_session_id
    session_path.mkdir(parents=True, exist_ok=True)
    log.info(f"Diretório da sessão criado em: {session_path}")
    
    # Salva este evento de configuração como o primeiro evento da sessão
    save_event_to_file('raceConfigure', data)

@sio.on('hasFinished')
def on_has_finished(data):
    """
    Recebe o evento de que um jogador terminou. Controla o fim da corrida
    e dispara o pipeline quando o último jogador termina.
    """
    global finished_players
    if not current_session_id:
        return

    player_id = data.get('player')
    if not player_id:
        log.warning("Recebido evento 'hasFinished' sem 'player'. Ignorando.")
        return

    log.info(f"Jogador {player_id} terminou a corrida.")
    finished_players[player_id] = True
    
    # Salva o evento no arquivo de log da sessão
    save_event_to_file('hasFinished', data)

    # Verifica se todos os jogadores esperados (2) terminaram
    if len(finished_players) >= 2:
        log.info(f"Todos os jogadores terminaram a corrida para a sessão {current_session_id}.")
        log.info("Disparando o pipeline de processamento de dados...")
        # Emite o evento que aciona o pipeline_worker
        sio.emit('pipelineTrigger', {'sessionId': current_session_id})
        # Encerra formalmente a coleta (embora já devesse ter parado para ambos)
        global current_session_id
        current_session_id = None

@sio.on('eSense')
def on_esense(data):
    """Handler para os dados de EEG."""
    player_id = data.get('player')
    # Só coleta se a sessão estiver ativa E o jogador ainda não tiver terminado
    if not current_session_id or not player_id or finished_players.get(player_id):
        return
        
    try:
        file_name = f'player_{player_id}_eeg.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        log.error(f"Erro ao salvar dados de EEG para Player {player_id}", exc_info=True)

# --- Handlers para outros eventos de jogo ---
# Todos eles simplesmente chamam a função auxiliar 'save_event_to_file'

@sio.on('raceStarted')
def on_race_started(data):
    save_event_to_file('raceStarted', data)

@sio.on('collision')
def on_collision(data):
    save_event_to_file('collision', data)

@sio.on('overtake')
def on_overtake(data):
    save_event_to_file('overtake', data)

@sio.on('handGesture')
def on_hand_gesture(data):
    save_event_to_file('handGesture', data)

# ==============================================================================
# SEÇÃO DE INICIALIZAÇÃO
# ==============================================================================
if __name__ == '__main__':
    try:
        RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
        sio.connect(BROKER_URL, wait=True, wait_timeout=30, transports='websocket')
        sio.wait()
    except socketio.exceptions.ConnectionError as e:
        log.critical(f"Não foi possível conectar ao Broker em {BROKER_URL}. Encerrando. Erro: {e}")
    except Exception:
        log.critical("Uma exceção não tratada ocorreu no loop principal do coletor.", exc_info=True)