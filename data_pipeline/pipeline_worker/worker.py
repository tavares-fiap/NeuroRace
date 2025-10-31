# data_pipeline/pipeline_worker/worker.py

import os
import socketio
from pathlib import Path
from processing_logic import process_session, calculate_kpis_for_session

# --- Configuração ---
BROKER_URL = os.getenv('BROKER_URL', 'http://localhost:3000')
RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', '/data/raw_data'))
TRUSTED_DATA_PATH = Path(os.getenv('TRUSTED_DATA_PATH', '/data/trusted_data'))
REFINED_DATA_PATH = Path(os.getenv('REFINED_DATA_PATH', '/data/refined_data'))

print(f"[WORKER] Conectando ao Broker em {BROKER_URL}")

sio = socketio.Client()

@sio.event
def connect():
    print('[WORKER] Conectado ao Broker, aguardando corridas...')

@sio.event
def disconnect():
    print('[WORKER] Desconectado do Broker')

@sio.on('hasFinished')
def on_race_finished(data):
    """
    Este é o GATILHO que inicia todo o pipeline de processamento.
    """
    session_id = data.get('sessionId')
    if not session_id:
        print("[WORKER] Erro: evento 'hasFinished' sem 'sessionId'.")
        return
        
    print(f"\n[WORKER] Recebido sinal de fim de corrida para Session ID: {session_id}")
    print("="*50)
    
    try:
        # --- Passo 1: Executar a lógica do ETL (Raw -> Trusted) ---
        process_session(session_id, RAW_DATA_PATH, TRUSTED_DATA_PATH)
        
        # --- Passo 2: Executar a lógica do Refined (Trusted -> Refined/Firebase) ---
        calculate_kpis_for_session(session_id, TRUSTED_DATA_PATH, REFINED_DATA_PATH)
        
        print(f"\n[WORKER] Pipeline completo para {session_id} finalizado com sucesso.")
        print("="*50)
        
    except Exception as e:
        print(f"[WORKER] ERRO CRÍTICO durante o processamento da sessão {session_id}: {e}")

if __name__ == '__main__':
    # Inicia a conexão com o broker e espera por eventos para sempre
    sio.connect(BROKER_URL, wait=True, wait_timeout=10, transports='websocket')
    sio.wait()