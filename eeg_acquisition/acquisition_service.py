import os, socket, json
import socketio

PLAYER_ID = int(os.getenv('PLAYER_ID', '1'))
ACQ_PORT  = int(os.getenv('ACQ_PORT', '13854'))
HOST = os.getenv('EEG_HOST', '127.0.0.1')
BROKER_URL = os.getenv('BROKER_URL', 'http://broker:3000')

print(f"[ACQ] EEG_HOST={HOST} PORT={ACQ_PORT} BROKER_URL={BROKER_URL}")

BUFFER_SIZE = 4096
N_READINGS = int(os.getenv('N_READINGS', '5')) # janela de leituras para média móvel (rolling window)
POOR_SIGNAL_LEVEL_THRESHOLD = int(os.getenv('POOR_SIGNAL_LEVEL_THRESHOLD', '100')) # com o neurosky, provavelmente o limite sera 0. Por enquanto usamos 100 pois sao numeros completamente aleatorios

window = []

def extract_attention(packet):
    return packet['eSense']['attention']

def filter_attention(packet):
    attention_raw = extract_attention(packet)
    window.append(attention_raw)
    if len(window) > N_READINGS:
        window.pop(0)
    attention_smooth = sum(window)/len(window)
    return attention_smooth

def start_acquisition_service():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, ACQ_PORT))
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
                packet = json.loads(raw)
                print("\n-----received data----")
                print(packet)
                if 'eSense' in packet and packet['poorSignalLevel'] <= POOR_SIGNAL_LEVEL_THRESHOLD:
                    att_smooth = filter_attention(packet)
                    print("\n-----sent attention=----")
                    print(att_smooth)
                    sio.emit('attention', {
                        'player': PLAYER_ID,
                        'attention': att_smooth
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
