import os
import socket
import json
import socketio
import time
import logging

# ==============================================================================
# SEÇÃO DE CONFIGURAÇÃO DO LOGGING
# ==============================================================================
log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format) # Nível INFO é suficiente aqui
log = logging.getLogger(__name__)

# ==============================================================================
# SEÇÃO DE CONFIGURAÇÃO DO SERVIÇO
# ==============================================================================
# SOURCE = os.getenv("EEG_SOURCE", "sim")
PLAYER_ID = int(os.getenv('PLAYER_ID', '1'))
ACQ_PORT  = int(os.getenv('ACQ_PORT', '13854'))
HOST = os.getenv('EEG_HOST', '127.0.0.1')
BROKER_URL = os.getenv('BROKER_URL', 'http://broker:3000')
SOURCE = os.getenv('SOURCE', 'real')

log.info(f"Serviço de Aquisição para Player {PLAYER_ID} iniciado.")
log.info(f"Conectando à fonte de EEG em {HOST}:{ACQ_PORT}")
log.info(f"Enviando dados para o Broker em {BROKER_URL}")

BUFFER_SIZE = 4096
# N_READINGS = int(os.getenv('N_READINGS', '5')) # janela de leituras para média móvel (rolling window)
POOR_SIGNAL_LEVEL_THRESHOLD = int(os.getenv('POOR_SIGNAL_LEVEL_THRESHOLD', '0'))

# window = []

def signal_status(psl: int | None, threshold: int) -> str:
    if psl is None:
        return "unknown"
    if psl >= 200:
        return "no-signal"
    return "ok" if psl <= threshold else "poor"

# def extract_attention(packet):
#     e = packet.get('eSense') or {}
#     return e.get('attention')

# def filter_attention(packet):
#     attention_raw = extract_attention(packet)
#     if attention_raw is None:
#         return None
#     window.append(attention_raw)
#     if len(window) > N_READINGS:
#         window.pop(0)
#     attention_smooth = sum(window)/len(window)
#     return attention_smooth

def start_acquisition_service():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sio = socketio.Client(logger=True, engineio_logger=False) # EngineIO logger é muito verboso

    try:
        # --- Conexões Iniciais ---
        log.info("Tentando conectar à fonte de EEG...")
        client.connect((HOST, ACQ_PORT))
        log.info("Conectado à fonte de EEG com sucesso.")
        
        log.info("Enviando handshake para a fonte de EEG...")
        client.sendall(b'{"enableRawOutput": false, "format": "Json"}')
        
        log.info("Tentando conectar ao Broker...")
        sio.connect(BROKER_URL)
        log.info("Conectado ao Broker com sucesso.")

        # --- Loop Principal de Aquisição ---
        buffer = ''
        while True:
            data = client.recv(BUFFER_SIZE)
            if not data:
                log.warning("A fonte de EEG fechou a conexão.")
                break
                
            buffer += data.decode('utf-8')
            while '\r' in buffer:
                raw, buffer = buffer.split('\r', 1)
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    packet = json.loads(raw)
                    log.debug(f"Pacote de dados recebido: {packet}")
                except json.JSONDecodeError:
                    log.warning(f"Falha ao decodificar JSON. Dados brutos: '{raw}'")
                    continue

                now_ms = int(time.time() * 1000)

                # if 'blinkStrength' in packet:
                #     sio.emit('blink', {
                #         'player': PLAYER_ID,
                #         'blink': packet['blinkStrength'],
                #         'timeStamp': now_ms
                #     })
                if 'eSense' in packet:
                    psl = packet.get('poorSignalLevel')
                    status = signal_status(psl, POOR_SIGNAL_LEVEL_THRESHOLD)
                    
                    eSense_payload = {
                        'player': PLAYER_ID,
                        'attention': packet['eSense']['attention'],
                        'meditation': packet['eSense']['meditation'],
                        'eegPower': packet['eegPower'],
                        'poorSignalLevel': psl,
                        'status': status,
                        'source': SOURCE,
                        'timeStamp': now_ms,
                    }
                    sio.emit('eSense', eSense_payload)
                    log.debug(f"Pacote eSense enviado para o Broker.")

                    # att_smooth = filter_attention(packet)
                    # if att_smooth is not None:
                    #     sio.emit('attention', {
                    #         'player': PLAYER_ID,
                    #         'attention': att_smooth,
                    #         'timeStamp': now_ms
                    #     })

    except KeyboardInterrupt:
        log.info("Encerrando serviço de aquisição por solicitação do usuário.")
    except socket.error as e:
        log.critical(f"Erro de conexão com a fonte de EEG em {HOST}:{ACQ_PORT}. Verifique se o simulador ou dispositivo está rodando. Erro: {e}")
    except socketio.exceptions.ConnectionError as e:
        log.critical(f"Não foi possível conectar ao Broker em {BROKER_URL}. Verifique se o broker está rodando. Erro: {e}")
    except Exception:
        log.critical("Uma exceção não tratada ocorreu no loop de aquisição.", exc_info=True)
    finally:
        if client:
            client.close()
        if sio and sio.connected:
            sio.disconnect()
        log.info("Conexões encerradas.")

if __name__ == '__main__':
    start_acquisition_service()