import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests

# 📱 스마트폰 맞춤형 레이아웃 설정
st.set_page_config(page_title="나의 프리미엄 대시보드", layout="centered")

st.title("🦅 프리미엄 투자 대시보드")
st.caption(f"조회 기준: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# -------------------------------------------------------------
# 🛡️ 야후 파이낸스 차단 우회용 세션 설정
# -------------------------------------------------------------
@st.cache_resource
def get_safe_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

safe_session = get_safe_session()

# -------------------------------------------------------------
# [설정] 지표 및 20개 요청 종목 딕셔너리 정렬
# -------------------------------------------------------------
macro_tickers = {
    "원/달러 환율 💵": "KRW=X",
    "미국채 10년물 금리(%) 📈": "^TNX",
    "필라델피아 반도체지수 💻": "^SOX",
    "국제유가(WTI) 🛢️": "CL=F"
}

my_stocks = {
    "SK하이닉스": "000660.KS",
    "삼성전자": "005930.KS",
    "삼성생명": "032830.KS",
    "삼성SDI": "006400.KS",
    "삼성SDS": "018260.KS",
    "포스코홀딩스": "005490.KS",
    "현대모비스": "012330.KS",
    "현대차": "005380.KS",
    "현대로템": "064350.KS",
    "디앤디파마텍": "472220.KQ",
    "대한광통신": "010170.KS",
    "KODEX 200 (ETF)": "069500.KS",
    "TIGER 미국우주테크 (ETF)": "483480.KS", # 야후 데이터 연동 체크용
    "구글(Alphabet)": "GOOGL",
    "아마존(Amazon)": "AMZN",
    "엔비디아(Nvidia)": "NVDA",
    "마이크로소프트(MS)": "MSFT",
    "마벨 테크놀로지": "MRVL",
    "테슬라(Tesla)": "TSLA",
    "마이크론": "MU"
}

# -------------------------------------------------------------
# 스마트폰 화면 공간 활용을 위한 3개의 탭(Tab) 구성
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🌍 거시경제 지표", "📊 종목 분석실", "📰 실시간 뉴스/실적"])

# =============================================================
# 탭 1: 거시경제 지표
# =============================================================
with tab1:
    st.subheader("📌 실시간 글로벌 매크로 지표")
    
    # 2x2 격자로 예쁘게 배치하기 위해 화면 나눔
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    cols = [col1, col2, col3, col4]
    
    try:
        macro_keys = list(macro_tickers.keys())
        for i, name in enumerate(macro_keys):
            ticker = macro_tickers[name]
            ticker_obj = yf.Ticker(ticker, session=safe_session)
            data = ticker_obj.history(period="30d")
            
            current_val = data['Close'].iloc[-1]
            prev_val = data['Close'].iloc[-2]
            diff = current_val - prev_val
            
            with cols[i]:
                st.metric(label=name, value=f"{current_val:,.2f}", delta=f"{diff:+.2f}")
                
        st.divider()
        st.subheader("📈 30일 트렌드 차트")
        selected_macro = st.selectbox("추세를 확인할 지표 선택", macro_keys)
        m_ticker = macro_tickers[selected_macro]
        chart_data = yf.Ticker(m_ticker, session=safe_session).history(period="30d")[['Close']]
        st.line_chart(chart_data)
        
    except Exception as e:
        st.error("지표를 가져오는 중 일시적인 지연이 발생했습니다. 잠시 후 새로고침 해주세요.")

# =============================================================
# 탭 2: 종목 분석실 (가격 범위 및 PER/PBR/ROE)
# =============================================================
with tab2:
    st.subheader("🏢 20개 종목 핵심 스냅샷")
    st.caption("30일 최고/최저가 및 투자 지표 (PER/PBR/ROE)")
    
    stock_data_list = []
    
    with st.spinner('20개 종목의 대용량 데이터를 분석 중입니다... 약 10초 소요됩니다.'):
        for name, ticker in my_stocks.items():
            try:
                ticker_obj = yf.Ticker(ticker, session=safe_session)
                
                # 가격 데이터 (최근 30일)
                hist_30d = ticker_obj.history(period="30d")
                if not hist_30d.empty:
                    current_p = hist_30d['Close'].iloc[-1]
                    high_30d = hist_30d['High'].max()
                    low_30d = hist_30d['Low'].min()
                    
                    # 전일 대비 등락률 계산
                    hist_2d = hist_30d.tail(2)
                    if len(hist_2d) == 2:
                        change_p = ((hist_2d['Close'].iloc[-1] - hist_2d['Close'].iloc[-2]) / hist_2d['Close'].iloc[-2]) * 100
                    else:
                        change_p = 0.0
                else:
                    current_p, high_30d, low_30d, change_p = 0, 0, 0, 0
                
                # 기업 기본 재무 정보 (PER, PBR, ROE) 안전하게 추출
                info = ticker_obj.info
                per = info.get('trailingPE', None)
                pbr = info.get('priceToBook', None)
                roe = info.get('returnOnEquity', None)
                
                # ROE는 소수점으로 들어오므로 %로 변환
                roe_val = f"{roe * 100:.1f}%" if roe is not None else "-"
                per_val = f"{per:.1f}" if per is not None else "-"
                pbr_val = f"{pbr:.1f}" if pbr is not None else "-"
                
                stock_data_list.append({
                    "종목명": name,
                    "현재가": f"{current_p:,.0f}" if ".KS" in ticker or ".KQ" in ticker else f"${current_p:,.2f}",
                    "전일대비": f"{change_p:+.2f}%",
                    "30일 최고가": f"{high_30d:,.0f}" if ".KS" in ticker or ".KQ" in ticker else f"${high_30d:,.2f}",
                    "30일 최저가": f"{low_30d:,.0f}" if ".KS" in ticker or ".KQ" in ticker else f"${low_30d:,.2f}",
                    "PER": per_val,
                    "PBR": pbr_val,
                    "ROE": roe_val
                })
            except Exception as e:
                # 데이터 수집 오류 시 빈 값 처리
                stock_data_list.append({
                    "종목명": name, "현재가": "N/A", "전일대비": "-", "30일 최고가": "-", "30일 최저가": "-", "PER": "-", "PBR": "-", "ROE": "-"
                })
                
    df_stocks = pd.DataFrame(stock_data_list)
    # 모바일 환경에서 좌우 스크롤로 편하게 볼 수 있는 대화형 테이블 출력
    st.dataframe(df_stocks, use_container_width=True)

# =============================================================
# 탭 3: 기업별 실시간 뉴스 및 실적 가이드
# =============================================================
with tab3:
    st.subheader("📰 개별 기업 이슈 및 실적 브리핑")
    selected_stock = st.selectbox("상세 정보를 확인할 기업을 선택하세요", list(my_stocks.keys()))
    
    selected_ticker = my_stocks[selected_stock]
    ticker_obj = yf.Ticker(selected_ticker, session=safe_session)
    
    # 1. 뉴스 데이터 가져오기
    st.markdown(f"#### ⚡ {selected_stock} 최근 주요 뉴스")
    try:
        news_list = ticker_obj.news
        if news_list:
            for item in news_list[:5]: # 최신 뉴스 5개만 표출
                title = item.get('title', '제목 없음')
                publisher = item.get('publisher', '알 수 없음')
                link = item.get('link', '#')
                st.markdown(f"- [{title}]({link}) (*{publisher}*)")
        else:
            st.info("현재 제공되는 실시간 뉴스가 없습니다.")
    except:
        st.warning("뉴스 데이터를 가져오지 못했습니다.")
        
    st.divider()
    
    # 2. 실적 및 예상실적 정보 가이드
    st.markdown(f"#### 📈 {selected_stock} 실적 및 밸류에이션 정보 요약")
    try:
        info = ticker_obj.info
        
        # 가용한 실적 요약 지표 매핑
        market_cap = info.get('marketCap', 0)
        forward_pe = info.get('forwardPE', '-')
        eps = info.get('trailingEps', '-')
        forward_eps = info.get('forwardEps', '-')
        revenue_growth = info.get('revenueGrowth', None)
        
        rev_growth_val = f"{revenue_growth * 100:+.1f}%" if revenue_growth is not None else "-"
        
        perf_df = pd.DataFrame({
            "실적 항목": ["시가 총액", "최근 주당순이익(EPS)", "미래 예상 EPS (Forward EPS)", "예상 PER (Forward PER)", "최근 매출 성장률"],
            "수치 및 가이드": [
                f"{market_cap:,.0f}" if market_cap else "-",
                f"{eps}" if eps != '-' else "-",
                f"{forward_eps}" if forward_eps != '-' else "-",
                f"{forward_pe}" if forward_pe != '-' else "-",
                rev_growth_val
            ]
        })
        st.table(perf_df)
        st.caption("※ 미국 주식은 디테일한 예상 EPS가 제공되며, 국내 주식은 데이터 제공 범위에 따라 일부 항목이 '-'로 표시될 수 있습니다.")
    except Exception as e:
        st.error("실적 요약 데이터를 불러오는 중 오류가 발생했습니다.")
