import socketio
import pandas as pd
import os
import json

# --- Configuração ---
BROKER_URL = os.getenv("BROKER_URL", "http://localhost:3000")
RESULTS_DIR = '/results'
OUTPUT_FILE = os.path.join(RESULTS_DIR, 'analysis_summary.json')

# --- Estado da Aplicação ---
finished_players = set() # O serviço agora tem seu próprio estado

# --- Cliente Socket.IO ---
sio = socketio.Client()

def perform_analysis():
    """Lê os arquivos CSV, calcula as métricas e salva um resumo em JSON."""
    global finished_players
    print("Dois jogadores finalizaram. Iniciando análise das métricas...")

    try:
        # Caminhos para os arquivos de dados
        esense_p1_path = os.path.join(RESULTS_DIR, 'esense_player_1.csv')
        esense_p2_path = os.path.join(RESULTS_DIR, 'esense_player_2.csv')
        blink_p1_path = os.path.join(RESULTS_DIR, 'blink_player_1.csv')
        blink_p2_path = os.path.join(RESULTS_DIR, 'blink_player_2.csv')

        # Carrega os dados usando Pandas
        p1_esense_df = pd.read_csv(esense_p1_path)
        p2_esense_df = pd.read_csv(esense_p2_path)
        p1_blink_df = pd.read_csv(blink_p1_path)
        p2_blink_df = pd.read_csv(blink_p2_path)

        # Função auxiliar para calcular estatísticas de um jogador
        def get_player_stats(esense_df, blink_df):
            stats = {
                'attention_avg': round(esense_df['attention'].mean(), 2),
                'meditation_avg': round(esense_df['meditation'].mean(), 2),
                'attention_peak': int(esense_df['attention'].max()),
                'meditation_peak': int(esense_df['meditation'].max()),
                'attention_consistency': round(esense_df['attention'].std(), 2),
                'meditation_consistency': round(esense_df['meditation'].std(), 2),
                'total_blinks': len(blink_df),
                'signal_quality_ok_percentage': round(
                    (len(esense_df[esense_df['poorSignalLevel'] == 0]) / len(esense_df)) * 100, 2
                )
            }
            return stats

        # Calcula as estatísticas
        stats_p1 = get_player_stats(p1_esense_df, p1_blink_df)
        stats_p2 = get_player_stats(p2_esense_df, p2_blink_df)
        
        # Gera o resumo
        summary = {
            'winner_by_attention': 'player_1' if stats_p1['attention_avg'] > stats_p2['attention_avg'] else 'player_2',
            'winner_by_meditation': 'player_1' if stats_p1['meditation_avg'] > stats_p2['meditation_avg'] else 'player_2',
            'most_consistent_player_attention': 'player_1' if stats_p1['attention_consistency'] < stats_p2['attention_consistency'] else 'player_2'
        }

        # Estrutura final
        analysis_results = {
            'race_summary': summary,
            'player_1_stats': stats_p1,
            'player_2_stats': stats_p2
        }

        # Salva o resultado
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(analysis_results, f, indent=4)
        
        print(f"Análise concluída com sucesso! Resumo salvo em: {OUTPUT_FILE}")

    except FileNotFoundError:
        print("Erro: Arquivos CSV não encontrados. A análise não pode ser executada.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a análise: {e}")
    
    # Limpa o estado para a próxima corrida
    finished_players.clear()


# --- Handlers de Eventos do Socket.IO ---

@sio.event
def connect():
    print("Serviço de Análise conectado ao broker.")

@sio.on('hasFinished') # <-- MUDANÇA IMPORTANTE: Ouvindo 'hasFinished'
def on_has_finished(data):
    """Ouve o fim da corrida de cada jogador e dispara a análise quando ambos terminarem."""
    player_id = data.get('player')
    if player_id and player_id not in finished_players:
        print(f"Serviço de Análise registrou que o jogador {player_id} terminou.")
        finished_players.add(player_id)

        if len(finished_players) == 2:
            perform_analysis()
            
@sio.on('raceStarted') # Opcional, mas bom para limpar o estado
def on_race_started(data):
    """Limpa a contagem de jogadores ao iniciar uma nova corrida."""
    print("Nova corrida iniciada, limpando estado do serviço de análise.")
    finished_players.clear()

@sio.event
def disconnect():
    print("Serviço de Análise desconectado do broker.")

# --- Execução Principal ---
if __name__ == '__main__':
    print("Serviço de Análise aguardando pelos eventos de fim de corrida...")
    sio.connect(BROKER_URL)
    sio.wait()