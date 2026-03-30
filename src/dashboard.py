import streamlit as st
import boto3
import json
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests

load_dotenv()

st.set_page_config(page_title="Telco Pulse | Monitoramento NOC", layout="wide")

# ==========================================
# CSS CUSTOMIZADO (Consertado para unificar os cards)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0f172a !important; 
    }
    
    .titulo-dashboard { font-size: 26px !important; font-weight: 700 !important; color: #f8fafc; margin-bottom: 0px; padding-bottom: 0px; }
    .subtitulo-dashboard { font-size: 14px !important; color: #94a3b8; margin-top: 5px; margin-bottom: 25px; }

    /* Estilo dos Rótulos das Métricas para não truncar o texto */
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 13px !important; font-weight: 500 !important; }
    div[data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 28px !important; font-weight: 700 !important; }

    /* Botões Clean */
    .stButton > button {
        background-color: #1e293b !important; color: #e2e8f0 !important;
        border: 1px solid #334155 !important; border-radius: 4px !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover { border-color: #60a5fa !important; color: #60a5fa !important; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Limpo
st.markdown('<p class="titulo-dashboard">Monitoramento de Infraestrutura: Telco Pulse</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-dashboard">NOC Dashboard - Conectividade TCP e Volume de Incidentes Sociais.</p>', unsafe_allow_html=True)

@st.cache_data(ttl=60)
def buscar_ultimo_dado_s3():
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        bucket = os.getenv('S3_BUCKET_NAME')
        objetos = s3.list_objects_v2(Bucket=bucket, Prefix='raw/')
        
        if 'Contents' in objetos:
            arquivos_ordenados = sorted(objetos['Contents'], key=lambda x: x['LastModified'], reverse=True)
            ultimo_arquivo = arquivos_ordenados[0]['Key']
            resposta = s3.get_object(Bucket=bucket, Key=ultimo_arquivo)
            return json.loads(resposta['Body'].read().decode('utf-8')), ultimo_arquivo
        return None, None
    except Exception:
        return None, None

def disparar_robo_github():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    url = f"https://api.github.com/repos/{repo}/actions/workflows/coleta_automatica.yml/dispatches"
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"}
    resposta = requests.post(url, headers=headers, json={"ref": "main"})
    return resposta.status_code == 204

dados, nome_arquivo = buscar_ultimo_dado_s3()

if dados:
    dt_utc = datetime.fromisoformat(dados['timestamp'])
    dt_formatada = (dt_utc - timedelta(hours=3)).strftime('%H:%M:%S (BRT)')

    col_status, col_espaco, col_btn_s3, col_btn_github = st.columns([3, 1, 1.5, 1.5])
    with col_status:
        st.markdown(f"✅ **Última Coleta Confirmada:** {dt_formatada}")
        st.caption(f"Fonte: AWS S3 ({nome_arquivo[-12:]})")
    with col_btn_s3:
        if st.button("Atualizar Visão", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_btn_github:
        if st.button("Solicitar Coleta Manual", use_container_width=True):
            with st.spinner("Acordando robô..."):
                if disparar_robo_github(): st.toast('Processo de varredura engatilhado no GitHub Actions.', icon='🚀')
                else: st.toast('Erro: Falha de comunicação com a API do GitHub.', icon='❌')

    st.markdown("<hr style='margin: 10px 0px; border-color: #334155;'>", unsafe_allow_html=True)
    
    # SELETOR DE REGIAO
    lista_regioes = ['Nacional', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    col_sel, col_empty = st.columns([3, 4])
    with col_sel:
        regiao_selecionada = st.selectbox("Seletor Regional de Incidentes (Google Trends):", lista_regioes, index=0)
    
    st.write("")
    colunas = st.columns(4)
    df_view = []
    
    # Dicionário com as cores oficiais das marcas para o tema escuro
    cores_marcas = {"Vivo": "#a855f7", "Claro": "#ef4444", "TIM": "#3b82f6", "Oi": "#eab308"}
    
    for index, item in enumerate(dados['telemetria']):
        operadora = item['operadora']
        latencia = item['latencia_ms']
        erro = item['erro_tecnico']
        status_http = item.get('status_http', 200) # Busca o código de retorno
        indice = item['indices_sociais'].get(regiao_selecionada, 0)
        cor_marca = cores_marcas.get(operadora, "#f8fafc")
        
        df_view.append({"Operadora": operadora, "Ping (ms)": latencia, "Retorno": status_http, "Diagnóstico": erro, f"Alertas ({regiao_selecionada})": indice})
        
        with colunas[index]:
            # A mágica do Card Unificado acontece aqui
            with st.container(border=True):
                if erro != "Nenhum" or latencia > 1000:
                    status_badge = "🔴 INDISPONÍVEL"
                elif latencia > 350:
                    status_badge = "🟡 DEGRADADO"
                else:
                    status_badge = "🟢 OPERACIONAL"

                # Título com a cor da marca
                st.markdown(f"<h3 style='margin-bottom:0px; margin-top:0px; color:{cor_marca};'>{operadora}</h3>", unsafe_allow_html=True)
                
                # Prova Técnica visível
                st.markdown(f"**Status:** {status_badge}")
                if erro == "Nenhum":
                    st.markdown(f"<p style='color:#10b981; font-family:monospace; margin-bottom:15px;'>Retorno: {status_http} OK</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color:#ef4444; font-family:monospace; margin-bottom:15px;'>Erro: {erro}</p>", unsafe_allow_html=True)
                
                # Métricas lado a lado sem truncar
                col_met1, col_met2 = st.columns(2)
                with col_met1:
                    st.metric(label="Ping (ms)", value=latencia)
                with col_met2:
                    st.metric(label="Buscas", value=indice)

    st.markdown("<hr style='margin: 20px 0px; border-color: #334155;'>", unsafe_allow_html=True)
    
    with st.expander("Visualizar Base de Dados Bruta (S3 Lake)"):
        st.dataframe(pd.DataFrame(df_view), use_container_width=True)

else:
    st.error("Não foi possível carregar os dados do Amazon S3.")