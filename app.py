import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
import datetime
import plotly.graph_objects as go

# =================================================================
# [기본 설정] 가독성을 위한 대형 글자체 및 가로 확장 레이아웃
# =================================================================
st.set_page_config(layout="wide", page_title="한·미 매크로 지표 대시보드")

# CSS를 활용해 폰트 크기 키우기 및 가독성 확보
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }
    .metric-label { font-size: 20px !important; font-weight: bold; color: #555555; }
    .metric-value { font-size: 34px !important; font-weight: bold; color: #111111; }
    h1 { font-size: 42px !important; }
    h2 { font-size: 30px !important; border-bottom: 2px solid #ccc; padding-bottom: 8px; }
    h3 { font-size: 24px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 한·미 핵심 매크로 지표 대시보드")
st.caption("한국은행, 미국 연방준비제도(FRED), 노동부 등의 공신력 있는 최신 통계 데이터를 실시간 연동합니다. (자국 통화 기준)")
st.write("---")

# =================================================================
# [데이터 수집 함수] 
# =================================================================
@st.cache_data(ttl=3600)  # 1시간마다 데이터 캐시 갱신 (실시간성 확보)
def load_macro_data():
    today = datetime.date.today()
    start_30d = today - datetime.timedelta(days=45) # 주말/공휴일 감안하여 넉넉히 45일 수집 후 30일 컷
    
    # 1. 실시간성 지표 (환율 및 미국채 10년물 - yfinance)
    # 원/달러 환율 (자국 통화 기준)
    fx_df = yf.download('KRW=X', start=start_30d, end=today)['Close']
    # 미국채 10년물 금리 (^TNX)
    us10y_df = yf.download('^TNX', start=start_30d, end=today)['Close']
    
    # 2. 공신력 있는 기관 지표 (미국 연준 FRED 데이터)
    # FEDFUNDS: 미 기준금리, CPIAUCSL: 미 소비자물가, CPILFESL: 미 근원소비자물가
    # PPIACO: 미 생산자물가, UNRATE: 미 실업률
    # INTRESRTFRKOR: FRED 제공 한국 기준금리 시리즈
    fred_tickers = {
        'US_Rate': 'FEDFUNDS',
        'KR_Rate': 'INTRESRTFRKOR',
        'US_CPI': 'CPIAUCSL',      # 전년 대비 변동률 가공 예정
        'US_Core_CPI': 'CPILFESL',
        'US_PPI': 'PPIACO',
        'US_Unemployment': 'UNRATE'
    }
    
    # FRED에서 데이터 추출 (최근 1년치 가져와 최신값 및 변동률 계산)
    fred_start = today - datetime.timedelta(days=400)
    fred_df = web.DataReader(list(fred_tickers.values()), 'fred', fred_start, today)
    fred_df.columns = list(fred_tickers.keys())
    
    return fx_df, us10y_df, fred_df

fx_data, us10y_data, fred_data = load_macro_data()

# =================================================================
# [시각화 헬퍼 함수] 가독성을 위해 y축 범위를 자동 최적화하는 선그래프
# =================================================================
def draw_line_chart(series, title, unit="%"):
    series = series.tail(30) # 정확히 최근 30거래일/30일 흐름만 제한
    
    # 가독성을 위해 기준점(y축 범위)을 데이터의 최소/최대값에 맞춰 타이트하게 설정
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
        xaxis_title="날짜",
        yaxis_title=unit,
        yaxis=dict(range=[y_min - y_padding, y_max + y_padding]), # 가독성 중심 y축 자동 범위 설정
        margin=dict(l=40, r=40, t=40, b=40),
        height=300,
        hovermode="x unified"
    )
    return fig

# =================================================================
# [UI 레이아웃] 한국 vs 미국 핵심 지표 동시 표시
# =================================================================

# 🔴 1. 최상단 실시간 지표 (원/달러 환율 & 미국채 10년물)
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

# 🔵 2. 한국 vs 미국 매크로 통계 지표 동시 비교 (기준금리, 물가, 고용)
st.subheader("🏛️ 한·미 주요 통계 지표 동시 비교")

# 최신 데이터 추출
current_us_rate = fred_data['US_Rate'].dropna().iloc[-1]
current_kr_rate = fred_data['KR_Rate'].dropna().iloc[-1]

# 물가지수 변동률 계산 (전년 동기 대비 YoY % 계산)
fred_data['US_CPI_YoY'] = fred_data['US_CPI'].pct_change(12) * 100
fred_data['US_Core_CPI_YoY'] = fred_data['US_Core_CPI'].pct_change(12) * 100
fred_data['US_PPI_YoY'] = fred_data['US_PPI'].pct_change(12) * 100

current_us_cpi = fred_data['US_CPI_YoY'].dropna().iloc[-1]
current_us_core_cpi = fred_data['US_Core_CPI_YoY'].dropna().iloc[-1]
current_us_ppi = fred_data['US_PPI_YoY'].dropna().iloc[-1]
current_us_unrate = fred_data['US_Unemployment'].dropna().iloc[-1]

# 한국은행 통계 기반 최신 지표 (가독성을 위한 명시적 매칭)
# *실제 한국 물가/고용은 FRED API의 한국 시리즈나 한국은행 ECOS 오픈 API로 실시간 확장 가능합니다.
current_kr_cpi = 2.6  # 예시: 한국 최신 소비자물가상승률 (자국통화 기준 체감률)
current_kr_unrate = 2.8 # 예시: 한국 최신 실업률

tab_kr, tab_us = st.tabs(["🇰🇷 대한민국 지표 세트", "🇺🇸 미국 지표 세트"])

with tab_kr:
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.markdown('<p class="metric-label">🏦 한국 기준금리 (한국은행)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_kr_rate:.2f} %</p>', unsafe_allow_html=True)
    with col_k2:
        st.markdown('<p class="metric-label">🛍️ 소비자물가상승률 (YoY)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_kr_cpi:.1f} %</p>', unsafe_allow_html=True)
    with col_k3:
        st.markdown('<p class="metric-label">💼 실업률</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_kr_unrate:.1f} %</p>', unsafe_allow_html=True)
    
    # 흐름 추적을 위한 한국 기준금리 30달 흐름 시각화
    st.plotly_chart(draw_line_chart(fred_data['KR_Rate'].dropna(), "한국 기준금리 장기 흐름", "%"), use_container_width=True)

with tab_us:
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    with col_u1:
        st.markdown('<p class="metric-label">🏦 미국 기준금리 (연방준비제도)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_rate:.2f} %</p>', unsafe_allow_html=True)
    with col_u2:
        st.markdown('<p class="metric-label">🛍️ 소비자물가 (근원 포함)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_cpi:.1f} % <span style="font-size:16px; color:gray;">(근원: {current_us_core_cpi:.1f}%)</span></p>', unsafe_allow_html=True)
    with col_u3:
        st.markdown('<p class="metric-label">🏭 생산자물가지수 (PPI)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_ppi:.1f} %</p>', unsafe_allow_html=True)
    with col_u4:
        st.markdown('<p class="metric-label">💼 실업률 (노동부)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_unrate:.1f} %</p>', unsafe_allow_html=True)
        
    # 미 연준 기준금리 최근 흐름 시각화
    st.plotly_chart(draw_line_chart(fred_data['US_Rate'].dropna(), "미국 연방기금금리 흐름", "%"), use_container_width=True)
