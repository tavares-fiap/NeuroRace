import socket, json
from config import HOST, PORT, BUFFER_SIZE, N_READINGS

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
    client.connect((HOST, PORT))
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
                if raw:
                    packet = json.loads(raw)
                    attention_smooth = filter_attention(packet)
                    print(attention_smooth)

    except KeyboardInterrupt:
        print("Encerrando aquisição.")
    finally:
        client.close()

if __name__ == '__main__':
    start_acquisition_service()
