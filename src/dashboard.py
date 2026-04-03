import streamlit as st
import boto3
import json
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

st.set_page_config(page_title="Telco Pulse | Monitoramento NOC", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# DESIGN SYSTEM - TELCO PULSE
# ==========================================
# Implementamos um design moderno tipo "Bloomberg Terminal"
# com foco em leitura rápida, cores que indicam status, e hierarquia visual clara.

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        box-sizing: border-box;
    }
    
    /* Paleta de Cores */
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #1e293b;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
    }
    
    /* Fundo e Estrutura Base */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #0f172a 0%, #1a1f35 100%) !important;
        background-attachment: fixed !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    
    /* Header Premium */
    .header-container {
        background: linear-gradient(90deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
        border-bottom: 1px solid rgba(51, 65, 85, 0.3);
        padding: 24px 32px;
        margin: -24px -24px 24px -24px;
        backdrop-filter: blur(10px);
        border-radius: 0 0 12px 12px;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    
    .logo-icon {
        font-size: 28px;
        font-weight: 700;
        color: #60a5fa;
    }
    
    .titulo-dashboard {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: -0.5px;
    }
    
    .subtitulo-dashboard {
        font-size: 13px !important;
        color: #94a3b8 !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
        font-weight: 400 !important;
    }
    
    /* Status Badge Elegante (sem emojis) */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin: 8px 0;
    }
    
    .status-operational {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-degraded {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .status-unavailable {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Cards Premium */
    .operative-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.6));
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    .operative-card:hover {
        border-color: rgba(96, 165, 250, 0.4);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transform: translateY(-2px);
    }
    
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(20, 28, 45, 0.8));
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-left: 3px solid #60a5fa;
        border-radius: 10px;
        padding: 16px;
        transition: all 0.3s ease;
    }
    
    .kpi-label {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    
    .kpi-value {
        color: #f8fafc;
        font-size: 28px;
        font-weight: 700;
        line-height: 1;
    }
    
    .kpi-change {
        color: #94a3b8;
        font-size: 11px;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Operadora Titles */
    .operadora-title {
        font-size: 18px !important;
        font-weight: 700 !important;
        margin-bottom: 4px !important;
        margin-top: 0 !important;
    }
    
    /* Métricas Refinadas */
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 26px !important;
        font-weight: 700 !important;
    }
    
    /* Botões Refined */
    .stButton > button {
        background: linear-gradient(135deg, #1e293b, #0f172a) !important;
        color: #e2e8f0 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 10px 16px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #334155, #1e293b) !important;
        border-color: #60a5fa !important;
        color: #60a5fa !important;
        box-shadow: 0 0 20px rgba(96, 165, 250, 0.2) !important;
    }
    
    /* Dividers Elegantes */
    .elegant-divider {
        margin: 24px 0 !important;
        border: 0 !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(51, 65, 85, 0.5), transparent) !important;
    }
    
    /* Section Titles */
    .section-title {
        color: #f8fafc !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        margin-top: 32px !important;
        margin-bottom: 20px !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .section-icon {
        color: #60a5fa;
        font-size: 22px;
    }
    
    /* Selectbox Refined */
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }
    
    /* Expander Refined */
    [data-testid="stExpander"] button {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stExpander"] summary {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* DataTable Styling */
    [data-testid="stDataFrame"] {
        background-color: transparent !important;
    }
    
    .dataframe-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(20, 28, 45, 0.4));
        border: 1px solid rgba(51, 65, 85, 0.3);
        border-radius: 8px;
        padding: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER PREMIUM
# ==========================================
st.markdown('''<div class="header-container">
    <div class="logo-section">
        <span class="logo-icon">■</span>
        <div>
            <p class="titulo-dashboard">Telco Pulse</p>
            <p class="subtitulo-dashboard">NOC Dashboard • Monitoramento de Infraestrutura em Tempo Real</p>
        </div>
    </div>
</div>''', unsafe_allow_html=True)

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

@st.cache_data(ttl=60)
def buscar_ultimo_dado_s3():
    """
    Puxa o arquivo mais recente de telemetria do S3.
    Cache de 60s evita sobrecarregar a AWS.
    """
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
            # Ordena por data e pega o mais recente
            arquivos_ordenados = sorted(objetos['Contents'], key=lambda x: x['LastModified'], reverse=True)
            ultimo_arquivo = arquivos_ordenados[0]['Key']
            resposta = s3.get_object(Bucket=bucket, Key=ultimo_arquivo)
            return json.loads(resposta['Body'].read().decode('utf-8')), ultimo_arquivo
        return None, None
    except Exception as erro_s3:
        st.warning(f"Falha ao buscar S3: {erro_s3}")
        return None, None

def disparar_coleta_manual():
    """
    Ativa uma coleta de dados via GitHub Actions.
    Útil quando queremos forçar uma atualização sem esperar o próximo ciclo automático.
    """
    import requests
    
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    url = f"https://api.github.com/repos/{repo}/actions/workflows/coleta_telco.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        resposta = requests.post(url, headers=headers, json={"ref": "main"})
        return resposta.status_code == 204
    except Exception:
        return False

def gerar_status_badge(erro_deteccao: str, latencia_ms: int, maior_alerta_regional: float) -> tuple:
    """
    Determina o status operacional baseado em 3 métricas técnicas:
    - erro_deteccao: Se tem erro TCP detectado
    - latencia_ms: Tempo de resposta (>1s é preocupante)
    - maior_alerta_regional: Pico de menções em Trends (indica reclamações em massa)
    """
    if erro_deteccao != "Nenhum" or latencia_ms > 1000 or maior_alerta_regional > 70:
        return "INDISPONÍVEL", "status-unavailable"
    elif latencia_ms > 350 or maior_alerta_regional > 40:
        return "DEGRADADO", "status-degraded"
    else:
        return "OPERACIONAL", "status-operational"

# ==========================================
# CARREGAMENTO INICIAL DE DADOS
# ==========================================

dados, nome_arquivo = buscar_ultimo_dado_s3()

if dados:
    # Converte timestamp ISO para hora local (BRT = UTC-3)
    dt_utc = datetime.fromisoformat(dados['timestamp'])
    dt_formatada = (dt_utc - timedelta(hours=3)).strftime('%H:%M:%S')
    dt_data = (dt_utc - timedelta(hours=3)).strftime('%d de %B de %Y')
    
    # ==========================================
    # PAINEL DE CONTROLE - INFO + BOTÕES
    # ==========================================
    col_info, col_refresh, col_manual = st.columns([2, 1, 1])
    
    with col_info:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(20, 28, 45, 0.5)); 
                    border: 1px solid rgba(51, 65, 85, 0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;'>
            <span style='color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase;'>Última Coleta Confirmada</span><br>
            <span style='color: #f8fafc; font-size: 14px; font-weight: 600;'>{dt_formatada} BRT</span><br>
            <span style='color: #60a5fa; font-size: 11px;'>Fonte: AWS S3 • {nome_arquivo[-12:]}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_refresh:
        # Atualiza o cache para puxar dados frescos
        if st.button("Atualizar", use_container_width=True, key="btn_refresh"):
            st.cache_data.clear()
            st.rerun()
    
    with col_manual:
        # Trigger manual da coleta - útil se quisermos dados mais frescos agora
        if st.button("Coleta Manual", use_container_width=True, key="btn_manual"):
            with st.spinner("Ativando sensor..."):
                if disparar_coleta_manual():
                    st.toast('Coleta iniciada no GitHub Actions')
                else:
                    st.toast('Falha ao comunicar com GitHub API')
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # FILTRO REGIONAL + KPIs
    # ==========================================
    
    # Permite análise granular por estado - Google Trends tem dados por região
    lista_regioes = ['Nacional', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    col_sel, col_empty = st.columns([2, 5])
    with col_sel:
        regiao_selecionada = st.selectbox("Análise por Região", lista_regioes, index=0, help="Filtra alertas por estado")
    
    st.markdown('<div class="section-title"><span class="section-icon">─</span>Indicadores-Chave de Performance</div>', unsafe_allow_html=True)
    
    # Calcula KPIs a partir dos dados brutos
    total_operadoras_problematicas = sum(1 for item in dados['telemetria'] if item['erro_tecnico'] != "Nenhum" or item['latencia_ms'] > 1000)
    media_latencia_geral = sum(item['latencia_ms'] for item in dados['telemetria']) / len(dados['telemetria'])
    alertas_totais_nacional = sum(max(item['indices_sociais'].values()) for item in dados['telemetria'])
    
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        operadoras_ok = len(dados['telemetria']) - total_operadoras_problematicas
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-label">Status Geral</div>
            <div class="kpi-value" style="color: #10b981;">{operadoras_ok}/{len(dados['telemetria'])}</div>
            <div class="kpi-change">Operadoras Operacionais</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with kpi_cols[1]:
        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: #f59e0b;">
            <div class="kpi-label">Latência Média</div>
            <div class="kpi-value" style="color: #f59e0b;">{media_latencia_geral:.0f}</div>
            <div class="kpi-change">Milissegundos · TCP 443</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with kpi_cols[2]:
        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: #ef4444;">
            <div class="kpi-label">Picos de Alertas</div>
            <div class="kpi-value" style="color: #ef4444;">{alertas_totais_nacional:.0f}</div>
            <div class="kpi-change">Maior menção em Trends</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with kpi_cols[3]:
        # Calcula "idade" dos dados em formato amigável
        dt_coleta = datetime.fromisoformat(dados['timestamp'])
        
        # Garante que ambas as datas estejam em UTC
        if dt_coleta.tzinfo is None:
            dt_coleta = dt_coleta.replace(tzinfo=timezone.utc)
        agora = datetime.now(timezone.utc)
        
        # Calcula diferença e evita números negativos
        tempo_decorrido = agora - dt_coleta
        minutos_totais = max(0, int(tempo_decorrido.total_seconds() / 60))
        
        # Formata para apresentação
        horas, minutos = divmod(minutos_totais, 60)
        tempo_texto = f"{horas}h {minutos}m" if horas > 0 else f"{minutos}m"

        st.markdown(f'''
        <div class="kpi-card" style="border-left-color: #3b82f6;">
            <div class="kpi-label">Tempo dos Dados</div>
            <div class="kpi-value" style="color: #3b82f6;">{tempo_texto}</div>
            <div class="kpi-change">Atrás · Coleta Automática</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # CARDS DAS OPERADORAS
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">◉</span>Status das Operadoras</div>', unsafe_allow_html=True)
    
    colunas = st.columns(4)
    df_view = []
    
    # Cores que correspondem à marca das operadoras (usado para destacar cards)
    cores_marcas = {"Vivo": "#a855f7", "Claro": "#ef4444", "TIM": "#3b82f6", "Oi": "#eab308"}
    
    for index, item in enumerate(dados['telemetria']):
        operadora = item['operadora']
        latencia_ms = item['latencia_ms']
        erro_tecnico = item['erro_tecnico']
        status_http = item.get('status_http', 200)
        indice_regional = item['indices_sociais'].get(regiao_selecionada, 0)
        cor_marca = cores_marcas.get(operadora, "#f8fafc")
        
        # Pega o maior alerta em qualquer região (mais crítico)
        maior_alerta = max(item['indices_sociais'].values())
        
        df_view.append({
            "Operadora": operadora,
            "Ping (ms)": latencia_ms,
            "Status": status_http,
            "Diagnóstico": erro_tecnico,
            f"Alertas ({regiao_selecionada})": indice_regional
        })
        
        with colunas[index]:
            status_texto, css_status = gerar_status_badge(erro_tecnico, latencia_ms, maior_alerta)
            
            st.markdown(f'''
            <div class="operative-card">
                <h3 class="operadora-title" style="color: {cor_marca};">{operadora}</h3>
                <div class="status-badge {css_status}">{status_texto}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Exibe métricas técnicas lado a lado
            met_col1, met_col2 = st.columns(2)
            with met_col1:
                st.metric("Ping", f"{latencia_ms}ms")
            with met_col2:
                st.metric("Alertas", f"{indice_regional:.0f}")
            
            # Mostra resultado do teste TCP
            if erro_tecnico == "Nenhum":
                st.markdown(f'<p style="color: #10b981; font-family: monospace; font-size: 12px; margin: 8px 0;">TCP OK</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color: #ef4444; font-family: monospace; font-size: 12px; margin: 8px 0;">{erro_tecnico}</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # ANÁLISE PARA TOMADA DE DECISÃO
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">▦</span>Análise Regional de Incidentes</div>', unsafe_allow_html=True)
    
    # Agrega dados por estado para visualização e identificação de hotspots
    estado_totais = {}
    operadora_totais = {}
    
    for item in dados['telemetria']:
        operadora = item['operadora']
        indices_sociais = item['indices_sociais']
        operadora_totais[operadora] = indices_sociais.get(regiao_selecionada, 0)
        
        # Soma alertas por estado (mais fácil ver "quais estados estão em pior estado")
        for estado, valor in indices_sociais.items():
            if estado != 'Nacional':
                estado_totais[estado] = estado_totais.get(estado, 0) + valor
    
    # Identifica os 5 estados com maior volume de reclamações
    top5_estados = sorted(estado_totais.items(), key=lambda x: x[1], reverse=True)[:5]
    df_top5 = pd.DataFrame(top5_estados, columns=['Estado', 'Volume'])
    df_top5['Volume'] = df_top5['Volume'].round(1)
    
    # Classifica risco para facilitar leitura rápida
    def classificar_risco(volume):
        if volume > 60:
            return 'ALTO RISCO'
        elif volume > 40:
            return 'MÉDIO RISCO'
        else:
            return 'BAIXO RISCO'
    df_top5['Risco'] = df_top5['Volume'].apply(classificar_risco)
    
    # Prepara distribuição por operadora
    df_ops = pd.DataFrame(list(operadora_totais.items()), columns=['Operadora', 'Volume'])
    volume_total = df_ops['Volume'].sum()
    if volume_total > 0:
        df_ops['Percentual'] = (df_ops['Volume'] / volume_total * 100).round(1).astype(str) + '%'
    else:
        df_ops['Percentual'] = '0.0%'
    df_ops['Volume'] = df_ops['Volume'].round(0).astype(int)
    
    # Exibe gráficos lado a lado
    col_graf1, col_graf2 = st.columns(2)
    
    mapa_risco = {'ALTO RISCO': '#ef4444', 'MÉDIO RISCO': '#f59e0b', 'BAIXO RISCO': '#10b981'}
    
    with col_graf1:
        # Ranking de estados mais afetados
        fig_barra = px.bar(
            df_top5, x='Estado', y='Volume',
            text_auto=True,
            color='Risco',
            color_discrete_map=mapa_risco,
            title="Estados Mais Afetados (Top 5)"
        )
        fig_barra.update_traces(textposition='outside', cliponaxis=False)
        fig_barra.update_layout(
            title=dict(text="Estados Mais Afetados (Top 5)", font=dict(size=16, color='#e2e8f0'), x=0),
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title='', tickfont=dict(color='#94a3b8')),
            yaxis=dict(showgrid=True, gridcolor='rgba(51, 65, 85, 0.2)', title='', showticklabels=False),
            margin=dict(l=0, r=0, t=40, b=0),
            hovermode=False,
            showlegend=False,
            font=dict(color='#e2e8f0', family='Inter')
        )
        st.plotly_chart(fig_barra, use_container_width=True, config={'displayModeBar': False})
    
    with col_graf2:
        # Mostra qual operadora tem mais menções (social listening)
        fig_pizza = px.pie(
            df_ops, values='Volume', names='Operadora',
            hole=0.6,
            color='Operadora', 
            color_discrete_map=cores_marcas,
            custom_data=['Percentual']
        )
        fig_pizza.update_traces(
            textposition='inside',
            textinfo='percent',
            hovertemplate="<b>%{label}</b><br>Participação: %{customdata[0]}<extra></extra>",
            marker=dict(line=dict(color='rgba(15, 23, 42, 0.95)', width=2))
        )
        fig_pizza.update_layout(
            title=dict(text=f"Distribuição de Alertas ({regiao_selecionada})", font=dict(size=16, color='#e2e8f0'), x=0),
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color='#e2e8f0')),
            margin=dict(l=0, r=0, t=40, b=50),
            font=dict(color='#e2e8f0', family='Inter')
        )
        st.plotly_chart(fig_pizza, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================
    # VISUALIZAÇÃO DE DADOS BRUTOS
    # ==========================================
    st.markdown('<div class="section-title"><span class="section-icon">◈</span>Dados Operacionais</div>', unsafe_allow_html=True)
    
    with st.expander("Detalhar Matriz de Telemetria", expanded=False):
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        df_view_limpo = pd.DataFrame(df_view).head(4)
        st.dataframe(
            df_view_limpo.style.format({
                "Ping (ms)": "{:.0f}",
                f"Alertas ({regiao_selecionada})": "{:.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ==========================================
    # GUIA DE INTERPRETAÇÃO
    # ==========================================
    with st.expander("Entender as Métricas do NOC", expanded=False):
        st.markdown("""
        ### Como Funciona o Monitoramento
        
        **Telemetria Técnica (Testes TCP)**
        - Conecta direto aos servidores centrais das operadoras (porta 443)
        - Latência > 1200ms é preocupante (indica congestão ou problema de backbone)
        - Se não conseguir conectar, a operadora pode estar fora do ar
        
        **Inteligência Social (Google Trends)**
        - Rastreia volume de buscas por termos como "Vivo caiu", "Claro sem sinal"
        - Se muita gente está reclamando, é porque tem algo errado de verdade
        - Valores altos mesmo com TCP OK = problema na rede de acesso ao usuário
        
        **Como Classificamos Risco (Por estado)**
        - **🔴 ALTO RISCO** (acima de 60): Falha confirmada em larga escala
        - **🟡 MÉDIO RISCO** (40-60): Usuários relatando problemas, mas não é total
        - **🟢 BAIXO RISCO** (abaixo de 40): Operação normal ou problemas muito localizados
        
        ***Dica:* Se há alertas altos mas o TCP está OK, pode ser problema de 4G/5G, não de backbone.*
        """)
    
    st.markdown('<div class="elegant-divider"></div>', unsafe_allow_html=True)

else:
    st.error("Não foi possível carregar os dados de monitoramento. Verifique:")
    st.info("• Conexão com AWS S3\n• Credenciais de acesso (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)\n• Bucket S3 está preenchido?")