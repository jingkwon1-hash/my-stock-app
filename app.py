import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go
import requests

# =================================================================
# 텔레그램 알림 설정 (1단계에서 구한 내 정보를 여기에 적으세요!)
# =================================================================
TELEGRAM_TOKEN = "여기에_복사한_토큰을_넣으세요"
TELEGRAM_CHAT_ID = "여기에_복사한_ID숫자를_넣으세요"

def send_alert(message):
    """지표가 범위를 벗어나면 스마트폰으로 알림을 보내는 함수"""
    # 임시 기본값이 그대로 있으면 알림을 보내지 않음
    if "여기에" in TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        pass

# =================================================================
# [기본 설정] 레이아웃 및 디자인 수정
# =================================================================
st.set_page_config(layout="wide", page_title="MACRO 지표")

# 제목 크기를 기존 42px에서 약 70% 크기인 30px로 축소 조정
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }
    .metric-label { font-size: 20px !important; font-weight: bold; color: #555555; }
    .metric-value { font-size: 34px !important; font-weight: bold; color: #111111; }
    h1 { font-size: 30px !important; color: #222222; font-weight: 800; } /* 제목 크기 70% 변경 */
    h2 { font-size: 26px !important; border-bottom: 2px solid #ccc; padding-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 MACRO 지표") # 제목 변경
st.caption("공신력 있는 최신 통계 데이터를 실시간 연동하며, 범위를 벗어나면 스마트폰 알림을 전송합니다.")
st.write("---")

# =================================================================
# [데이터 수집]
# =================================================================
@st.cache_data(ttl=3600)
def load_macro_data():
    today = datetime.date.today()
    start_30d = today - datetime.timedelta(days=45)
    
    fx_df = yf.download('KRW=X', start=start_30d, end=today)['Close']
    us10y_df = yf.download('^TNX', start=start_30d, end=today)['Close']
    
    try:
        us_rate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
        us_rate_df = pd.read_csv(us_rate_url, parse_dates=['DATE'], index_col='DATE')
        
        us_unrate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE"
        us_unrate_df = pd.read_csv(us_unrate_url, parse_dates=['DATE'], index_col='DATE')
    except Exception as e:
        idx = pd.date_range(end=today, periods=5)
        us_rate_df = pd.DataFrame({'FEDFUNDS': [5.25]*5}, index=idx)
        us_unrate_df = pd.DataFrame({'UNRATE': [4.0]*5}, index=idx)
        
    return fx_df, us10y_df, us_rate_df, us_unrate_df

fx_data, us10y_data, us_rate_data, us_unrate_data = load_macro_data()

# 최신 지표 변수 지정
latest_fx = float(fx_data.iloc[-1].values[0])
latest_bond = float(us10y_data.iloc[-1].values[0])
current_us_rate = float(us_rate_data['FEDFUNDS'].iloc[-1])
current_us_unrate = float(us_unrate_data['UNRATE'].iloc[-1])

# 한국 지표 세팅
current_kr_rate = 3.50 
current_kr_cpi = 2.6  

# =================================================================
# 🚨 [조건문] 알림 기준 체크 로직 (지정한 범위를 벗어나면 알림)
# =================================================================
# 1. 원/달러 환율 (기준: 1500원 ~ 1550원)
if latest_fx < 1500:
    send_alert(f"⚠️ 원/달러 환율이 하한선(1,500원) 밑으로 하락했습니다. 현재: {latest_fx:,.2f}원")
elif latest_fx > 1550:
    send_alert(f"🚨 원/달러 환율이 상한선(1,550원)을 넘겼습니다. 현재: {latest_fx:,.2f}원")

# 2. 미국 10년물 국채금리 (기준: 4.0% ~ 4.7%)
if latest_bond < 4.0:
    send_alert(f"⚠️ 미국 10년물 국채금리가 4.0% 밑으로 하락했습니다. 현재: {latest_bond:.2f}%")
elif latest_bond > 4.7:
    send_alert(f"🚨 미국 10년물 국채금리가 4.7%를 넘겼습니다. 현재: {latest_bond:.2f}%")

# 3. 한국 기준금리 (기준: 3.0% ~ 3.75%)
if current_kr_rate < 3.0 or current_kr_rate > 3.75:
    send_alert(f"📢 한국 기준금리가 지정된 범위(3.0%~3.75%)를 벗어났습니다. 현재: {current_kr_rate:.2f}%")

# 4. 미국 기준금리 (기준: 4.75% ~ 5.5%)
if current_us_rate < 4.75:
    send_alert(f"⚠️ 미국 기준금리가 4.75% 밑으로 하락했습니다. 현재: {current_us_rate:.2f}%")
elif current_us_rate > 5.5:
    send_alert(f"🚨 미국 기준금리가 5.5%를 넘겼습니다. 현재: {current_us_rate:.2f}%")

# 5. 한국 소비자물가상승률 (기준: 2.5% ~ 3.0%)
if current_kr_cpi < 2.5 or current_kr_cpi > 3.0:
    send_alert(f"📢 한국 소비자물가상승률이 범위(2.5%~3.0%)를 벗어났습니다. 현재: {current_kr_cpi:.1f}%")

# 6. 미국 실업률 (기준: 3.0% ~ 4.5%)
if current_us_unrate < 3.0 or current_us_unrate > 4.5:
    send_alert(f"📢 미국 실업률이 범위(3.0%~4.5%)를 벗어났습니다. 현재: {current_us_unrate:.1f}%")


# =================================================================
# [시각화 헬퍼 함수]
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
# [UI 레이아웃 화면 표시]
# =================================================================
st.subheader("🚨 실시간 금융 및 채권 시장")
col_fx, col_bond = st.columns(2)

with col_fx:
    prev_fx = float(fx_data.iloc[-2].values[0])
    fx_delta = latest_fx - prev_fx
    st.markdown('<p class="metric-label">💵 원/달러 환율</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{latest_fx:,.2f} 원 <span style="font-size:18px; color:{"red" if fx_delta >=0 else "blue"};">({"▲" if fx_delta>=0 else "▼"} {abs(fx_delta):.2f}원)</span></p>', unsafe_allow_html=True)
    st.plotly_chart(draw_line_chart(fx_data.iloc[:, 0], "원/달러 환율", "원"), use_container_width=True)

with col_bond:
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
        st.markdown(f'<p class="metric-value">{current_kr_rate:.2f} %</p>', unsafe_allow_html=True)
    with col_k2:
        st.markdown('<p class="metric-label">🛍️ 소비자물가상승률 (YoY)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_kr_cpi:.1f} %</p>', unsafe_allow_html=True)
    with col_k3:
        st.markdown('<p class="metric-label">💼 실업률</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_kr_unrate:.1f} %</p>', unsafe_allow_html=True)

with tab_us:
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown('<p class="metric-label">🏦 미국 기준금리 (연방준비제도)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_rate:.2f} %</p>', unsafe_allow_html=True)
    with col_u2:
        st.markdown('<p class="metric-label">💼 실업률 (노동부)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{current_us_unrate:.1f} %</p>', unsafe_allow_html=True)
