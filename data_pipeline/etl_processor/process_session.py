import os
import sys
import pandas as pd
from pathlib import Path

# --- Configuração ---
# Caminhos DENTRO do container, que são mapeados para as pastas locais
RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', '/data/raw_data'))
TRUSTED_DATA_PATH = Path(os.getenv('TRUSTED_DATA_PATH', '/data/trusted_data'))

def process_session(session_id: str):
    """
    Função principal que orquestra o ETL para uma única sessão.
    """
    print(f"[ETL] Iniciando processamento para a Session ID: {session_id}")
    
    session_raw_path = RAW_DATA_PATH / session_id
    if not session_raw_path.exists():
        print(f"[ETL] Erro: Diretório da sessão não encontrado em {session_raw_path}")
        return

    # --- 1. EXTRACT ---
    print(f"[ETL][EXTRACT] Lendo dados brutos de {session_raw_path}...")
    eeg_df = load_eeg_data(session_raw_path)
    events_df = load_game_events(session_raw_path)

    if eeg_df.empty:
        print("[ETL] Aviso: Nenhum dado de EEG encontrado para a sessão. Abortando.")
        return

    # --- 2. TRANSFORM ---
    print("[ETL][TRANSFORM] Transformando e unificando os dados...")
    trusted_df = transform_and_merge(eeg_df, events_df)

    # --- 3. LOAD ---
    TRUSTED_DATA_PATH.mkdir(parents=True, exist_ok=True)
    output_path = TRUSTED_DATA_PATH / f"{session_id}.parquet"
    
    print(f"[ETL][LOAD] Salvando dados da Camada Trusted em {output_path}...")
    trusted_df.to_parquet(output_path, index=False, compression='snappy')
    
    print(f"[ETL] Processamento para a sessão {session_id} finalizado com sucesso!")

def load_eeg_data(session_path: Path) -> pd.DataFrame:
    """Carrega, combina e pré-processa os arquivos de EEG de todos os jogadores."""
    all_eeg_data = []
    # Encontra todos os arquivos de EEG na pasta da sessão
    eeg_files = list(session_path.glob("player_*_eeg.jsonl"))
    
    for file_path in eeg_files:
        try:
            # json_normalize já cria um DataFrame a partir do JSON aninhado
            df = pd.read_json(file_path, lines=True)
            all_eeg_data.append(df)
        except Exception as e:
            print(f"  - Aviso: Falha ao ler o arquivo {file_path}: {e}")
            
    if not all_eeg_data:
        return pd.DataFrame()

    return pd.concat(all_eeg_data, ignore_index=True)

def load_game_events(session_path: Path) -> pd.DataFrame:
    """Carrega os eventos de jogo da sessão."""
    events_file = session_path / "game_events.jsonl"
    if not events_file.exists():
        return pd.DataFrame()
    try:
        return pd.read_json(events_file, lines=True)
    except Exception as e:
        print(f"  - Aviso: Falha ao ler o arquivo de eventos {events_file}: {e}")
        return pd.DataFrame()

def transform_and_merge(eeg_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Esta é a função central de transformação.
    """
    # Desempacota o dicionário 'eegPower' em colunas separadas
    eeg_power_df = pd.json_normalize(eeg_df['eegPower'])
    eeg_df = pd.concat([eeg_df.drop('eegPower', axis=1), eeg_power_df], axis=1)

    # Renomeia 'timeStamp' para um nome padrão e converte para datetime
    eeg_df = eeg_df.rename(columns={'timeStamp': 'timestamp'})
    eeg_df['timestamp'] = pd.to_datetime(eeg_df['timestamp'], unit='ms', utc=True)
    
    # Adiciona colunas de evento ao eeg_df
    eeg_df['game_event_type'] = None

    # Se houver eventos, prepara-os e combina com os dados de EEG
    if not events_df.empty:
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'], unit='ms', utc=True)
        # Renomeia colunas para evitar conflitos
        events_df = events_df.rename(columns={'eventType': 'game_event_type'})
        
        # Concatena os dois DataFrames
        combined_df = pd.concat([eeg_df, events_df], ignore_index=True)
    else:
        combined_df = eeg_df
        
    # Ordena pela timestamp para criar a linha do tempo final
    combined_df = combined_df.sort_values(by='timestamp').reset_index(drop=True)
    
    # Cria a coluna de validação do sinal
    combined_df['is_signal_valid'] = (combined_df['poorSignalLevel'] == 0)

    # Seleciona e ordena as colunas para o schema final da Camada Trusted
    final_columns = [
        'timestamp', 'player', 'attention', 'meditation', 
        'poorSignalLevel', 'is_signal_valid', 'game_event_type',
        'delta', 'theta', 'lowAlpha', 'highAlpha', 'lowBeta', 
        'highBeta', 'lowGamma', 'highGamma'
    ]
    # Filtra colunas que existem no DataFrame para evitar erros
    existing_columns = [col for col in final_columns if col in combined_df.columns]
    
    return combined_df[existing_columns]

if __name__ == '__main__':
    # Permite que passemos o session_id como um argumento ao rodar o script
    if len(sys.argv) > 1:
        session_id_to_process = sys.argv[1]
        process_session(session_id_to_process)
    else:
        print("Uso: python process_session.py <session_id>")