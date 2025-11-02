import os
import json
import socketio
from pathlib import Path
import logging

# ==============================================================================
# SEÇÃO DE CONFIGURAÇÃO DO LOGGING
# ==============================================================================
log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
# Define o logger do engine.io para um nível mais alto (só mostrará erros)
logging.getLogger("engineio.client").setLevel(logging.WARNING)
logging.getLogger("socketio.client").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

# ==============================================================================
# SEÇÃO DE CONFIGURAÇÃO DO SERVIÇO
# ==============================================================================
BROKER_URL = os.getenv('BROKER_URL', 'http://localhost:3000')
RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', '/data/raw_data'))

log.info(f"Coletor iniciado. Conectando ao Broker em {BROKER_URL}")
log.info(f"Salvando dados brutos em {RAW_DATA_PATH}")

current_session_id = None
# Ativa os loggers internos da biblioteca para depuração de conexão
sio = socketio.Client(logger=True, engineio_logger=False) # EngineIO logger é muito verboso

@sio.event
def connect():
    log.info("Conectado ao Broker com sucesso. Aguardando dados...")

@sio.event
def disconnect():
    log.warning("Desconectado do Broker.")

@sio.on('hasFinished')
def on_race_finished(data):
    """Gatilho para parar a coleta para a sessão atual."""
    global current_session_id
    session_id = data.get('sessionId')
    log.info(f"Recebido evento de fim de corrida para Session ID: {session_id}")
    if current_session_id == session_id:
        current_session_id = None
        log.info(f"Coleta para a sessão {session_id} encerrada.")

@sio.on('gameEvent')
def on_game_event(data):
    """Handler para TODOS os eventos de jogo."""
    global current_session_id
    event_type = data.get('eventType')
    session_id = data.get('sessionId')

    if event_type == 'raceStarted':
        if not session_id:
            log.error("Evento 'raceStarted' recebido sem 'sessionId'.")
            return
        current_session_id = session_id
        log.info(f"Nova corrida iniciada. Coletando para Session ID: {current_session_id}")
        session_path = RAW_DATA_PATH / current_session_id
        session_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Diretório da sessão criado em: {session_path}")
    
    if not current_session_id or session_id != current_session_id:
        return
    try:
        file_name = 'game_events.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        log.error(f"Erro ao salvar evento de jogo para sessão {current_session_id}", exc_info=True)

@sio.on('eSense')
def on_esense(data):
    """Handler para os dados de EEG."""
    if not current_session_id:
        return
    player_id = data.get('player')
    if not player_id:
        log.warning("Recebido pacote eSense sem 'player_id'. Pacote ignorado.")
        return
    try:
        file_name = f'player_{player_id}_eeg.jsonl'
        file_path = RAW_DATA_PATH / current_session_id / file_name
        with open(file_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        log.error(f"Erro ao salvar dados de EEG para Player {player_id} na sessão {current_session_id}", exc_info=True)

if __name__ == '__main__':
    try:
        RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
        sio.connect(BROKER_URL, wait=True, wait_timeout=30, transports='websocket')
        sio.wait()
    except socketio.exceptions.ConnectionError as e:
        log.critical(f"Não foi possível conectar ao Broker em {BROKER_URL}. Encerrando. Erro: {e}")
    except Exception:
        log.critical("Uma exceção não tratada ocorreu no loop principal do coletor.", exc_info=True)