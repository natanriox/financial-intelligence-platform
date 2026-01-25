# Financial Intelligence Platform 

![Dashboard Preview](https://via.placeholder.com/1200x600/0f172a/ffffff?text=Financial+Intelligence+Platform)

**Análise Financeira Corporativa Universal** - Dashboard C-Level para qualquer empresa brasileira

## **Funcionalidades Profissionais**

- **Dashboard Executivo** - KPIs em tempo real (Receita, EBITDA, Capital de Giro)
- **Previsão Estratégica** - 4 métodos avançados (Média Móvel, Regressão, Exponencial, ARIMA)
- **Alertas Inteligentes** - Anomalias e variações críticas
- **Visualizações Interativas** - Sankey, Pizza, Previsões Multi-método
- **Exportação Profissional** - Relatórios executivos automáticos

## **Demo Online**
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/seuusuario/financial-intelligence)

## **Como Usar**

1. **Faça upload do seu extrato CSV** (Bradesco, Nubank, Itaú, etc.)
2. **Formato mínimo**: `date,value,type,description,category`
3. **Exemplo**:

date,value,type,description,category
01/01/2026,1500.00,Credito,Salário,Salário
02/01/2026,-250.00,Debito,Conta Luz,Contas


## **KPIs Executivos Incluídos**

| Indicador | Benchmark |
|-----------|-----------|
| DSO (45 dias) | Setorial: 60 dias |
| Margem EBITDA | Setorial: 18% |
| Liquidez Corrente (1.8x) | Setorial: 1.5x |

## **Tech Stack**

Streamlit - Pandas - Plotly - SciPy - Análise Estatística Avançada


## **Deploy Fácil**
- [Streamlit Cloud](https://streamlit.io/cloud) (Grátis)
- [Hugging Face Spaces](https://huggingface.co/spaces)
- [Railway](https://railway.app)

**Desenvolvido por Natan Riox | Jan/2026**

4. Crie dados de exemplo (sample_data/extrato_exemplo.csv)

date,value,type,description,category
01/01/2026,2500.00,Credito,Salário Base,Salário
02/01/2026,-180.50,Debito,Conta de Luz,Contas Fixas
03/01/2026,450.00,Credito,Venda Cliente A,Vendas
05/01/2026,-75.00,Debito,Netflix,Assinaturas
10/01/2026,3200.00,Credito,Salário Variável,Salário

5. .gitignore

__pycache__/
*.pyc
.env
.DS_Store
.coverage
htmlcov/
.streamlit/secrets.toml
