import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Dashboard de Vendas")

@st.cache_data
def load_data():
    arquivo = 'Vendas.xlsx'
    df_vendas = pd.read_excel(arquivo, sheet_name='Lançamento Diário')
    df_metas = pd.read_excel(arquivo, sheet_name='Metas')

    # Tratamento de dados baseado nas colunas reais
    df_vendas['Data'] = pd.to_datetime(df_vendas['Data'])
    df_vendas['Faturamento Bruto'] = pd.to_numeric(df_vendas['Faturamento Bruto'], errors='coerce').fillna(0)
    df_vendas['N° de Clientes'] = pd.to_numeric(df_vendas['N° de Clientes'], errors='coerce').fillna(0)
    df_metas['Valor da Meta'] = pd.to_numeric(df_metas['Valor da Meta'], errors='coerce').fillna(0)

    # Mapa para cruzar meses texto (metas) com número (vendas)
    mes_map = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
               'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
    df_metas['Mes_Num'] = df_metas['Mês'].str.lower().str.strip().map(mes_map)
    
    return df_vendas, df_metas

try:
    vendas, metas = load_data()

    # Barra Lateral
    st.sidebar.header("Filtros")
    anos = sorted(vendas['Ano'].unique(), reverse=True)
    ano_sel = st.sidebar.selectbox("Ano", anos)

    mes_nomes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 
                 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    
    meses_disp = sorted(vendas[vendas['Ano'] == ano_sel]['Mês'].unique())
    mes_sel = st.sidebar.selectbox("Mês", meses_disp, format_func=lambda x: mes_nomes[x])

    # Filtragem e Cálculos
    df_f = vendas[(vendas['Ano'] == ano_sel) & (vendas['Mês'] == mes_sel)]
    valor_meta = metas[(metas['Ano'] == ano_sel) & (metas['Mes_Num'] == mes_sel)]['Valor da Meta'].sum()

    faturamento = df_f['Faturamento Bruto'].sum()
    clientes = df_f['N° de Clientes'].sum()
    ticket = faturamento / clientes if clientes > 0 else 0
    progresso = (faturamento / valor_meta * 100) if valor_meta > 0 else 0

    # Layout do Dashboard
    st.title("📊 Dashboard de Vendas")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
    c2.metric("% Meta Atingida", f"{progresso:.1f}%")
    c3.metric("Ticket Médio", f"R$ {ticket:.2f}")
    c4.metric("Nº de Clientes", f"{clientes:,.0f}")

    st.markdown("###")
    g1, g2 = st.columns([2, 1])

    with g1:
        st.subheader("Evolução Diária")
        fig = px.area(df_f[df_f['Faturamento Bruto'] > 0], x='Data', y='Faturamento Bruto', template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("Acompanhamento da Meta")
        if valor_meta > 0:
            fig_p = go.Figure(go.Pie(labels=['Atingido', 'Falta'], 
                values=[min(faturamento, valor_meta), max(0, valor_meta - faturamento)], hole=.7,
                marker_colors=['#27ae60', '#f1f1f1']))
            fig_p.update_layout(showlegend=False, height=350)
            fig_p.add_annotation(text=f"{progresso:.1f}%", showarrow=False, font_size=25)
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.warning("Meta não cadastrada para este mês.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")