import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 📱 스마트폰 화면에 딱 맞도록 레이아웃 설정
st.set_page_config(page_title="나의 주식 대시보드", layout="centered")

st.title("📊 글로벌 투자 대시보드")
st.caption(f"조회 기준: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# -------------------------------------------------------------
# [데이터 수집] 거시경제 및 개별 종목
# -------------------------------------------------------------
macro_tickers = {
    "원/달러 환율 💵": "KRW=X",
    "미국채 10년물 금리(%) 📈": "^TNX",
    "필라델피아 반도체지수 💻": "^SOX"
}

my_stocks = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "애플(Apple)": "AAPL"
}

# -------------------------------------------------------------
# 1. TOP: 거시경제 지표 (스마트폰에서 보기 편하게 카드 형태로 배치)
# -------------------------------------------------------------
st.subheader("📌 핵심 거시경제 지표")

# 화면을 3개의 구역으로 나눕니다
col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]

for i, (name, ticker) in enumerate(macro_tickers.items()):
    data = yf.Ticker(ticker).history(period="30d")
    current_val = data['Close'].iloc[-1]
    prev_val = data['Close'].iloc[-2]
    diff = current_val - prev_val
    
    # 각 구역에 숫자 카드를 배치합니다
    with cols[i]:
        st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{diff:+.2f}")

st.divider()

# -------------------------------------------------------------
# 2. MIDDLE: 스마트폰 터치가 가능한 그래프 그리기
# -------------------------------------------------------------
st.subheader("📈 최근 30일 트렌드")
selected_macro = st.selectbox("보고 싶은 지표를 선택하세요", list(macro_tickers.keys()))

# 사용자가 선택한 지표의 30일 치 데이터를 가져와 그래프로 그립니다
macro_ticker_symbol = macro_tickers[selected_macro]
chart_data = yf.Ticker(macro_ticker_symbol).history(period="30d")[['Close']]
st.line_chart(chart_data)

st.divider()

# -------------------------------------------------------------
# 3. BOTTOM: 내 관심 종목 현황
# -------------------------------------------------------------
st.subheader("🏢 관심 종목 현황")

stock_summary = []
for name, ticker in my_stocks.items():
    today_info = yf.Ticker(ticker).history(period="2d")
    if len(today_info) >= 2:
        current_price = today_info['Close'].iloc[-1]
        prev_price = today_info['Close'].iloc[-2]
        change_percent = ((current_price - prev_price) / prev_price) * 100
    else:
        current_price = today_info['Close'].iloc[-1] if not today_info.empty else 0
        change_percent = 0
        
    stock_summary.append({
        "종목명": name,
        "현재가": f"{current_price:,.2f}",
        "전일대비": f"{change_percent:+.2f}%"
    })

# 표 형태로 예쁘게 출력
st.table(pd.DataFrame(stock_summary))
