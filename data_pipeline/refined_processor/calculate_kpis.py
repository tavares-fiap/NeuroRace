import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

# --- Configuração dos Parâmetros de Análise ---
TRUSTED_DATA_PATH = Path(os.getenv('TRUSTED_DATA_PATH', '/data/trusted_data'))
REFINED_DATA_PATH = Path(os.getenv('REFINED_DATA_PATH', '/data/refined_data'))
FOCUS_THRESHOLD = 70  # Limiar de atenção para ser considerado "em foco"
CALM_THRESHOLD = 60   # Limiar de meditação para ser considerado "em calma"

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
    
    # Filtra apenas eventos de colisão para o LFO
    collision_events = events_df[events_df['game_event_type'] == 'collision']

    for _, event in collision_events.iterrows():
        event_time = event['timestamp']
        
        # Janela ANTES do evento
        before_window = df_valid_signal[
            (df_valid_signal['timestamp'] >= event_time - timedelta(seconds=window_seconds)) &
            (df_valid_signal['timestamp'] < event_time)
        ]
        
        # Janela DEPOIS do evento
        after_window = df_valid_signal[
            (df_valid_signal['timestamp'] > event_time) &
            (df_valid_signal['timestamp'] <= event_time + timedelta(seconds=window_seconds))
        ]
        
        if before_window.empty or after_window.empty:
            continue

        # Variação de Foco e Calma
        focus_change = after_window['attention'].mean() - before_window['attention'].mean()
        calm_change = after_window['meditation'].mean() - before_window['meditation'].mean()

        # LFO - Latência para o Foco
        lfo_seconds = None
        # Verifica se o foco realmente caiu após a colisão
        if after_window['attention'].mean() < before_window['attention'].mean():
            # Procura pelo primeiro momento em que o foco se recupera
            recovery_window = df_valid_signal[
                (df_valid_signal['timestamp'] > event_time) &
                (df_valid_signal['attention'] > FOCUS_THRESHOLD)
            ]
            if not recovery_window.empty:
                recovery_time = recovery_window.iloc[0]['timestamp']
                lfo_seconds = (recovery_time - event_time).total_seconds()
        
        results.append({
            'event_type': event['game_event_type'],
            'focus_change': focus_change,
            'calm_change': calm_change,
            'lfo_seconds': lfo_seconds
        })

    if not results:
        return {}, {}, None

    # Agrega os resultados
    results_df = pd.DataFrame(results)
    focus_variation = results_df.groupby('event_type')['focus_change'].mean().to_dict()
    calm_variation = results_df.groupby('event_type')['calm_change'].mean().to_dict()
    avg_lfo = results_df['lfo_seconds'].dropna().mean()

    return focus_variation, calm_variation, avg_lfo

def calculate_kpis_for_session(session_id: str):
    print(f"[REFINED] Iniciando cálculo de KPIs para a Session ID: {session_id}")
    
    # --- 1. LER DADOS DA CAMADA TRUSTED ---
    trusted_file = TRUSTED_DATA_PATH / f"{session_id}.parquet"
    if not trusted_file.exists():
        print(f"[REFINED] Erro: Arquivo da camada Trusted não encontrado em {trusted_file}")
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

        # --- 2. CALCULAR CADA KPI ---
        
        # KPI: Sessão Válida (%)
        valid_session_pct = (len(df_valid_signal) / len(player_df)) * 100
        
        # KPI: TZF - Tempo em Zona de Foco (%)
        tzf_pct = (df_valid_signal['attention'] > FOCUS_THRESHOLD).sum() / total_valid_readings * 100
        
        # KPI: TZC - Tempo em Zona de Calma (%)
        tzc_pct = (df_valid_signal['meditation'] > CALM_THRESHOLD).sum() / total_valid_readings * 100

        # KPI: CF - Calm Focus (%)
        calm_focus_pct = ((df_valid_signal['attention'] > FOCUS_THRESHOLD) & (df_valid_signal['meditation'] > CALM_THRESHOLD)).sum() / total_valid_readings * 100
        
        # KPI: CVF - Consistência do Foco (Desvio Padrão e Rótulo)
        attention_std_dev = df_valid_signal['attention'].std()
        cvf_label = get_cvf_label(attention_std_dev)
        
        # KPI: Tendência de Fadiga (Theta/Beta Ratio Slope)
        # Adiciona um valor pequeno para evitar divisão por zero
        df_valid_signal['fatigue_ratio'] = df_valid_signal['theta'] / (df_valid_signal['highBeta'] + 1e-6)
        df_valid_signal = df_valid_signal.dropna(subset=['fatigue_ratio'])
        df_valid_signal['time_index'] = np.arange(len(df_valid_signal))
        fatigue_slope = np.polyfit(df_valid_signal['time_index'], df_valid_signal['fatigue_ratio'], 1)[0] if len(df_valid_signal) > 1 else 0

        # KPIs Pós-Evento (Variação e Latência)
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
            'lfo_avg_recovery_seconds': round(avg_lfo, 2) if avg_lfo else None
        }
        
        session_kpis[f'player_{player_id}'] = player_kpis
        print(f"  - KPIs calculados: {json.dumps(player_kpis, indent=2)}")

    # --- 3. SALVAR RESULTADO REFINADO ---
    if session_kpis:
        REFINED_DATA_PATH.mkdir(parents=True, exist_ok=True)
        output_path = REFINED_DATA_PATH / f"{session_id}_summary.json"
        
        with open(output_path, 'w') as f:
            json.dump(session_kpis, f, indent=4)
            
        print(f"\n[REFINED] Sumário de KPIs salvo em {output_path}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        session_id_to_process = sys.argv[1]
        calculate_kpis_for_session(session_id_to_process)
    else:
        print("Uso: python calculate_kpis.py <session_id>")