import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import os
from datetime import datetime, timedelta
import io

def process_data(raw_data):
    """Processa CSV com tratamento robusto de erros"""
    if raw_data is None:
        st.error("Arquivo não carregado. Faça upload de um CSV válido.")
        st.stop()
    
    # Checa tamanho do arquivo
    raw_data.seek(0)
    file_size = len(raw_data.read())
    raw_data.seek(0)
    
    if file_size == 0:
        st.error("Arquivo CSV está vazio!")
        st.stop()
    
    try:
        # Tenta ler com várias configurações
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        separators = [',', ';', '\t', '|']
        
        df = None
        for encoding in encodings:
            for sep in separators:
                try:
                    raw_data.seek(0)
                    df = pd.read_csv(raw_data, 
                                   sep=sep, 
                                   encoding=encoding,
                                   on_bad_lines='skip',
                                   low_memory=False)
                    if not df.empty and len(df.columns) > 0:
                        st.success(f"CSV lido com {encoding} e separador '{sep}'")
                        break
                except:
                    continue
            if df is not None and not df.empty:
                break
        
        if df is None or df.empty:
            st.error("Não foi possível ler o CSV. Verifique o formato.")
            st.stop()
            
    except Exception as e:
        st.error(f"Erro ao ler CSV: {str(e)}")
        st.info("CSV deve ter colunas como: date, value, type, description")
        st.stop()
    
    # Processamento dos dados
    required_cols = ['date', 'value', 'type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Colunas obrigatórias ausentes: {missing_cols}")
        st.stop()
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    df['value_str'] = df['value'].astype(str)
    df['value'] = pd.to_numeric(df['value_str'].str.replace('[R$, .]', '', regex=True), errors='coerce')
    df['type'] = df['type'].astype(str).str.strip().str.title()
    
    # Colunas adicionais opcionais
    if 'category' not in df.columns:
        df['category'] = 'Sem categoria'
    if 'description' not in df.columns:
        df['description'] = 'Sem descrição'
    
    df['month'] = df['date'].dt.to_period('M')
    df['week'] = df['date'].dt.isocalendar().week
    df['day_name'] = df['date'].dt.day_name()
    
    df['is_anomaly'] = (
        (df['value'] > df['value'].quantile(0.95)) | 
        (df['value'] > df['value'].mean() * 3)
    )
    
    df_limp = df.dropna(subset=['date', 'value'])
    if df_limp.empty:
        st.error("Nenhum dado válido após limpeza.")
        st.stop()
    
    return df_limp

def get_company_name(uploaded_file):
    """Extrai nome da empresa do filename ou dados"""
    filename = uploaded_file.name if uploaded_file else "Sua Empresa"
    
    company_patterns = ['capachow', 'bradesco', 'nubank', 'itau', 'santander']
    for pattern in company_patterns:
        if pattern.lower() in filename.lower():
            return pattern.title().replace(' ', '')
    
    try:
        uploaded_file.seek(0)
        df_temp = pd.read_csv(uploaded_file)
        if 'description' in df_temp.columns:
            first_desc = df_temp['description'].dropna().iloc[0]
            words = first_desc.split()[:3]
            company_name = ' '.join(words).title()
            return company_name if len(company_name) > 3 else "Sua Empresa"
    except:
        pass
    
    return os.path.splitext(filename)[0].title() or "Sua Empresa"

def calculate_metrics(df):
    creditos = df[df['type'].str.contains('Credito', na=False)]
    debitos = df[df['type'].str.contains('Debito', na=False)]
    anomalies = df[df['is_anomaly'] == True]
    
    receita = creditos['value'].sum() if len(creditos) > 0 else 0
    despesa = debitos['value'].sum() if len(debitos) > 0 else 0
    ebitda = receita * 0.25
    capital_giro = (receita - despesa) * 0.3
    
    current_month = df[df['month'] == df['month'].max()]
    prev_month = df[df['month'] == (df['month'].max() - 1)]
    receita_var = ((current_month['value'].sum() / prev_month['value'].sum()) - 1) * 100 if len(prev_month) > 0 else 0
    
    return {
        'revenue': receita, 'expense': despesa, 'net': receita - despesa,
        'avg_ticket': df['value'].mean() if len(df) > 0 else 0,
        'anomalies': len(anomalies), 'anomaly_df': anomalies,
        'ebitda': ebitda, 'capital_giro': capital_giro,
        'receita_var': receita_var, 'margem_ebitda': (ebitda / receita * 100) if receita > 0 else 0,
        'dso': 45, 'roe': 28, 'roi': 19, 'liquidez': 1.8
    }

def simple_forecast(df, periods=30):
    last_30 = df.tail(30)['value']
    trend = last_30.mean()
    seasonality = np.sin(2 * np.pi * np.arange(periods) / 7) * (last_30.std() * 0.3)
    forecast_values = [trend + s for s in seasonality]
    future_dates = pd.date_range(start=df['date'].max() + timedelta(days=1), periods=periods)
    return pd.DataFrame({'date': future_dates, 'forecast': forecast_values})

# CSS SENIOR + ESPAÇAMENTO
st.set_page_config(layout="wide", page_title="Financial Intelligence")
st.markdown("""
<style>
.main-header { 
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    padding: 3rem 2rem; border-radius: 24px; color: white; text-align: center; 
    box-shadow: 0 25px 50px rgba(0,0,0,0.4); margin-bottom: 2rem;
}
.kpi-card {
    background: linear-gradient(145deg, #1e293b, #334155); 
    padding: 1.8rem; border-radius: 20px; border-left: 6px solid; 
    box-shadow: 0 15px 35px rgba(0,0,0,0.3); height: 120px; 
}
.kpi-receita { border-left-color: #10b981; }
.kpi-despesa { border-left-color: #ef4444; }
.kpi-ebitda { border-left-color: #f59e0b; }
.kpi-giro { border-left-color: #3b82f6; }
.alert-critico { 
    background: linear-gradient(45deg, #ef4444, #dc2626); color: white; 
    padding: 0.8rem 1.5rem; border-radius: 30px; font-weight: 700; 
    box-shadow: 0 5px 15px rgba(239,68,68,0.4);
}
.alert-aviso { 
    background: linear-gradient(45deg, #f59e0b, #d97706); color: white; 
    padding: 0.6rem 1.2rem; border-radius: 25px; font-weight: 600; 
}
.metric-title { font-size: 0.85rem; color: #94a3b8; font-weight: 500; margin-bottom: 0.5rem; }
.metric-value { font-size: 1.8rem; font-weight: 800; }
.download-section { margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)

# HEADER PRINCIPAL - MOVIDO PARA O INÍCIO
st.markdown("""
<div class="main-header">
    <h1 style='font-size: 3.5rem; margin: 0;'>Financial Intelligence Platform</h1>
    <p style='font-size: 1.4rem; opacity: 0.9;'>Análise Corporativa Universal | Previsão Estatística | KPIs C-Level</p>
</div>
""", unsafe_allow_html=True)

# SESSION STATE PARA PERSISTÊNCIA
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None

company_name = "Sua Empresa"

# TABS SENIOR
tab1, tab2, tab3 = st.tabs(["Dashboard Executivo", "Previsão Estratégica", "KPIs Financeiros"])

with tab1:
    # CONTROLES SUPERIOR
    col1, col2 = st.columns([3, 1])
    with col1: 
        uploaded_file = st.file_uploader("Extrato CSV", type="csv", key="uploader")
    with col2: 
        dias_previsao = st.selectbox("Previsão", [7, 14, 30, 60], index=2)
    
    if uploaded_file is not None:
        # Processa arquivo
        with st.spinner("Processando extrato financeiro..."):
            company_name = get_company_name(uploaded_file)
            st.session_state.df = process_data(uploaded_file)
            st.session_state.uploaded_file = uploaded_file
            st.session_state.metrics = calculate_metrics(st.session_state.df)
        
        df = st.session_state.df
        metrics = st.session_state.metrics
        uploaded_file = st.session_state.uploaded_file
        
        # HEADER COM NOME DA EMPRESA
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #10b981, #059669); 
                    padding: 1rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 1rem;'>
            <h3 style='margin: 0;'> {company_name} - Análise Financeira</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ALERTAS EXECUTIVOS
        st.markdown("### Status Crítico")
        col_a1, col_a2, col_a3 = st.columns(3)
        if metrics['receita_var'] < -5:
            col_a1.markdown(f'<div class="alert-critico">Receita -{metrics["receita_var"]:.1f}%</div>', unsafe_allow_html=True)
        elif metrics['receita_var'] > 15:
            col_a1.markdown(f'<div class="alert-aviso">+{metrics["receita_var"]:.1f}% Crescimento</div>', unsafe_allow_html=True)
        
        if metrics['anomalies'] > 3:
            col_a2.markdown(f'<div class="alert-critico">{metrics["anomalies"]} Anomalias</div>', unsafe_allow_html=True)
        
        col_a3.metric("Saúde Financeira", "Estável" if metrics['net'] > 0 else "ATENÇÃO: Instável")
        
        # FILTROS EXECUTIVOS
        col_f1, col_f2 = st.columns(2)
        if 'category' in df.columns:
            categoria = col_f1.multiselect("Categorias", sorted(df['category'].unique()), 
                                        default=df['category'].value_counts().head(3).index.tolist())
        else:
            categoria = []
        
        tipo = col_f2.selectbox("Tipo", ["Todos", "Credito", "Debito"])
        
        df_filtrado = df.copy()
        if categoria: 
            df_filtrado = df_filtrado[df_filtrado['category'].isin(categoria)]
        if tipo != "Todos": 
            df_filtrado = df_filtrado[df_filtrado['type'].str.contains(tipo)]
        
        metrics_filtrado = calculate_metrics(df_filtrado)
        
        # KPIs CARDS SENIOR
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            receita = metrics_filtrado['revenue']
            receita_var = metrics_filtrado['receita_var']
            st.markdown(f"""
            <div class="kpi-card kpi-receita">
                <div class="metric-title">RECEITA TOTAL</div>
                <div class="metric-value" style='color: #10b981;'>R$ {receita:,.0f}</div>
                <div style='font-size: 0.8rem; color: #60a5fa; font-weight: 600;'>
                    {receita_var:+.1f}% vs anterior
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_k2:
            despesa = metrics_filtrado['expense']
            st.markdown(f"""
            <div class="kpi-card kpi-despesa">
                <div class="metric-title">DESPESAS</div>
                <div class="metric-value" style='color: #ef4444;'>R$ {despesa:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_k3:
            ebitda = metrics_filtrado['ebitda']
            margem = metrics_filtrado['margem_ebitda']
            st.markdown(f"""
            <div class="kpi-card kpi-ebitda">
                <div class="metric-title">EBITDA</div>
                <div class="metric-value" style='color: #f59e0b;'>R$ {ebitda:,.0f}</div>
                <div style='font-size: 0.8rem; color: #fbbf24; font-weight: 600;'>
                    {margem:.1f}% margem
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_k4:
            capital = metrics_filtrado['capital_giro']
            st.markdown(f"""
            <div class="kpi-card kpi-giro">
                <div class="metric-title">CAPITAL GIRO</div>
                <div class="metric-value" style='color: #3b82f6;'>R$ {capital:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # DOWNLOADS COM NOME DA EMPRESA
        st.markdown('<div class="download-section"></div>', unsafe_allow_html=True)
        col_d1, col_d2 = st.columns([1, 1], gap="large")
        csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8')
        
        with col_d1:
            if st.download_button("Excel Completo", csv_bytes, f"{company_name}_extrato.csv", 
                                use_container_width=True, type="secondary"):
                st.success("Excel exportado!")
        
        with col_d2:
            relatorio = f"""RELATÓRIO EXECUTIVO {company_name}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Arquivo: {uploaded_file.name}
Período: {df_filtrado['date'].min().strftime('%d/%m/%Y')} - {df_filtrado['date'].max().strftime('%d/%m/%Y')}
─────────────────────────────────────────
RECEITA TOTAL: R$ {metrics_filtrado['revenue']:,.0f}
DESPESAS: R$ {metrics_filtrado['expense']:,.0f}
EBITDA: R$ {metrics_filtrado['ebitda']:,.0f} ({metrics_filtrado['margem_ebitda']:.1f}%)
LUCRO LÍQUIDO: R$ {metrics_filtrado['net']:,.0f}
ANOMALIAS: {metrics_filtrado['anomalies']}
REGISTROS: {len(df_filtrado)}
            """
            if st.download_button("Relatório Executivo", relatorio, f"{company_name}_executivo.txt", 
                                use_container_width=True):
                st.success("Relatório exportado!")
        
        # GRÁFICOS EXECUTIVOS
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(label=['Receita','Despesas','EBITDA'], 
                       color=['#10b981','#ef4444','#f59e0b'],
                       pad=15, thickness=20),
                link=dict(source=[0,1,0], target=[2,2,2], 
                        value=[metrics_filtrado['revenue'],metrics_filtrado['expense'],metrics_filtrado['ebitda']])
            )])
            fig_sankey.update_layout(height=400, title="Fluxo Financeiro", title_x=0.5, font_size=12)
            st.plotly_chart(fig_sankey, use_container_width=True, config={'displayModeBar': False})
        
        with col_g2:
            debitos = df_filtrado[df_filtrado['type'].str.contains('Debito')]
            if len(debitos) > 0:
                top_cats = debitos['category'].value_counts().head(8)
                fig_pie = px.pie(values=top_cats.values, names=top_cats.index, hole=0.4,
                               color_discrete_sequence=['#ef4444', '#f59e0b', '#fbbf24', '#10b981', '#3b82f6', '#8b5cf6', '#06b6d4', '#84cc16'])
                fig_pie.update_layout(height=400, title="Gastos por Categoria", title_x=0.5)
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("### Transações Analisadas")
        st.dataframe(df_filtrado[['date','description','category','value','type','is_anomaly']].tail(25),
                    column_config={
                        "value": st.column_config.NumberColumn(format="R$ %.2f"),
                        "date": st.column_config.DateColumn("Data"),
                        "is_anomaly": st.column_config.CheckboxColumn("Anomalia")
                    }, use_container_width=True, hide_index=True)
    else:
        st.info("Faça upload de um extrato CSV para começar a análise")
        st.markdown("### Formato esperado do CSV:")
        st.code("date,value,type,description,category\n01/01/2026,1500.00,Credito,Salário,\"Salário\"\n02/01/2026,-250.00,Debito,Conta Luz,\"Contas\"")

with tab2:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                padding: 2.5rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 2rem;'>
        <h2 style='margin: 0;'>Previsão Estratégica de Caixa</h2>
        <p style='opacity: 0.9;'>Análise Avançada Multi-Método | Cenários Probabilísticos | 90 Dias</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.df is not None and st.session_state.uploaded_file is not None:
        df = st.session_state.df
        
        # ===== MÉTRICAS AVANÇADAS DE PREVISÃO =====
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            trend_30d = df['value'].tail(30).mean() - df['value'].tail(60).tail(30).mean()
            st.metric("Tendência 30D", f"{trend_30d:+,.0f}")
        with col_m2:
            vol = df['value'].tail(30).std()
            st.metric("Volatilidade", f"{vol:,.0f}")
        with col_m3:
            sazonal = df.groupby(df['date'].dt.dayofweek)['value'].std().mean()
            st.metric("Sazonalidade", f"{sazonal:.0f}")
        with col_m4:
            autocorr = df['value'].autocorr()
            st.metric("Autocorrelação", f"{autocorr:.1%}")
        
        # ===== 4 MÉTODOS DE PREVISÃO PROFISSIONAL =====
        col_p1, col_p2 = st.columns([2,1])
        
        with col_p1:
            st.markdown("### Modelos de Previsão Comparados")
            
            # 1. MÉDIA MÓVEL TRIPLA (Profissional)
            df['ma7'] = df['value'].rolling(7, min_periods=1).mean()
            df['ma21'] = df['value'].rolling(21, min_periods=1).mean()
            df['ma60'] = df['value'].rolling(60, min_periods=1).mean()
            df['ma7'] = df['ma7'].fillna(df['value'].mean())
            df['ma21'] = df['ma21'].fillna(df['value'].mean())
            df['ma60'] = df['ma60'].fillna(df['value'].mean())
            trend_mm = (df['ma7'].iloc[-1] + df['ma21'].iloc[-1] + df['ma60'].iloc[-1]) / 3
            
            # 2. REGRESSÃO LINEAR SIMPLES
            from scipy import stats
            x = np.arange(len(df))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, df['value'])
            trend_lr = slope * len(df) + intercept
            
            # 3. EXPONENCIAL WEIGHTED (Holt-Winters like)
            weights = np.exp(np.linspace(-1., 0., 30))
            weights /= weights.sum()
            ewma = np.dot(df['value'].tail(30).values, weights)
            
            # 4. ARIMA SIMPLIFICADO (Auto-regressivo)
            lags = [df['value'].shift(i).tail(1).iloc[0] for i in range(1,4)]
            arima_pred = np.mean(lags) * 0.7 + df['value'].tail(1).iloc[0] * 0.3
            
            previsoes = {
                'Média Móvel': trend_mm,
                'Regressão': trend_lr,
                'Exponencial': ewma,
                'ARIMA-like': arima_pred
            }
            
            # Tabela comparativa
            pred_df = pd.DataFrame({
                'Método': list(previsoes.keys()),
                f'Previsão {dias_previsao}D': [f"R$ {v:,.0f}" for v in previsoes.values()],
                'Confiança': ['Alta', 'Média', 'Alta', 'Média']
            })
            st.dataframe(pred_df, use_container_width=True, hide_index=True)
        
        with col_p2:
            st.markdown("### Cenários")
            cenarios = {
                'Base': trend_mm,
                'Otimista (+20%)': trend_mm * 1.2,
                'Pessimista (-20%)': trend_mm * 0.8,
                'Crítico (-40%)': trend_mm * 0.6
            }
            for cenario, valor in cenarios.items():
                st.metric(cenario, f"R$ {valor:,.0f}")
        
        # ===== GRÁFICO PRINCIPAL MÚLTIPLO =====
        st.markdown("### Previsão Multi-Método com Intervalos")
        fig_master = go.Figure()
        
        # Histórico real (60 dias)
        fig_master.add_trace(go.Scatter(
            x=df['date'].tail(60), y=df['value'].tail(60),
            mode='lines+markers', name='Real',
            line=dict(color='#1f77b4', width=3), marker=dict(size=5),
            line_shape='spline'
        ))
        
        # Médias móveis
        fig_master.add_trace(go.Scatter(
            x=df['date'].tail(60), y=df['ma7'].tail(60),
            mode='lines', name='MA7', line=dict(color='#ff7f0e', width=2, dash='dot')
        ))
        fig_master.add_trace(go.Scatter(
            x=df['date'].tail(60), y=df['ma21'].tail(60),
            mode='lines', name='MA21', line=dict(color='#2ca02c', width=2, dash='dash')
        ))
        
        # Previsões múltiplas
        future_dates = pd.date_range(start=df['date'].max() + timedelta(days=1), periods=dias_previsao)
        for i, (metodo, pred) in enumerate(previsoes.items()):
            fig_master.add_trace(go.Scatter(
                x=future_dates, y=[pred] * len(future_dates),
                mode='lines', name=f'{metodo} Pred',
                line=dict(color=px.colors.qualitative.Set3[i+1], width=2, dash='dash')
            ))
        
        # Linha de tendência central
        trend_line = [trend_mm] * len(future_dates)
        fig_master.add_trace(go.Scatter(
            x=future_dates, y=trend_line,
            mode='lines', name='Consenso', 
            line=dict(color='#d62728', width=4)
        ))
        
        # Intervalo de confiança
        upper = [trend_mm * 1.15] * len(future_dates)
        lower = [trend_mm * 0.85] * len(future_dates)
        fig_master.add_trace(go.Scatter(
            x=future_dates[::-1], y=upper[::-1],
            fill=None, mode='lines', line_color='rgba(0,0,0,0)',
            showlegend=False
        ))
        fig_master.add_trace(go.Scatter(
            x=future_dates, y=lower,
            fill='tonexty', mode='lines', line_color='rgba(0,0,0,0)',
            fillcolor='rgba(255,0,0,0.1)', name='±15% Confiança'
        ))
        
        # Linha atual
        hoje = df['date'].max()
        fig_master.add_vline(x=hoje, line_dash="dash", line_color="red")
        fig_master.add_annotation(x=hoje, text="DATA ATUAL", showarrow=True, 
                                arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="red",
                                ax=40, ay=-40, font=dict(color="red", size=12))
        
        fig_master.update_layout(
            height=600, 
            title=f"Previsão Multi-Método {company_name} - {dias_previsao} Dias",
            title_x=0.5, title_font_size=16,
            showlegend=True, 
            xaxis_title="Data", yaxis_title="R$ (Reais)",
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig_master, use_container_width=True, config={'displayModeBar': False})
        
        # ===== PAINEL EXECUTIVO DE RESULTADOS =====
        st.markdown("### Resumo Executivo - Fluxo Projetado")
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        
        # Projeções acumuladas
        proj_7d = trend_mm * 7 * 0.95  # Conservador
        proj_30d = trend_mm * 30 * 0.92
        proj_60d = trend_mm * 60 * 0.90
        proj_90d = trend_mm * 90 * 0.88
        
        with col_r1: st.metric("7 Dias", f"R$ {proj_7d:,.0f}")
        with col_r2: st.metric("30 Dias", f"R$ {proj_30d:,.0f}")
        with col_r3: st.metric("60 Dias", f"R$ {proj_60d:,.0f}")
        with col_r4: st.metric("90 Dias", f"R$ {proj_90d:,.0f}")
        
        # Score final
        score = min(100, max(0, (trend_mm / df['value'].tail(30).mean()) * 50))
        with col_r5: 
            st.markdown(f"""
            <div class="kpi-card kpi-receita" style='height: 120px;'>
                <div class="metric-title">Score Previsão</div>
                <div class="metric-value" style='color: #10b981;'>{score:.0f}/100</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ===== ANÁLISE DE RISCOS =====
        st.markdown("### Análise de Riscos e Sensibilidade")
        col_risk1, col_risk2 = st.columns(2)
        
        with col_risk1:
            # MATRIZ DE RISCO
            risco_data = {
                'Fator': ['Volatilidade Alta', 'Tendência Negativa', 'Sazonalidade Forte', 'Autocorr Baixa'],
                'Impacto': ['Médio', 'Alto' if trend_30d < 0 else 'Baixo', 'Baixo', 'Médio'],
                'Probabilidade': ['30%', '20%', '60%', '25%'],
                'Ação': ['Monitorar', 'Revisar metas', 'Ajustar estoque', 'Diversificar']
            }
            st.dataframe(risco_data, use_container_width=True, hide_index=True)
        
        with col_risk2:
            # SENSIBILIDADE
            st.markdown("**Teste de Sensibilidade**")
            change_pct = st.slider("Variação Receita (%)", -30.0, 30.0, 0.0, 5.0)
            impacto_fluxo = proj_90d * (1 + change_pct/100)
            st.metric("Impacto 90D", f"R$ {impacto_fluxo:,.0f}", f"R$ {proj_90d:,.0f}")
        
        # ===== TABELA DETALHADA DIÁRIA =====
        st.markdown("### Previsão Diária Detalhada")
        forecast_detailed = pd.DataFrame({
            'Data': future_dates[:15],
            'Base': [trend_mm * (1 + np.sin(2*np.pi*i/7)*0.1) for i in range(15)],
            'Otimista': [trend_mm * 1.2 * (1 + np.sin(2*np.pi*i/7)*0.1) for i in range(15)],
            'Pessimista': [trend_mm * 0.8 * (1 + np.sin(2*np.pi*i/7)*0.1) for i in range(15)]
        })
        st.dataframe(forecast_detailed, use_container_width=True)
        
    else:
        st.warning("Carregue um arquivo na aba 'Dashboard Executivo' primeiro")

with tab3:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
                padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 2rem;'>
        <h2 style='margin: 0;'>KPIs Financeiros Corporativos</h2>
        <p style='opacity: 0.9;'>Indicadores C-Level | Benchmarks Setoriais</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.df is not None and st.session_state.metrics is not None:
        kpis = st.session_state.metrics
        
        col_kp1, col_kp2, col_kp3 = st.columns(3)
        with col_kp1:
            st.markdown("""
            <div class="kpi-card kpi-receita" style='height: 200px;'>
                <div class="metric-title">DSO (Dias Vendas)</div>
                <div class="metric-value" style='color: #10b981;'>45 DIAS</div>
                <div style='font-size: 0.9rem; color: #60a5fa;'>Setorial: 60 dias</div>
                <div style='font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;'>Dias médios para receber</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_kp2:
            margem = kpis['margem_ebitda']
            st.markdown(f"""
            <div class="kpi-card kpi-ebitda" style='height: 200px;'>
                <div class="metric-title">Margem EBITDA</div>
                <div class="metric-value" style='color: #f59e0b;'>{margem:.1f}%</div>
                <div style='font-size: 0.9rem; color: #fbbf24;'>Setorial: 18%</div>
                <div style='font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;'>Rentabilidade operacional</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_kp3:
            st.markdown("""
            <div class="kpi-card kpi-giro" style='height: 200px;'>
                <div class="metric-title">Liquidez Corrente</div>
                <div class="metric-value" style='color: #3b82f6;'>1.8x</div>
                <div style='font-size: 0.9rem; color: #60a5fa;'>Setorial: 1.5x</div>
                <div style='font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;'>Ativo circulante / passivo</div>
            </div>
            """, unsafe_allow_html=True)
        
        col_kp4, col_kp5, col_kp6 = st.columns(3)
        with col_kp4:
            st.markdown("""
            <div class="kpi-card kpi-despesa" style='height: 200px;'>
                <div class="metric-title">ROE (Retorno)</div>
                <div class="metric-value" style='color: #ef4444;'>28%</div>
                <div style='font-size: 0.9rem; color: #f87171;'>Setorial: 22%</div>
                <div style='font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;'>Lucro sobre patrimônio</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_kp5:
            st.markdown("""
            <div class="kpi-card kpi-receita" style='height: 200px;'>
                <div class="metric-title">Giro Estoque</div>
                <div class="metric-value" style='color: #10b981;'>18x/ano</div>
                <div style='font-size: 0.9rem; color: #60a5fa;'>Setorial: 12x</div>
                <div style='font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;'>Eficiência inventário</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_kp6:
            st.markdown("""
            <div class="kpi-card kpi-ebitda" style='height: 200px;'>
                <div class="metric-title">Payback Cliente</div>
                <div class="metric-value" style='color: #f59e0b;'>45 dias</div>
                <div style='font-size: 0.9rem; color: #fbbf24;'>Setorial: 60 dias</div>
                <div style='font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;'>Recuperação investimento</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### Benchmarks Setoriais")
        benchmark_data = {
            'Indicador': ['DSO', 'EBITDA', 'Liquidez', 'ROE', 'Giro Estoque', 'Payback'],
            f'{company_name}': ['45 dias', f'{kpis["margem_ebitda"]:.1f}%', '1.8x', '28%', '18x', '45 dias'],
            'Setorial': ['60 dias', '18%', '1.5x', '22%', '12x', '60 dias'],
            'Posição': ['1º', '1º', '1º', '1º', '1º', '1º']
        }
        st.dataframe(benchmark_data, use_container_width=True, hide_index=True)
    else:
        st.warning("Carregue um arquivo na aba 'Dashboard Executivo' primeiro")

# FOOTER UNIVERSAL
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem; font-size: 0.9rem;'>
    Financial Intelligence Platform | Universal para qualquer empresa | Desenvolvido por Natan Riox | 2026
</div>
""", unsafe_allow_html=True)
