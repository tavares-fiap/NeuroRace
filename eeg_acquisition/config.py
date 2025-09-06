import os

HOST = '127.0.0.1'
ACQUISITION_PORT = int(os.getenv('ACQ_PORT', '13854'))
BROKER_URL = os.getenv('BROKER_URL', 'http://localhost:3000')
PACKET_INTERVAL = float(os.getenv('PACKET_INTERVAL', '1.0'))
BUFFER_SIZE = 4096
N_READINGS = int(os.getenv('N_READINGS', '5')) # janela de leituras para média móvel (rolling window)
POOR_SIGNAL_LEVEL_THRESHOLD = int(os.getenv('POOR_SIGNAL_LEVEL_THRESHOLD', '100')) # com o neurosky, provavelmente o limite sera 0. Por enquanto usamos 100 pois sao numeros completamente aleatorios