import yfinance as yf
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import sys
import time

# --- CONFIGURAÇÕES DO TALOS ---
ATIVO = "PETR4.SA"
NOME_PLANILHA = "TALOS_DATASET"
ARQUIVO_CREDS = "creds.json"

def conectar_sheets():
    """Autentica no Google Cloud e conecta à planilha."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDS, scope)
        client = gspread.authorize(creds)
        sheet = client.open(NOME_PLANILHA).sheet1
        return sheet
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha na autenticação: {e}")
        # Se falhar a conexão, não mata o programa, espera e tenta de novo na próxima
        return None

def coletar_dados():
    # Define Fuso Horário de Brasília
    tz = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(tz)
    
    print(f"\n--- TALOS CHECK: {agora.strftime('%H:%M:%S')} ---")

    # Verifica fim de semana
    if agora.weekday() > 4:
        print("Fim de semana. Mercado fechado.")
        return

    # 1. Coleta os dados do dia
    try:
        # Baixa o dia todo para garantir que pegamos o último candle fechado
        df = yf.download(ATIVO, period="1d", interval="1m", progress=False)
    except Exception as e:
        print(f"Erro no Yahoo: {e}")
        return

    if df.empty:
        print("Yahoo retornou vazio (aguardando abertura ou dados).")
        return

    # --- CORREÇÃO DE FUSO HORÁRIO ---
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    df.index = df.index.tz_convert('America/Sao_Paulo')
    # --------------------------------

    # 2. Tratamento de Dados
    df.reset_index(inplace=True)
    
    # Padroniza DataHora como String YYYY-MM-DD HH:MM:SS
    col_data = 'Datetime' if 'Datetime' in df.columns else 'Date'
    if col_data in df.columns:
        df['DataHora'] = df[col_data].dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        df['DataHora'] = df.index.strftime('%Y-%m-%d %H:%M:%S')

    cols_finais = ['DataHora', 'Open', 'High', 'Low', 'Close', 'Volume']
    df_limpo = df[cols_finais].copy()
    df_limpo['TARGET_MANUAL'] = "" 

    # 3. LÓGICA ANTI-DUPLICIDADE (O SEGREDO)
    sheet = conectar_sheets()
    if not sheet: return # Se a conexão falhou, tenta na próxima volta

    todos_dados = sheet.get_all_values()
    
    # Se a planilha já tem dados (tem cabeçalho + linhas)
    if len(todos_dados) > 1:
        # Pega a data da última linha (coluna 0 é a DataHora)
        ultima_data_sheet = todos_dados[-1][0]
        print(f"Último registro na nuvem: {ultima_data_sheet}")
        
        # Filtra: Só quero o que for MAIOR (mais novo) que a última data
        # Isso evita duplicar o que já está lá
        df_para_enviar = df_limpo[df_limpo['DataHora'] > ultima_data_sheet]
        
    else:
        # Planilha vazia ou só cabeçalho
        if len(todos_dados) == 0:
            cabecalho = cols_finais + ['TARGET_MANUAL']
            sheet.append_row(cabecalho)
            print("Cabeçalho criado.")
        
        df_para_enviar = df_limpo

    # 4. Envia apenas o Delta (a diferença)
    qtd_novas = len(df_para_enviar)
    
    if qtd_novas > 0:
        dados_matriz = df_para_enviar.values.tolist()
        try:
            sheet.append_rows(dados_matriz)
            print(f"✅ SUCESSO! {qtd_novas} novas linhas adicionadas.")
        except Exception as e:
            print(f"[ERRO] Ao salvar no Sheets: {e}")
    else:
        print("⏸️ Sem dados novos no Yahoo por enquanto.")

def main():
    print("--- 🛡️ TALOS MONITOR RODANDO ---")
    print("Pressione Ctrl+C para parar.")
    while True:
        coletar_dados()
        # Espera 60 segundos antes de checar de novo
        time.sleep(60)

if __name__ == "__main__":
    main()