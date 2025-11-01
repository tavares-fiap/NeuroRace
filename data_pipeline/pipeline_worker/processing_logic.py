import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# --- Configuração dos Parâmetros de Análise ---
FOCUS_THRESHOLD = 70  # Limiar de atenção para ser considerado "em foco"
CALM_THRESHOLD = 60   # Limiar de meditação para ser considerado "em calma"

# ==============================================================================
# SEÇÃO 1: LÓGICA DO ETL (RAW -> TRUSTED)
# Originalmente do process_session.py
# ==============================================================================

def load_eeg_data(session_path: Path) -> pd.DataFrame:
    """Carrega, combina e pré-processa os arquivos de EEG de todos os jogadores."""
    all_eeg_data = []
    eeg_files = list(session_path.glob("player_*_eeg.jsonl"))
    for file_path in eeg_files:
        try:
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
    """Função central de transformação: unifica, limpa e estrutura os dados."""
    eeg_power_df = pd.json_normalize(eeg_df['eegPower'])
    eeg_df = pd.concat([eeg_df.drop('eegPower', axis=1), eeg_power_df], axis=1)
    eeg_df = eeg_df.rename(columns={'timeStamp': 'timestamp'})
    eeg_df['timestamp'] = pd.to_datetime(eeg_df['timestamp'], unit='ms', utc=True)
    eeg_df['game_event_type'] = None
    
    if not events_df.empty:
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'], unit='ms', utc=True)
        events_df = events_df.rename(columns={'eventType': 'game_event_type'})
        combined_df = pd.concat([eeg_df, events_df], ignore_index=True)
    else:
        combined_df = eeg_df
        
    combined_df = combined_df.sort_values(by='timestamp').reset_index(drop=True)
    combined_df['is_signal_valid'] = (combined_df['poorSignalLevel'] == 0)
    
    final_columns = [
        'timestamp', 'player', 'attention', 'meditation', 'poorSignalLevel', 
        'is_signal_valid', 'game_event_type', 'delta', 'theta', 'lowAlpha', 
        'highAlpha', 'lowBeta', 'highBeta', 'lowGamma', 'highGamma'
    ]
    existing_columns = [col for col in final_columns if col in combined_df.columns]
    return combined_df[existing_columns]

def process_session(session_id: str, raw_path: Path, trusted_path: Path):
    """Orquestra o ETL: Extract, Transform, Load de Raw para Trusted."""
    print(f"[ETL] Iniciando processamento para a Session ID: {session_id}")
    session_raw_path = raw_path / session_id
    if not session_raw_path.exists():
        print(f"[ETL] Erro: Diretório da sessão não encontrado em {session_raw_path}")
        return

    # Extract
    eeg_df = load_eeg_data(session_raw_path)
    events_df = load_game_events(session_raw_path)
    if eeg_df.empty:
        print("[ETL] Aviso: Nenhum dado de EEG encontrado. Abortando.")
        return

    # Transform
    trusted_df = transform_and_merge(eeg_df, events_df)

    # Load
    trusted_path.mkdir(parents=True, exist_ok=True)
    output_path = trusted_path / f"{session_id}.parquet"
    trusted_df.to_parquet(output_path, index=False, compression='snappy')
    print(f"[ETL] Camada Trusted salva em {output_path}")

# ==============================================================================
# SEÇÃO 2: LÓGICA DE CÁLCULO DE KPIs (TRUSTED -> REFINED)
# Originalmente do calculate_kpis.py
# ==============================================================================

def get_cvf_label(std_dev: float) -> str:
    """Retorna um rótulo textual para a consistência do foco."""
    if std_dev < 15:
        return "Estável"
    elif std_dev < 25:
        return "Oscilante"
    else:
        return "Muito Oscilante"

def calculate_post_event_metrics(df_valid_signal: pd.DataFrame, events_df: pd.DataFrame, window_seconds: int = 5):
    """Calcula a variação média de foco/calma e a latência de recuperação após eventos."""
    if events_df.empty:
        return {}, {}, None
    results = []
    collision_events = events_df[events_df['game_event_type'] == 'collision']
    for _, event in events_df.iterrows():
        event_time = event['timestamp']
        before_window = df_valid_signal[(df_valid_signal['timestamp'] >= event_time - timedelta(seconds=window_seconds)) & (df_valid_signal['timestamp'] < event_time)]
        after_window = df_valid_signal[(df_valid_signal['timestamp'] > event_time) & (df_valid_signal['timestamp'] <= event_time + timedelta(seconds=window_seconds))]
        if before_window.empty or after_window.empty:
            continue
        focus_change = after_window['attention'].mean() - before_window['attention'].mean()
        calm_change = after_window['meditation'].mean() - before_window['meditation'].mean()
        lfo_seconds = None
        if event['game_event_type'] == 'collision' and after_window['attention'].mean() < before_window['attention'].mean():
            recovery_window = df_valid_signal[(df_valid_signal['timestamp'] > event_time) & (df_valid_signal['attention'] > FOCUS_THRESHOLD)]
            if not recovery_window.empty:
                recovery_time = recovery_window.iloc[0]['timestamp']
                lfo_seconds = (recovery_time - event_time).total_seconds()
        results.append({'event_type': event['game_event_type'], 'focus_change': focus_change, 'calm_change': calm_change, 'lfo_seconds': lfo_seconds})
    if not results:
        return {}, {}, None
    results_df = pd.DataFrame(results)
    focus_variation = results_df.groupby('event_type')['focus_change'].mean().to_dict()
    calm_variation = results_df.groupby('event_type')['calm_change'].mean().to_dict()
    avg_lfo = results_df['lfo_seconds'].dropna().mean()
    return focus_variation, calm_variation, avg_lfo

