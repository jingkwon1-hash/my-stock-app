import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests

# 📱 스마트폰 화면에 딱 맞도록 레이아웃 설정
st.set_page_config(page_title="나의 주식 대시보드", layout="centered")

st.title("📊 글로벌 투자 대시보드")
st.caption(f"조회 기준: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# -------------------------------------------------------------
# 🛡️ 야후 파이낸스 차단 우회용 변장 도구 (Session) 설정
# -------------------------------------------------------------
@st.cache_resource
def get_safe_session():
    session = requests.Session()
    # 일반 크롬 브라우저인 것처럼 위장하는 헤더 정보입니다.
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

safe_session = get_safe_session()

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
# 1. TOP: 거시경제 지표
# -------------------------------------------------------------
st.subheader("📌 핵심 거시경제 지표")

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]

# 에러가 나더라도 앱이 멈추지 않고 안전하게 작동하게 만듭니다.
try:
    for i, (name, ticker) in enumerate(macro_tickers.items()):
        # [수정] 변장 도구(session)를 들고 안전하게 데이터를 가져옵니다.
        ticker_obj = yf.Ticker(ticker, session=safe_session)
        data = ticker_obj.history(period="30d")
        
        current_val = data['Close'].iloc[-1]
        prev_val = data['Close'].iloc[-2]
        diff = current_val - prev_val
        
        with cols[i]:
            st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{diff:+.2f}")
            
    st.divider()

    # -------------------------------------------------------------
    # 2. MIDDLE: 스마트폰 터치가 가능한 그래프 그리기
    # -------------------------------------------------------------
    st.subheader("📈 최근 30일 트렌드")
    selected_macro = st.selectbox("보고 싶은 지표를 선택하세요", list(macro_tickers.keys()))

    macro_ticker_symbol = macro_tickers[selected_macro]
    ticker_obj = yf.Ticker(macro_ticker_symbol, session=safe_session)
    chart_data = ticker_obj.history(period="30d")[['Close']]
    st.line_chart(chart_data)

    st.divider()

    # -------------------------------------------------------------
    # 3. BOTTOM: 내 관심 종목 현황
    # -------------------------------------------------------------
    st.subheader("🏢 관심 종목 현황")

    stock_summary = []
    for name, ticker in my_stocks.items():
        ticker_obj = yf.Ticker(ticker, session=safe_session)
        today_info = ticker_obj.history(period="2d")
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

    st.table(pd.DataFrame(stock_summary))

except Exception as e:
    st.error("🔄 야후 서버 일시적 지연입니다. 10초 후 새로고침(F5)을 해주세요!")
