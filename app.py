import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pytz
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuração da Página
st.set_page_config(layout="wide", page_title="Dashboard de Vendas v5.0")

# 2. Função de Carregamento com CACHE (TTL de 10 minutos)
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # URL da sua planilha (Certifique-se de que é o link correto do seu Google Sheets)
    url = "https://docs.google.com/spreadsheets/d/1KeeAFVOjg59JhODe4maqMEyQiyyXa8xSsxSuKTN1wB8/edit?usp=sharing"
    
    df_vendas = conn.read(spreadsheet=url, worksheet="Lançamento Diário")
    df_metas = conn.read(spreadsheet=url, worksheet="Metas")

    # Limpeza de nomes de colunas
    df_vendas.columns = [c.strip() for c in df_vendas.columns]
    df_metas.columns = [c.strip() for c in df_metas.columns]

    # Conversão de tipos para evitar erros nos KPIs
    df_vendas['Data'] = pd.to_datetime(df_vendas['Data'])
    df_vendas['Faturamento Bruto'] = pd.to_numeric(df_vendas['Faturamento Bruto'], errors='coerce').fillna(0)
    df_vendas['N° de Clientes'] = pd.to_numeric(df_vendas['N° de Clientes'], errors='coerce').fillna(0)
    df_metas['Valor da Meta'] = pd.to_numeric(df_metas['Valor da Meta'], errors='coerce').fillna(0)

    # Mapa para cruzar meses texto (metas) com número (vendas)
    mes_map = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
               'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
    df_metas['Mes_Num'] = df_metas['Mês'].str.lower().str.strip().map(mes_map)
    
    return df_vendas, df_metas, datetime.now(pytz.timezone('America/Sao_Paulo'))

try:
    # Carrega os dados
    vendas, metas, hora_atualizacao = load_data()

    # --- CABEÇALHO ---
    col_titulo, col_status = st.columns([3, 1])
    with col_titulo:
        st.title("📊 Painel de Vendas Executivo")
    with col_status:
        st.caption("✨ Dados atualizados em:")
        st.write(f"**{hora_atualizacao.strftime('%d/%m/%Y %H:%M:%S')}**")

    st.markdown("---")

    # --- FILTROS NA BARRA LATERAL ---
    st.sidebar.header("Filtros")
    anos = sorted(vendas['Ano'].unique(), reverse=True)
    ano_sel = st.sidebar.selectbox("Selecione o Ano", anos)

    mes_nomes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 
                 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    
    meses_disp = sorted(vendas[vendas['Ano'] == ano_sel]['Mês'].unique())
    mes_sel = st.sidebar.selectbox("Selecione o Mês", meses_disp, format_func=lambda x: mes_nomes[x])

    # --- FILTRAGEM E CÁLCULOS ---
    df_f = vendas[(vendas['Ano'] == ano_sel) & (vendas['Mês'] == mes_sel)]
    valor_meta = metas[(metas['Ano'] == ano_sel) & (metas['Mes_Num'] == mes_sel)]['Valor da Meta'].sum()

    faturamento = df_f['Faturamento Bruto'].sum()
    clientes = df_f['N° de Clientes'].sum()
    ticket = faturamento / clientes if clientes > 0 else 0
    progresso = (faturamento / valor_meta * 100) if valor_meta > 0 else 0

    # --- EXIBIÇÃO DOS KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
    
    # Alerta visual: se o progresso for baixo, a cor pode ajudar a destacar
    c2.metric("% Meta Atingida", f"{progresso:.1f}%", delta=f"{progresso-100:.1f}%")
    
    c3.metric("Ticket Médio", f"R$ {ticket:.2f}")
    c4.metric("Nº de Clientes", f"{clientes:,.0f}")

    st.markdown("###")

    # --- GRÁFICOS ---
    g1, g2 = st.columns([2, 1])

    with g1:
        st.subheader("Evolução Diária")
        # Gráfico de área para faturamento diário
        fig = px.area(df_f[df_f['Faturamento Bruto'] > 0].sort_values('Data'), 
                       x='Data', y='Faturamento Bruto', template="plotly_white",
                       color_discrete_sequence=['#0047AB'])
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("Atingimento da Meta")
        if valor_meta > 0:
            fig_p = go.Figure(go.Pie(labels=['Atingido', 'Pendente'], 
                values=[min(faturamento, valor_meta), max(0, valor_meta - faturamento)], hole=.7,
                marker_colors=['#27ae60', '#f1f1f1']))
            fig_p.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
            fig_p.add_annotation(text=f"{progresso:.1f}%", showarrow=False, font_size=25)
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.warning("Meta não cadastrada.")

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")