def calculate_kpis_for_session(session_id: str, trusted_path: Path, refined_path: Path):
    """Orquestra o cálculo de KPIs e o envio para o Firebase."""
    print(f"[REFINED] Iniciando cálculo de KPIs para a Session ID: {session_id}")
    trusted_file = trusted_path / f"{session_id}.parquet"
    if not trusted_file.exists():
        print(f"[REFINED] Erro: Arquivo da camada Trusted não encontrado.")
        return

    df = pd.read_parquet(trusted_file)
    players = df['player'].dropna().unique()
    session_kpis = {}
    
    for player_id in players:
        player_id = int(player_id)
        print(f"\n--- Calculando KPIs para o Jogador {player_id} ---")
        player_df = df[df['player'] == player_id].copy()
        df_valid_signal = player_df[player_df['is_signal_valid']].copy()
        if df_valid_signal.empty:
            print("  - Nenhum dado com sinal válido. Pulando jogador.")
            continue
        total_valid_readings = len(df_valid_signal)

        # Cálculo dos KPIs
        valid_session_pct = (len(df_valid_signal) / len(player_df)) * 100
        tzf_pct = (df_valid_signal['attention'] > FOCUS_THRESHOLD).sum() / total_valid_readings * 100
        tzc_pct = (df_valid_signal['meditation'] > CALM_THRESHOLD).sum() / total_valid_readings * 100
        calm_focus_pct = ((df_valid_signal['attention'] > FOCUS_THRESHOLD) & (df_valid_signal['meditation'] > CALM_THRESHOLD)).sum() / total_valid_readings * 100
        attention_std_dev = df_valid_signal['attention'].std()
        cvf_label = get_cvf_label(attention_std_dev)
        df_valid_signal['fatigue_ratio'] = df_valid_signal['theta'] / (df_valid_signal['highBeta'] + 1e-6)
        df_valid_signal = df_valid_signal.dropna(subset=['fatigue_ratio'])
        df_valid_signal['time_index'] = np.arange(len(df_valid_signal))
        fatigue_slope = np.polyfit(df_valid_signal['time_index'], df_valid_signal['fatigue_ratio'], 1)[0] if len(df_valid_signal) > 1 else 0
        player_events = df[df['game_event_type'].notna() & (df['player'] == player_id)]
        focus_variation, calm_variation, avg_lfo = calculate_post_event_metrics(df_valid_signal, player_events)

        player_kpis = {
            'valid_session_percentage': round(valid_session_pct, 2),
            'tzf_percentage': round(tzf_pct, 2),
            'tzc_percentage': round(tzc_pct, 2),
            'calm_focus_percentage': round(calm_focus_pct, 2),
            'cvf_label': cvf_label,
            'cvf_attention_std_dev': round(attention_std_dev, 2),
            'fatigue_slope': round(fatigue_slope, 5),
            'post_event_focus_variation': focus_variation,
            'post_event_calm_variation': calm_variation,
            'lfo_avg_recovery_seconds': round(avg_lfo, 2) if avg_lfo is not None and pd.notna(avg_lfo) else None
        }
        session_kpis[f'player_{player_id}'] = player_kpis
        print(f"  - KPIs calculados: {json.dumps(player_kpis, indent=2)}")

    if session_kpis:
        # Salva o resultado localmente para debug
        refined_path.mkdir(parents=True, exist_ok=True)
        output_path = refined_path / f"{session_id}_summary.json"
        with open(output_path, 'w') as f:
            json.dump(session_kpis, f, indent=4)
        print(f"\n[REFINED] Sumário de KPIs salvo em {output_path}")

        # Envia o resultado para o Firestore
        try:
            print("[FIREBASE] Autenticando e enviando dados...")
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            doc_ref = db.collection('sessions').document(session_id)
            doc_ref.set(session_kpis)
            print(f"[FIREBASE] Dados da sessão {session_id} salvos com sucesso!")
        except Exception as e:
            print(f"[FIREBASE] Erro ao salvar dados no Firestore: {e}")