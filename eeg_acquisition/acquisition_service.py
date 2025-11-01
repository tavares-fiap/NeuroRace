import os, socket, json
import socketio
import time


# SOURCE = os.getenv("EEG_SOURCE", "sim")
PLAYER_ID = int(os.getenv('PLAYER_ID', '1'))
ACQ_PORT  = int(os.getenv('ACQ_PORT', '13854'))
HOST = os.getenv('EEG_HOST', '127.0.0.1')
BROKER_URL = os.getenv('BROKER_URL', 'http://broker:3000')

print(f"[ACQ] EEG_HOST={HOST} PORT={ACQ_PORT} BROKER_URL={BROKER_URL}")

BUFFER_SIZE = 4096
# N_READINGS = int(os.getenv('N_READINGS', '5')) # janela de leituras para média móvel (rolling window)
POOR_SIGNAL_LEVEL_THRESHOLD = int(os.getenv('POOR_SIGNAL_LEVEL_THRESHOLD', '50')) # com o neurosky, provavelmente o limite sera 0. Por enquanto usamos 100 pois sao numeros completamente aleatorios

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
    client.connect((HOST, ACQ_PORT))
    #handshake
    client.sendall(b'{"enableRawOutput": false, "format": "Json"}')
    sio = socketio.Client()
    sio.connect(BROKER_URL)
    try:
        buffer = ''
        while True:
            data = client.recv(BUFFER_SIZE)
            if not data:
                print("Servidor fechou a conexão.")
                break
            buffer += data.decode('utf-8')
            while '\r' in buffer:
                raw, buffer = buffer.split('\r', 1)
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    packet = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                print("\n-----received data----")
                print(packet)

                now_ms = int(time.time() * 1000)

                if 'blinkStrength' in packet:
                    sio.emit('blink', {
                        'player': PLAYER_ID,
                        'blink': packet['blinkStrength'],
                        # 'poorSignalLevel': psl,
                        # 'status': status,
                        'timeStamp': now_ms
                    })
                if 'eSense' in packet:
                    psl = packet.get('poorSignalLevel')
                    status = signal_status(psl, POOR_SIGNAL_LEVEL_THRESHOLD)
                    # att_smooth = filter_attention(packet)
                    # if att_smooth is not None:
                    #     sio.emit('attention', {
                    #         'player': PLAYER_ID,
                    #         'attention': att_smooth,
                    #         'timeStamp': now_ms
                    #     })

                    sio.emit('eSense', {
                        'player': PLAYER_ID,
                        'attention': packet['eSense']['attention'],
                        'meditation': packet['eSense']['meditation'],
                        'eegPower': packet['eegPower'],
                        'poorSignalLevel': psl,
                        'status': status,
                        'timeStamp': now_ms,
                    })

    except KeyboardInterrupt:
        print("Encerrando aquisição.")
    except Exception as e:
        print("Erro inesperado:", e)
    finally:
        client.close()
        sio.disconnect()
        print("Conexões encerradas.")

if __name__ == '__main__':
    start_acquisition_service()
