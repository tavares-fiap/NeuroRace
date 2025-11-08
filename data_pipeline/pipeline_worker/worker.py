import os
import socketio
from pathlib import Path
import logging
from processing_logic import process_session, calculate_kpis_for_session

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
TRUSTED_DATA_PATH = Path(os.getenv('TRUSTED_DATA_PATH', '/data/trusted_data'))
REFINED_DATA_PATH = Path(os.getenv('REFINED_DATA_PATH', '/data/refined_data'))

log.info(f"Worker iniciado. Conectando ao Broker em {BROKER_URL}")

sio = socketio.Client()

@sio.event
def connect():
    log.info("Conectado ao Broker com sucesso. Aguardando gatilho do pipeline...")

@sio.event
def disconnect():
    log.warning("Desconectado do Broker.")

@sio.on('pipelineTrigger')
def on_pipeline_trigger(data):
    """
    Este é o GATILHO que inicia todo o pipeline de processamento.
    Ele é disparado pelo raw_data_collector quando a corrida é confirmada como finalizada.
    """
    session_id = data.get('sessionId')
    if not session_id:
        log.error("Evento 'pipelineTrigger' recebido sem 'sessionId'. Ignorando.")
        return
        
    log.info("="*60)
    log.info(f"Gatilho de pipeline recebido. Iniciando processamento para Session ID: {session_id}")
    
    try:
        # --- Passo 1: Executar a lógica do ETL (Raw -> Trusted) ---
        process_session(session_id, RAW_DATA_PATH, TRUSTED_DATA_PATH)
        
        # --- Passo 2: Executar a lógica do Refined (Trusted -> Refined/Firebase) ---
        calculate_kpis_for_session(session_id, TRUSTED_DATA_PATH, REFINED_DATA_PATH, RAW_DATA_PATH)
        
        log.info(f"Pipeline para {session_id} finalizado com sucesso.")
        
    except FileNotFoundError as e:
        log.error(f"Falha no pipeline para {session_id}: Arquivos da sessão não encontrados. Detalhe: {e}")
    except Exception:
        log.critical(f"ERRO CRÍTICO no pipeline para {session_id}.", exc_info=True)
    finally:
        log.info("="*60)


if __name__ == '__main__':
    try:
        sio.connect(BROKER_URL, wait=True, wait_timeout=30, transports='websocket')
        sio.wait()
    except socketio.exceptions.ConnectionError as e:
        log.critical(f"Não foi possível conectar ao Broker em {BROKER_URL}. Encerrando. Erro: {e}")
    except Exception:
        log.critical("Uma exceção não tratada ocorreu no loop principal.", exc_info=True)