import socket, json
from config import HOST, ACQUISITION_PORT, BUFFER_SIZE, N_READINGS, POOR_SIGNAL_LEVEL_THRESHOLD, BROKER_URL
import socketio

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
    client.connect((HOST, ACQUISITION_PORT))
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
                        'player': 1,
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
