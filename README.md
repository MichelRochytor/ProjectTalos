# Project TALOS

Project TALOS é um sistema de trading algorítmico focado na análise e operação do ativo **PETR4 (Petrobras)** na bolsa de valores brasileira. O projeto utiliza uma arquitetura híbrida (Nuvem + Local) para coleta de dados, engenharia de features e treinamento de modelos de Machine Learning.

## 🏛️ Sobre o Projeto

O objetivo do TALOS não é apenas operar, mas criar um pipeline robusto de **Data Science** aplicado ao mercado financeiro. O sistema resolve o problema da falta de dados intraday (minuto a minuto) gratuitos e estruturados, criando seu próprio *Golden Dataset* para treino de Inteligência Artificial.

### Por que TALOS?
Na mitologia grega, Talos era um gigante autômato de bronze construído por Hefesto para proteger a Europa. Da mesma forma, este software visa proteger o capital e executar operações com a precisão de uma máquina.

## 🏗️ Arquitetura do Sistema

O projeto opera em um fluxo de três estágios:

1.  **Coleta (Cloud - GCP):**
    * Uma instância VM (Google Compute Engine) roda scripts cronometrados.
    * Os dados de mercado (Preço, Volume) são extraídos via API (`yfinance`) em intervalos de 1 minuto.
    * **Tech:** Python, Linux (Debian), Crontab.

2.  **Armazenamento (Data Lakehouse - Sheets):**
    * Utilização do Google Sheets como banco de dados em tempo real.
    * Facilita a visualização móvel e elimina a necessidade de transferências manuais de arquivos `.csv`.
    * **Tech:** Google Sheets API, Gspread.

3.  **Inteligência (Local - Workstation):**
    * Ambiente local para processamento pesado.
    * Rotulagem de dados (Criação de "Book Manual" de compra/venda).
    * Treinamento de modelos (Random Forest/LSTM).
    * Backtesting de estratégias.
    * **Tech:** Jupyter Notebook, Pandas, Scikit-learn, Matplotlib.
