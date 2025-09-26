import socketio
import csv
import os

BROKER_URL = os.getenv('BROKER_URL', 'http://broker:3000')
RESULTS_DIR = '/results'

recording_status = {
    'player_1': False,
    'player_2': False
}
finished_players = set()

sio = socketio.Client()


def initialize_csv_files():
    """Cria a pasta de resultados e os arquivos CSV com cabeçalhos, se não existirem."""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    esense_p1_file = os.path.join(RESULTS_DIR, 'esense_player_1.csv')
    esense_p2_file = os.path.join(RESULTS_DIR, 'esense_player_2.csv')
    blink_p1_file = os.path.join(RESULTS_DIR, 'blink_player_1.csv')
    blink_p2_file = os.path.join(RESULTS_DIR, 'blink_player_2.csv')

    esense_header = ['player', 'attention', 'meditation', 'poorSignalLevel', 'status', 'timeStamp']
    blink_header = ['player', 'blink', 'poorSignalLevel', 'status', 'timeStamp']

    with open(esense_p1_file, 'w', newline='') as f:
        csv.writer(f).writerow(esense_header)
    with open(esense_p2_file, 'w', newline='') as f:
        csv.writer(f).writerow(esense_header)
    with open(blink_p1_file, 'w', newline='') as f:
        csv.writer(f).writerow(blink_header)
    with open(blink_p2_file, 'w', newline='') as f:
        csv.writer(f).writerow(blink_header)

def clear_csv_files():
    """Limpa os dados dos arquivos CSV, mantendo apenas os cabeçalhos."""
    print("Limpando arquivos CSV para a próxima corrida...")
    initialize_csv_files()

@sio.event
def connect():
    print("Conectado ao broker com sucesso!")

@sio.event
def connect_error(data):
    print("A conexão falhou!")

@sio.event
def disconnect():
    print("Desconectado do broker.")

@sio.on('raceStarted')
def on_race_started(data):
    """Inicia a gravação para ambos os jogadores."""
    print("Evento 'raceStarted' recebido. Iniciando a gravação.")
    recording_status['player_1'] = True
    recording_status['player_2'] = True
    finished_players.clear()
    clear_csv_files()

@sio.on('eSense')
def on_esense(data):
    """Grava os dados do evento eSense no CSV correspondente."""
    player_id = data.get('player')
    if player_id and recording_status.get(f'player_{player_id}'):
        file_path = os.path.join(RESULTS_DIR, f'esense_player_{player_id}.csv')
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get('player'),
                data.get('attention'),
                data.get('meditation'),
                data.get('poorSignalLevel'),
                data.get('status'),
                data.get('timeStamp')
            ])

@sio.on('blink')
def on_blink(data):
    """Grava os dados do evento blink no CSV correspondente."""
    player_id = data.get('player')
    if player_id and recording_status.get(f'player_{player_id}'):
        file_path = os.path.join(RESULTS_DIR, f'blink_player_{player_id}.csv')
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get('player'),
                data.get('blink'),
                data.get('poorSignalLevel'),
                data.get('status'),
                data.get('timeStamp')
            ])

@sio.on('hasFinished')
def on_has_finished(data):
    """Para de gravar os dados do jogador que finalizou."""
    player_id = data.get('player')
    if player_id:
        player_key = f'player_{player_id}'
        print(f"Jogador {player_id} finalizou a corrida.")
        recording_status[player_key] = False
        finished_players.add(player_key)

        if len(finished_players) == 2:
            print("Ambos os jogadores finalizaram. A corrida acabou.")
            print("Emitindo evento 'collectEnded' para o serviço de análise.")
            sio.emit('collectEnded')

if __name__ == '__main__':
    initialize_csv_files()
    sio.connect(BROKER_URL)
    sio.wait()