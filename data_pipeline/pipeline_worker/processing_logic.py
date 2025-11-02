import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta, datetime
import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Configura um logger para este módulo. A configuração (formato, nível) será feita no entrypoint (worker.py)
log = logging.getLogger(__name__)

# --- Configuração dos Parâmetros de Análise ---
FOCUS_THRESHOLD = 70
CALM_THRESHOLD = 60
PERCENTILES_TO_CALCULATE = [25, 50, 75, 90]

# ==============================================================================
# SEÇÃO 1: LÓGICA DO ETL (RAW -> TRUSTED)
# ==============================================================================
def load_eeg_data(session_path: Path) -> pd.DataFrame:
    all_eeg_data = []
    eeg_files = list(session_path.glob("player_*_eeg.jsonl"))
    for file_path in eeg_files:
        try:
            df = pd.read_json(file_path, lines=True)
            all_eeg_data.append(df)
        except Exception:
            log.warning(f"Falha ao ler ou parsear o arquivo de EEG: {file_path}", exc_info=True)
    if not all_eeg_data:
        return pd.DataFrame()
    return pd.concat(all_eeg_data, ignore_index=True)

def load_game_events(session_path: Path) -> pd.DataFrame:
    events_file = session_path / "game_events.jsonl"
    if not events_file.exists():
        return pd.DataFrame()
    try:
        return pd.read_json(events_file, lines=True)
    except Exception:
        log.warning(f"Falha ao ler ou parsear o arquivo de eventos: {events_file}", exc_info=True)
        return pd.DataFrame()

