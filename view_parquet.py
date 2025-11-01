import duckdb
import pandas as pd
from pathlib import Path

# --- Configure o caminho para o arquivo Parquet que você quer ver ---
# Substitua pelo nome do arquivo que você gerou
SESSION_ID = "test-session-df492c66-7638-49ec-b686-40a089413e99"
file_path = Path("data_pipeline") / "data" / "trusted_data" / f"{SESSION_ID}.parquet"

if not file_path.exists():
    print(f"Erro: Arquivo não encontrado em '{file_path}'")
else:
    print(f"Lendo dados de: '{file_path}'\n")
    
    # Conecta ao DuckDB (não precisa de servidor, ele roda em memória)
    con = duckdb.connect()
    
    # O DuckDB pode consultar arquivos Parquet diretamente com SQL!
    # Vamos ver as primeiras 10 linhas da nossa tabela unificada.
    print("--- 10 Primeiras Linhas da Tabela Trusted ---")
    result_df = con.execute(f"""
        SELECT * 
        FROM read_parquet('{file_path}')
        LIMIT 10
    """).fetch_df()
    
    print(result_df)
    
    # Vamos fazer uma agregação simples para provar que funciona
    print("\n--- Média de Atenção por Jogador ---")
    avg_attention = con.execute(f"""
        SELECT 
            player, 
            AVG(attention) as avg_attention,
            COUNT(*) as total_readings
        FROM read_parquet('{file_path}')
        WHERE is_signal_valid = TRUE
        GROUP BY player
    """).fetch_df()
    
    print(avg_attention)