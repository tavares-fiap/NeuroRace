HOST = '127.0.0.1'
ACQUISITION_PORT = 13854
BROKER_URL = 'http://localhost:3000'
PACKET_INTERVAL = 1.0
BUFFER_SIZE = 4096
N_READINGS = 5 # janela de leituras para média móvel (rolling window)
POOR_SIGNAL_LEVEL_THRESHOLD = 100 # com o neurosky, provavelmente o limite sera 0. Por enquanto usamos 100 pois sao numeros completamente aleatorios