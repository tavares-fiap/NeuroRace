import socket, json, time, random
from config import HOST, ACQUISITION_PORT, PACKET_INTERVAL

def generate_eeg_power():
    return {
        "delta": random.randint(100000, 200000),
        "theta": random.randint(10000, 50000),
        "lowAlpha": random.randint(1000, 20000),
        "highAlpha": random.randint(1000, 20000),
        "lowBeta": random.randint(500, 15000),
        "highBeta": random.randint(500, 15000),
        "lowGamma": random.randint(200, 10000),
        "highGamma": random.randint(200, 10000),
    }

def generate_packet():
    return {
        "poorSignalLevel": random.randint(0, 200),
        "eSense": {"attention": random.randint(0, 100), "meditation": random.randint(0, 100)},
        "eegPower": generate_eeg_power(),
        "rawEeg": random.randint(-2048, 2047),
        "blinkStrength": random.choice([0]*9 + [random.randint(50,255)])
    }

def handle_client(conn, addr):
    print(f"[+] Conectado em {addr}")
    try:
        print("Iniciando stream de dados...")
        while True:
            packet = generate_packet()
            message = json.dumps(packet) + '\r'
            print("\n-----sent data-----")
            print(message)
            conn.sendall(message.encode('utf-8'))
            time.sleep(PACKET_INTERVAL)
    except (BrokenPipeError, ConnectionResetError):
        print(f"[-] Cliente desconectou {addr}")
    finally:
        conn.close()
        print(f"[*] Desconectado {addr}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, ACQUISITION_PORT))
    server.listen(1)
    print(f"TGC Simulator ouvindo em {HOST}:{ACQUISITION_PORT}")
    try:
        conn, addr = server.accept()
        handle_client(conn, addr)
    except KeyboardInterrupt:
        print("Simulator finalizando.")
    finally:
        server.close()

if __name__ == '__main__':
    start_server()