def transform_and_merge(eeg_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
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
    final_columns = ['timestamp', 'player', 'attention', 'meditation', 'poorSignalLevel', 'is_signal_valid', 'game_event_type', 'delta', 'theta', 'lowAlpha', 'highAlpha', 'lowBeta', 'highBeta', 'lowGamma', 'highGamma']
    existing_columns = [col for col in final_columns if col in combined_df.columns]
    return combined_df[existing_columns]

def process_session(session_id: str, raw_path: Path, trusted_path: Path):
    log.info(f"Iniciando processamento ETL para a Session ID: {session_id}")
    session_raw_path = raw_path / session_id
    if not session_raw_path.exists():
        raise FileNotFoundError(f"Diretório da sessão não encontrado em {session_raw_path}")
    eeg_df = load_eeg_data(session_raw_path)
    events_df = load_game_events(session_raw_path)
    if eeg_df.empty:
        log.warning("Nenhum dado de EEG encontrado para a sessão. Processo ETL abortado.")
        return
    trusted_df = transform_and_merge(eeg_df, events_df)
    trusted_path.mkdir(parents=True, exist_ok=True)
    output_path = trusted_path / f"{session_id}.parquet"
    trusted_df.to_parquet(output_path, index=False, compression='snappy')
    log.info(f"Camada Trusted salva com sucesso em {output_path}")

# ==============================================================================
# SEÇÃO 2: LÓGICA DE DATA SCIENCE, COACHING E ATUALIZAÇÃO DE USUÁRIOS
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

def update_global_stats(db, session_kpis):
    # ... (código existente)
    log.info("Atualizando estatísticas globais...")
    stats_ref = db.collection('global_stats').document('summary')
    @firestore.transactional
    def update_in_transaction(transaction, stats_ref, current_session_kpis):
        snapshot = stats_ref.get(transaction=transaction)
        stats = snapshot.to_dict() if snapshot.exists else {'all_tzf': [], 'all_lfo': []}
        for _, kpis in current_session_kpis.items():
            stats['all_tzf'].append(kpis['tzf_percentage'])
            if kpis.get('lfo_avg_recovery_seconds') is not None:
                stats['all_lfo'].append(kpis['lfo_avg_recovery_seconds'])
        all_tzf_series = pd.Series(stats['all_tzf'])
        all_lfo_series = pd.Series(stats['all_lfo'])
        stats['totalRacesAnalyzed'] = len(all_tzf_series)
        stats['averageTzf'] = all_tzf_series.mean()
        stats['averageLfoSeconds'] = all_lfo_series.mean()
        tzf_percentiles = all_tzf_series.quantile([p/100 for p in PERCENTILES_TO_CALCULATE]).to_dict()
        lfo_percentiles = all_lfo_series.quantile([p/100 for p in PERCENTILES_TO_CALCULATE]).to_dict()
        stats['percentiles'] = {
            'tzf': {str(p): v for p, v in tzf_percentiles.items()},
            'lfoSeconds': {str(p): v for p, v in lfo_percentiles.items()}
        }
        transaction.set(stats_ref, stats)
    transaction = db.transaction()
    update_in_transaction(transaction, stats_ref, session_kpis)
    log.info("Estatísticas globais atualizadas com sucesso.")

def generate_match_feedback(player_kpis, global_stats):
    # ... (código existente)
    feedback_parts = []
    feedback_matrix = {
        "tzf": {
            "p90": "Performance de elite! Seu foco nesta corrida te colocou no top 10% do evento.",
            "p75": "Excelente! Sua concentração ficou entre os 25% melhores, um resultado impressionante.",
            "p50": "Acima da média! Você demonstrou um controle atencional sólido e consistente.",
            "default": "Bom esforço! Manter o foco sob pressão é o primeiro passo para a maestria."
        },
        "lfo": {
            "p10": "Sua resiliência foi notável! Você se recuperou de erros mais rápido que 90% dos competidores.",
            "p25": "Muito resiliente! Sua capacidade de 'resetar' o foco após um erro é um grande diferencial.",
            "default": "Manter a calma após um erro é um desafio. Continue praticando para diminuir seu tempo de reação."
        }
    }
    tzf = player_kpis['tzf_percentage']
    tzf_percentiles = global_stats.get('percentiles', {}).get('tzf', {})
    if tzf > tzf_percentiles.get('0.9', float('inf')): feedback_parts.append(feedback_matrix['tzf']['p90'])
    elif tzf > tzf_percentiles.get('0.75', float('inf')): feedback_parts.append(feedback_matrix['tzf']['p75'])
    elif tzf > tzf_percentiles.get('0.5', float('inf')): feedback_parts.append(feedback_matrix['tzf']['p50'])
    else: feedback_parts.append(feedback_matrix['tzf']['default'])
    lfo = player_kpis.get('lfo_avg_recovery_seconds')
    if lfo is not None:
        lfo_percentiles = global_stats.get('percentiles', {}).get('lfoSeconds', {})
        if lfo < lfo_percentiles.get('0.1', float('-inf')): feedback_parts.append(feedback_matrix['lfo']['p10'])
        elif lfo < lfo_percentiles.get('0.25', float('-inf')): feedback_parts.append(feedback_matrix['lfo']['p25'])
        else: feedback_parts.append(feedback_matrix['lfo']['default'])
    return " ".join(feedback_parts)


def generate_evolution_feedback(user_profile):
    # ... (código existente)
    history = user_profile.get('raceHistory', [])
    if len(history) < 3:
        return "Continue jogando! Após 3 corridas, começaremos a analisar sua evolução e te dar dicas sobre seu progresso."
    tzf_history = [race['tzf'] for race in history]
    primeiras_corridas_avg = np.mean(tzf_history[:3])
    ultimas_corridas_avg = np.mean(tzf_history[-3:])
    if ultimas_corridas_avg > primeiras_corridas_avg * 1.1:
        return f"Progresso notável! Seu Foco médio saltou de {primeiras_corridas_avg:.1f}% para {ultimas_corridas_avg:.1f}% em suas últimas corridas. Continue assim!"
    elif ultimas_corridas_avg < primeiras_corridas_avg * 0.9:
        return "Parece que seu foco tem oscilado um pouco. Que tal revisar suas últimas corridas e ver o que mudou? Uma boa noite de sono pode fazer toda a diferença!"
    else:
        return "Você está mantendo um nível de performance consistente, o que é ótimo! O próximo desafio é encontrar novas estratégias para quebrar esse platô e alcançar um novo patamar de foco."

def update_user_profiles(db, session_id, session_kpis, events_df):
    # ... (código existente)
    log.info("Iniciando atualização de perfis de usuário...")
    start_event_rows = events_df[events_df['eventType'] == 'raceStarted']
    if start_event_rows.empty:
        log.warning("Evento 'raceStarted' não encontrado. Pulando atualização de perfis.")
        return
    user_map_list = start_event_rows.iloc[0].get('users', [])
    if not user_map_list:
        log.warning("Mapeamento de usuários (com email) não encontrado. Pulando atualização de perfis.")
        return
    user_mapping = {item['playerId']: item['email'] for item in user_map_list}
    finish_events = events_df[events_df['eventType'] == 'hasFinished']
    race_times = {row['player']: row['raceTimeSeconds'] for _, row in finish_events.iterrows()}
    winner_id = min(race_times, key=race_times.get) if race_times else None
    for player_id_str, kpis in session_kpis.items():
        player_id = int(player_id_str.split('_')[1])
        email = user_mapping.get(player_id)
        if not email: continue
        log.info(f"Processando perfil para o email: {email} (Player {player_id})")
        users_ref = db.collection('users')
        user_query = users_ref.where('email', '==', email).limit(1).get()
        user_ref = user_query[0].reference if user_query else users_ref.document()
        log.info(f"Usuário {'encontrado' if user_query else 'novo'}. ID do Documento: {user_ref.id}")
        @firestore.transactional
        def update_in_transaction(transaction, user_ref):
            snapshot = user_ref.get(transaction=transaction)
            new_data = snapshot.to_dict() if snapshot.exists else {"email": email, "createdAt": datetime.utcnow().isoformat()}
            new_data['totalRaces'] = new_data.get('totalRaces', 0) + 1
            if player_id == winner_id: new_data['totalWins'] = new_data.get('totalWins', 0) + 1
            new_data['winPercentage'] = (new_data.get('totalWins', 0) / new_data['totalRaces'])
            current_race_time = race_times.get(player_id)
            if current_race_time and current_race_time < new_data.get('bestRaceTimeSeconds', float('inf')):
                new_data['bestRaceTimeSeconds'] = current_race_time
            if kpis['tzf_percentage'] > new_data.get('personalBestTzf', 0):
                new_data['personalBestTzf'] = kpis['tzf_percentage']
            history = new_data.get('raceHistory', [])
            new_race_summary = {"sessionId": session_id, "raceTimestamp": datetime.utcnow().isoformat(), "tzf": kpis['tzf_percentage'], "tzc": kpis['tzc_percentage'],"fatigueSlope": kpis['fatigue_slope'], "lfoSeconds": kpis['lfo_avg_recovery_seconds']}
            history.append(new_race_summary)
            new_data['raceHistory'] = history[-10:]
            new_data['evolutionFeedback'] = generate_evolution_feedback(new_data)
            transaction.set(user_ref, new_data)
        transaction = db.transaction()
        update_in_transaction(transaction, user_ref)
    log.info("Perfis de usuário atualizados com sucesso.")


def calculate_kpis_for_session(session_id: str, trusted_path: Path, refined_path: Path, raw_path: Path):
    log.info(f"Iniciando cálculo de KPIs para a Session ID: {session_id}")
    trusted_file = trusted_path / f"{session_id}.parquet"
    if not trusted_file.exists(): raise FileNotFoundError("Arquivo da camada Trusted não encontrado.")
    df = pd.read_parquet(trusted_file)
    players = df['player'].dropna().unique()
    session_kpis = {}
    for player_id in players:
        player_id = int(player_id)
        log.info(f"Calculando KPIs para o Jogador {player_id}...")
        player_df = df[df['player'] == player_id].copy()
        df_valid_signal = player_df[player_df['is_signal_valid']].copy()
        if df_valid_signal.empty:
            log.warning(f"Nenhum dado com sinal válido para o Jogador {player_id}. Pulando.")
            continue
        total_valid_readings = len(df_valid_signal)
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
        player_kpis = {'valid_session_percentage': round(valid_session_pct, 2), 'tzf_percentage': round(tzf_pct, 2), 'tzc_percentage': round(tzc_pct, 2), 'calm_focus_percentage': round(calm_focus_pct, 2), 'cvf_label': cvf_label, 'cvf_attention_std_dev': round(attention_std_dev, 2), 'fatigue_slope': round(fatigue_slope, 5), 'post_event_focus_variation': focus_variation, 'post_event_calm_variation': calm_variation, 'lfo_avg_recovery_seconds': round(avg_lfo, 2) if avg_lfo is not None and pd.notna(avg_lfo) else None}
        session_kpis[f'player_{player_id}'] = player_kpis
        log.debug(f"KPIs calculados para Player {player_id}: {json.dumps(player_kpis, indent=2)}")

    if session_kpis:
        try:
            log.info("Autenticando com Firebase...")
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            update_global_stats(db, session_kpis)
            global_stats_doc = db.collection('global_stats').document('summary').get()
            global_stats = global_stats_doc.to_dict() if global_stats_doc.exists else {}
            for player_key, kpis in session_kpis.items():
                kpis['coachFeedback'] = generate_match_feedback(kpis, global_stats)
            doc_ref = db.collection('sessions').document(session_id)
            doc_ref.set(session_kpis)
            log.info(f"Dados da sessão {session_id} (com feedback) salvos com sucesso!")
            
            events_df = load_game_events(raw_path / session_id)
            if not events_df.empty:
                update_user_profiles(db, session_id, session_kpis, events_df)
        except Exception:
            log.critical("Falha crítica na comunicação com o Firestore ou na atualização de perfis.", exc_info=True)
            
        # Salva o resultado localmente, mesmo se o Firebase falhar
        refined_path.mkdir(parents=True, exist_ok=True)
        output_path = refined_path / f"{session_id}_summary.json"
        with open(output_path, 'w') as f:
            json.dump(session_kpis, f, indent=4)
        log.info(f"Sumário de KPIs salvo localmente em {output_path}")