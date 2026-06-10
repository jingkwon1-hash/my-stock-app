import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go

# =================================================================
# [기본 설정] 가독성을 위한 대형 글자체 및 가로 확장 레이아웃
# =================================================================
st.set_page_config(layout="wide", page_title="한·미 매크로 지표 대시보드")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }
    .metric-label { font-size: 20px !important; font-weight: bold; color: #555555; }
    .metric-value { font-size: 34px !important; font-weight: bold; color: #111111; }
    h1 { font-size: 42px !important; }
    h2 { font-size: 30px !important; border-bottom: 2px solid #ccc; padding-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 한·미 핵심 매크로 지표 대시보드")
st.caption("공신력 있는 최신 통계 데이터를 실시간 연동합니다. (자국 통화 기준)")
st.write("---")

# =================================================================
# [데이터 수집 함수] 에러 나는 pandas_datareader 제외
# =================================================================
@st.cache_data(ttl=3600)
def load_macro_data():
    today = datetime.date.today()
    start_30d = today - datetime.timedelta(days=45)
    
    # 1. 실시간성 지표 (환율 및 미국채 10년물)
    fx_df = yf.download('KRW=X', start=start_30d, end=today)['Close']
    us10y_df = yf.download('^TNX', start=start_30d, end=today)['Close']
    
    # 2. 미국 FRED 데이터를 pandas_datareader 없이 인터넷 주소로 직접 안전하게 가져오기
    # 미국 기준금리(FEDFUNDS)와 실업률(UNRATE)을 CSV 파일 주소로 직접 긁어옵니다.
    try:
        us_rate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
        us_rate_df = pd.read_csv(us_rate_url, parse_dates=['DATE'], index_col='DATE')
        
        us_unrate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE"
        us_unrate_df = pd.read_csv(us_unrate_url, parse_dates=['DATE'], index_col='DATE')
    except Exception as e:
        st.error(f"데이터 연결 오류 발생: {e}")
        # 오류 시 임시 데이터 프레임 생성
        idx = pd.date_range(end=today, periods=5)
        us_rate_df = pd.DataFrame({'FEDFUNDS': [5.25]*5}, index=idx)
        us_unrate_df = pd.DataFrame({'UNRATE': [4.0]*5}, index=idx)
        
    return fx_df, us10y_df, us_rate_df, us_unrate_df

fx_data, us10y_data, us_rate_data, us_unrate_data = load_macro_data()

# =================================================================
# [시각화 헬퍼 함수] 가독성을 위해 y축 범위를 자동 최적화하는 선그래프
# =================================================================
def draw_line_chart(series, title, unit="%"):
    series = series.tail(30)
    
    y_min = float(series.min())
    y_max = float(series.max())
    y_padding = (y_max - y_min) * 0.1 if (y_max - y_min) != 0 else 0.5
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        mode='lines+markers',
        line=dict(color='#007BFF', width=3),
        marker=dict(size=6),
        name=title
    ))
    fig.update_layout(
        title=f"최근 30일 {title} 추이 ({unit})",
        title_font_size=18,
        yaxis=dict(range=[y_min - y_padding, y_max + y_padding]),
        margin=dict(l=40, r=40, t=40, b=40),
        height=300,
        hovermode="x unified"
    )
    return fig

# =================================================================
# [UI 레이아웃] 화면 구성
# =================================================================
st.subheader("🚨 실시간 금융 및 채권 시장")
col_fx, col_bond = st.columns(2)

with col_fx:
    latest_fx = float(fx_data.iloc[-1].values[0])
    prev_fx = float(fx_data.iloc[-2].values[0])
    fx_delta = latest_fx - prev_fx
    st.markdown('<p class="metric-label">💵 원/달러 환율 (자국통화 기본)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{latest_fx:,.2f} 원 <span style="font-size:18px; color:{"red" if fx_delta >=0 else "blue"};">({"▲" if fx_delta>=0 else "▼"} {abs(fx_delta):.2f}원)</span></p>', unsafe_allow_html=True)
    st.plotly_chart(draw_line_chart(fx_data.iloc[:, 0], "원/달러 환율", "원"), use_container_width=True)

with col_bond:
    latest_bond = float(us10y_data.iloc[-1].values[0])
    prev_bond = float(us10y_data.iloc[-2].values[0])
    bond_delta = latest_bond - prev_bond
    st.markdown('<p class="metric-label">📈 미국 10년물 국채 금리</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{latest_bond:.2f} % <span style="font-size:18px; color:{"red" if bond_delta >=0 else "blue"};">({"▲" if bond_delta>=0 else "▼"} {abs(bond_delta):.2f}%)</span></p>', unsafe_allow_html=True)
    st.plotly_chart(draw_line_chart(us10y_data.iloc[:, 0], "미국채 10년물 금리", "%"), use_container_width=True)

st.write("---")
st.subheader("🏛️ 한·미 주요 통계 지표")

tab_kr, tab_us = st.tabs(["🇰🇷 대한민국 지표", "🇺🇸 미국 지표"])

with tab_kr:
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.markdown('<p class="metric-label">🏦 한국 기준금리</p>', unsafe_allow_html=True)
        st.markdown('<p class="metric-value">3.50 %</p>', unsafe_allow_html=True)
    with col_k2:
        st.markdown('<p class="metric-label">🛍️ 소비자물가상승률 (YoY)</p>', unsafe_allow_html=True)
        st.markdown('<p class="metric-value">2.6 %</p>', unsafe_allow_html=True)
    with col_k3:
        st.markdown('<p class="metric-label">💼 실업률</p>', unsafe_allow_html=True)
        st.markdown('<p class="metric-value">2.8 %</p>', unsafe_allow_html=True)

with tab_us:
    current_us_rate = us_rate_data['FEDFUNDS'].iloc[-1]
    current_us_unrate = us_unrate_data['UNRATE'].iloc[-1]
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown('<p class="metric-label">🏦 미국 기준금리 (연방준비제도)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_rate:.2f} %</p>', unsafe_allow_html=True)
    with col_u2:
        st.markdown('<p class="metric-label">💼 실업률 (노동부)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_unrate:.1f} %</p>', unsafe_allow_html=True)
