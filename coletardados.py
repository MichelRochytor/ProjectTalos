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
NOME_PLANILHA = "TALOS_DATASET" # Nome exato da planilha no Google Drive
ARQUIVO_CREDS = "creds.json"    # Arquivo de chave que você subiu para a VM

def conectar_sheets():
    """Autentica no Google Cloud e conecta à planilha."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDS, scope)
        client = gspread.authorize(creds)
        sheet = client.open(NOME_PLANILHA).sheet1
        return sheet
    except Exception as e:
        print(f"[ERRO] Falha na autenticação do Google Sheets: {e}")
        print("DICA: Verifique se você compartilhou a planilha com o e-mail do arquivo JSON.")
        sys.exit()

def coletar_dados():
    # Define Fuso Horário de Brasília
    tz = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(tz)
    
    print(f"\n--- INICIANDO TALOS COLLECTOR: {agora.strftime('%d/%m/%Y %H:%M:%S')} ---")

    # Verifica se é fim de semana (Sábado=5, Domingo=6)
    if agora.weekday() > 4:
        print("Hoje é fim de semana. Mercado fechado. Encerrando.")
        return

    # 1. Coleta os dados do dia (Intervalo de 1 minuto)
    print(f"📡 Baixando dados intraday de {ATIVO} via Yahoo Finance...")
    try:
        # Tenta baixar. Se falhar, tenta de novo após 5 segundos
        df = yf.download(ATIVO, period="1d", interval="1m", progress=False)
        if df.empty:
            print("⚠️ Yahoo retornou dados vazios (Talvez feriado ou pré-market).")
            return
    except Exception as e:
        print(f"[ERRO] Falha no yfinance: {e}")
        return

    # 2. Tratamento de Dados
    df.reset_index(inplace=True)
    
    # Tratamento de Data/Hora (converte para string compatível com Sheets)
    if 'Datetime' in df.columns:
        df['DataHora'] = df['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    elif 'Date' in df.columns:
        df['DataHora'] = df['Date'].astype(str)
    else:
        df['DataHora'] = df.index.strftime('%Y-%m-%d %H:%M:%S')

    # Organiza as colunas e remove dados desnecessários
    # Adicionamos uma coluna vazia 'MANUAL_LABEL' para você preencher depois
    cols_finais = ['DataHora', 'Open', 'High', 'Low', 'Close', 'Volume']
    df_limpo = df[cols_finais].copy()
    
    # Adiciona coluna para o Gabarito (0 = Neutro, 1 = Compra, 2 = Venda)
    df_limpo['TARGET_MANUAL'] = "" 

    # Converte para lista de listas (formato que o Gspread aceita)
    dados_matriz = df_limpo.values.tolist()

    # 3. Envio para a Nuvem
    print("☁️ Conectando ao Google Sheets...")
    sheet = conectar_sheets()
    
    # Se a planilha estiver vazia, cria o cabeçalho
    if len(sheet.get_all_values()) == 0:
        cabecalho = cols_finais + ['TARGET_MANUAL']
        sheet.append_row(cabecalho)
        print("📝 Cabeçalho criado com sucesso.")

    print(f"📤 Enviando {len(dados_matriz)} linhas de dados...")
    
    try:
        sheet.append_rows(dados_matriz)
        print(f"✅ SUCESSO! Dados de {agora.strftime('%d/%m/%Y')} salvos.")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar linhas: {e}")

if __name__ == "__main__":
    coletar_dados()