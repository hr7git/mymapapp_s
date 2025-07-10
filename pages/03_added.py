import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="시총 Top 10 기업 및 올웨더 포트폴리오 현황",
    page_icon="📈",
    layout="wide"
)

# 시총 Top 10 기업 (2024년 기준) - 최신 순위에 따라 조정 필요
TOP_10_COMPANIES = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Alphabet": "GOOGL", # Alphabet Class A
    "Amazon": "AMZN",
    "NVIDIA": "NVDA",
    "Meta": "META",
    "Berkshire Hathaway": "BRK-B",
    "Taiwan Semiconductor": "TSM",
    "Tesla": "TSLA", # Tesla는 시총 변동이 크지만 여전히 중요
    "Broadcom": "AVGO" # Visa 대신 Broadcom 등 최신 상위 기업으로 변경 고려
}

# 레이 달리오 올웨더 포트폴리오 자산군 (대표 ETF 티커)
# 실제 포트폴리오 비율과 일치하지 않으며, 개별 자산군 성능 시각화 목적
ALL_WEATHER_ASSETS = {
    "S&P 500 (주식)": "SPY",      # 주식
    "장기 국채 (20년+)": "TLT", # 장기 채권
    "중기 국채 (7-10년)": "IEF", # 중기 채권
    "금": "GLD",                 # 금
    "원자재": "DBC"               # 원자재 (상품)
}

# 주요 경제 위기 기간 정의
# Plotly의 x축 타입이 'date'일 경우 datetime 객체를 사용
# 이름: [시작 날짜, 종료 날짜, 설명]
CRISIS_PERIODS = {
    "코로나19 팬데믹 쇼크": [datetime(2020, 2, 19), datetime(2020, 4, 1), "코로나19 팬데믹으로 인한 급락"],
    "2022년 인플레이션/금리 인상": [datetime(2022, 1, 1), datetime(2022, 12, 31), "인플레이션 및 금리 인상으로 인한 시장 하락"],
    "실리콘밸리 은행 파산": [datetime(2023, 3, 8), datetime(2023, 3, 20), "SVB 파산으로 인한 금융시장 불안"]
    # 필요한 경우 더 많은 기간 추가
    # 예: "글로벌 금융 위기": [datetime(2007, 12, 1), datetime(2009, 6, 30), "서브프라임 모기지 사태"]
}


@st.cache_data
def get_stock_data(ticker, period="3y"):
    """주식 데이터를 가져오는 함수"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        st.error(f"'{ticker}' 데이터를 가져오는 중 오류 발생: {e}")
        return None

@st.cache_data
def get_company_info(ticker):
    """회사 정보를 가져오는 함수"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'marketCap': info.get('marketCap', 0),
            'currentPrice': info.get('currentPrice', 0)
        }
    except Exception as e:
        # st.warning(f"'{ticker}' 정보를 가져오는 중 오류 발생: {e}") # 디버깅용
        return {'name': 'N/A', 'sector': 'N/A', 'marketCap': 0, 'currentPrice': 0}

def format_market_cap(market_cap):
    """시가총액을 읽기 쉬운 형태로 변환"""
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.2f}T"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.2f}B"
    elif market_cap >= 1e6:
        return f"${market_cap/1e6:.2f}M"
    else:
        return f"${market_cap:,.0f}"

def add_crisis_regions(fig, start_date, end_date):
    """경제 위기 구간을 차트에 배경색으로 추가하는 함수"""
    for name, dates in CRISIS_PERIODS.items():
        crisis_start = dates[0]
        crisis_end = dates[1]
        description = dates[2]

        # 차트의 현재 기간과 겹치는지 확인
        if not (crisis_end < start_date or crisis_start > end_date):
            fig.add_vrect(
                x0=crisis_start,
                x1=crisis_end,
                fillcolor="rgba(255, 0, 0, 0.1)",  # 빨간색 계열의 투명한 배경
                layer="below",
                line_width=0,
                annotation_text=name, # 주석 텍스트 추가
                annotation_position="top left", # 주석 위치
                annotation_font_size=10,
                annotation_font_color="red"
            )


def main():
    st.title("📈 글로벌 시총 Top 기업 및 레이 달리오 올웨더 자산 현황")
    st.markdown("최근 **3년**간의 주가/자산 가격 데이터를 확인해보세요.")

    # 사이드바에서 섹션 선택
    section = st.sidebar.radio(
        "어떤 데이터를 보시겠습니까?",
        ["글로벌 Top 기업 주가", "레이 달리오 올웨더 자산"]
    )

    # -----------------------------------------------------------
    # 글로벌 Top 기업 주가 섹션
    # -----------------------------------------------------------
    if section == "글로벌 Top 기업 주가":
        st.header("🏢 글로벌 시총 Top 기업 주가 현황")
        st.markdown("전 세계 시가총액 상위 기업들의 주가 데이터를 제공합니다.")

        # 사이드바에서 기업 선택
        st.sidebar.header("기업 선택")
        selected_companies = st.sidebar.multiselect(
            "분석할 기업을 선택하세요:",
            options=list(TOP_10_COMPANIES.keys()),
            default=list(TOP_10_COMPANIES.keys())[:3]  # 기본으로 3개 선택
        )

        if not selected_companies:
            st.warning("최소 하나의 기업을 선택해주세요.")
            return

        # 기간 선택
        period_options = {
            "1년": "1y",
            "2년": "2y",
            "3년": "3y",
            "5년": "5y"
        }

        selected_period_name = st.sidebar.selectbox(
            "기간 선택:",
            options=list(period_options.keys()),
            index=2  # 기본값: 3년
        )
        selected_period_value = period_options[selected_period_name]

        # 차트 타입 선택
        chart_type = st.sidebar.radio(
            "차트 타입:",
            ["라인 차트", "캔들스틱 차트"],
            key="company_chart_type"
        )

        # 데이터 로딩
        with st.spinner("기업 데이터를 불러오는 중..."):
            stock_data = {}
            company_info = {}

            # 현재 날짜로부터 선택된 기간 만큼의 시작 날짜 계산 (add_crisis_regions 함수에 전달하기 위함)
            end_date = datetime.now()
            if selected_period_value == "1y":
                plot_start_date = end_date - timedelta(days=365)
            elif selected_period_value == "2y":
                plot_start_date = end_date - timedelta(days=2 * 365)
            elif selected_period_value == "3y":
                plot_start_date = end_date - timedelta(days=3 * 365)
            elif selected_period_value == "5y":
                plot_start_date = end_date - timedelta(days=5 * 365)
            else: # Fallback to 3 years
                plot_start_date = end_date - timedelta(days=3 * 365)


            for company in selected_companies:
                ticker = TOP_10_COMPANIES[company]
                data = get_stock_data(ticker, selected_period_value)
                info = get_company_info(ticker)

                if data is not None and not data.empty:
                    stock_data[company] = data
                    company_info[company] = info
                else:
                    st.warning(f"선택한 '{company}'의 데이터를 불러올 수 없습니다.")

        if not stock_data:
            st.error("선택한 기업의 데이터를 불러올 수 없습니다. 티커 목록을 확인하거나, 인터넷 연결을 확인해 주세요.")
            return

        # 회사 정보 표시
        st.subheader("📊 선택된 기업 정보")

        cols = st.columns(len(selected_companies))
        for i, company in enumerate(selected_companies):
            if company in company_info:
                info = company_info[company]
                with cols[i]:
                    st.metric(
                        label=f"{company}",
                        value=f"${info['currentPrice']:.2f}",
                        delta=f"시총: {format_market_cap(info['marketCap'])}"
                    )
                    st.caption(f"섹터: {info['sector']}")

        # 주가 차트
        st.subheader("📈 주가 차트")

        if chart_type == "라인 차트":
            fig = go.Figure()
            colors = px.colors.qualitative.Set1 # Plotly Express의 색상 팔레트 사용

            for i, (company, data) in enumerate(stock_data.items()):
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    name=company,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f'<b>{company}</b><br>' +
                                  '날짜: %{x}<br>' +
                                  '종가: $%{y:.2f}<br>' +
                                  '<extra></extra>'
                ))

            # 경제 위기 구간 추가
            add_crisis_regions(fig, plot_start_date, end_date)

            fig.update_layout(
                title=f"선택 기업 주가 추이 - {selected_period_name}",
                xaxis_title="날짜",
                yaxis_title="주가 (USD)",
                hovermode='x unified',
                height=600,
                template='plotly_white',
                xaxis_rangeslider_visible=True
            )

        else: # 캔들스틱 차트
            if len(selected_companies) > 1:
                st.info("캔들스틱 차트는 한 번에 하나의 기업만 표시됩니다. 첫 번째 선택된 기업의 차트를 표시합니다.")
            company = selected_companies[0]
            data = stock_data[company]

            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=company
            )])

            # 경제 위기 구간 추가 (캔들스틱 차트에도 적용)
            add_crisis_regions(fig, plot_start_date, end_date)

            fig.update_layout(
                title=f"{company} 캔들스틱 차트 - {selected_period_name}",
                xaxis_title="날짜",
                yaxis_title="주가 (USD)",
                height=600,
                template='plotly_white',
                xaxis_rangeslider_visible=True
            )

        st.plotly_chart(fig, use_container_width=True)

        # 성과 비교 테이블
        st.subheader("📊 성과 비교")
        performance_data = []
        for company, data in stock_data.items():
            if len(data) > 0:
                start_price = data['Close'].iloc[0]
                end_price = data['Close'].iloc[-1]
                total_return = ((end_price - start_price) / start_price) * 100

                max_price = data['Close'].max()
                min_price = data['Close'].min()
                std_dev = data['Close'].std()

                performance_data.append({
                    '기업': company,
                    '시작 가격': f"${start_price:.2f}",
                    '현재 가격': f"${end_price:.2f}",
                    '총 수익률': f"{total_return:.2f}%",
                    '최고가': f"${max_price:.2f}",
                    '최저가': f"${min_price:.2f}",
                    '변동성 (표준편차)': f"{std_dev:.2f}"
                })

        if performance_data:
            df_performance = pd.DataFrame(performance_data)
            st.dataframe(df_performance, use_container_width=True)

        # 거래량 차트
        st.subheader("📊 거래량 분석")
        fig_volume = go.Figure()
        colors = px.colors.qualitative.Set1 # Plotly Express의 색상 팔레트 사용

        for i, (company, data) in enumerate(stock_data.items()):
            fig_volume.add_trace(go.Scatter(
                x=data.index,
                y=data['Volume'],
                mode='lines',
                name=company,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'<b>{company}</b><br>' +
                              '날짜: %{x}<br>' +
                              '거래량: %{y:,.0f}<br>' +
                              '<extra></extra>'
            ))

        # 경제 위기 구간 추가 (거래량 차트에도 적용)
        add_crisis_regions(fig_volume, plot_start_date, end_date)

        fig_volume.update_layout(
            title=f"거래량 추이 - {selected_period_name}",
            xaxis_title="날짜",
            yaxis_title="거래량",
            hovermode='x unified',
            height=400,
            template='plotly_white',
            xaxis_rangeslider_visible=True
        )
        st.plotly_chart(fig_volume, use_container_width=True)

    # -----------------------------------------------------------
    # 레이 달리오 올웨더 포트폴리오 섹션
    # -----------------------------------------------------------
    elif section == "레이 달리오 올웨더 자산":
        st.header("🌧️ 레이 달리오 올웨더 포트폴리오 핵심 자산 분석")
        st.markdown("레이 달리오의 올웨더 포트폴리오를 구성하는 주요 자산군들의 가격 동향을 확인합니다.")
        st.info("⚠️ **참고:** 이 섹션은 실제 올웨더 포트폴리오의 비율이나 투자 전략을 구현한 것이 아니라, **주요 자산군들의 개별적인 가격 동향을 시각화**하여 이해를 돕기 위함입니다.")

        # 기간 선택 (올웨더 자산용)
        aw_period_options = {
            "1년": "1y",
            "3년": "3y",
            "5년": "5y",
            "10년": "10y"
        }
        selected_aw_period_name = st.sidebar.selectbox(
            "기간 선택 (올웨더 자산):",
            options=list(aw_period_options.keys()),
            index=1, # 기본값: 3년
            key="aw_period_selector"
        )
        selected_aw_period_value = aw_period_options[selected_aw_period_name]

        # 현재 날짜로부터 선택된 기간 만큼의 시작 날짜 계산 (add_crisis_regions 함수에 전달하기 위함)
        end_date_aw = datetime.now()
        if selected_aw_period_value == "1y":
            plot_start_date_aw = end_date_aw - timedelta(days=365)
        elif selected_aw_period_value == "3y":
            plot_start_date_aw = end_date_aw - timedelta(days=3 * 365)
        elif selected_aw_period_value == "5y":
            plot_start_date_aw = end_date_aw - timedelta(days=5 * 365)
        elif selected_aw_period_value == "10y":
            plot_start_date_aw = end_date_aw - timedelta(days=10 * 365)
        else: # Fallback to 3 years
            plot_start_date_aw = end_date_aw - timedelta(days=3 * 365)


        with st.spinner("올웨더 자산 데이터를 불러오는 중..."):
            aw_data = {}
            for asset_name, ticker in ALL_WEATHER_ASSETS.items():
                data = get_stock_data(ticker, selected_aw_period_value)
                if data is not None and not data.empty:
                    # 수익률 비교를 위해 시작 가격 기준으로 정규화
                    # 기준 시점 가격으로 나누어 100을 곱하여 백분율로 시작점을 통일
                    initial_price = data['Close'].iloc[0]
                    data['Normalized Close'] = (data['Close'] / initial_price) * 100
                    aw_data[asset_name] = data
                else:
                    st.warning(f"'{asset_name}' ({ticker}) 의 데이터를 불러올 수 없습니다.")

        if not aw_data:
            st.error("선택한 올웨더 자산의 데이터를 불러올 수 없습니다. 티커 목록을 확인하거나, 인터넷 연결을 확인해 주세요.")
            return

        st.subheader("📈 올웨더 자산군별 정규화된 가격 추이 (시작 시점 = 100)")
        st.markdown("각 자산군의 시작 시점 가격을 100으로 기준으로 설정하여, 상대적인 성과를 비교합니다.")

        fig_aw = go.Figure()
        colors_aw = px.colors.qualitative.Plotly # 다른 색상 팔레트 사용

        for i, (asset_name, data) in enumerate(aw_data.items()):
            fig_aw.add_trace(go.Scatter(
                x=data.index,
                y=data['Normalized Close'],
                mode='lines',
                name=asset_name,
                line=dict(color=colors_aw[i % len(colors_aw)], width=2),
                hovertemplate=f'<b>{asset_name}</b><br>' +
                              '날짜: %{x}<br>' +
                              '정규화된 가격: %{y:.2f}<br>' +
                              '<extra></extra>'
            ))

        # 경제 위기 구간 추가 (올웨더 자산 차트에도 적용)
        add_crisis_regions(fig_aw, plot_start_date_aw, end_date_aw)


        fig_aw.update_layout(
            title=f"올웨더 포트폴리오 자산군 성과 - {selected_aw_period_name}",
            xaxis_title="날짜",
            yaxis_title="정규화된 가격 (시작 시점 100)",
            hovermode='x unified',
            height=600,
            template='plotly_white',
            xaxis_rangeslider_visible=True,
            legend_title_text="자산군"
        )
        st.plotly_chart(fig_aw, use_container_width=True)

        # 올웨더 자산 성과 테이블
        st.subheader("📊 올웨더 자산군 성과 비교")
        aw_performance_data = []
        for asset_name, data in aw_data.items():
            if len(data) > 0:
                initial_normalized_price = data['Normalized Close'].iloc[0]
                current_normalized_price = data['Normalized Close'].iloc[-1]
                total_return = current_normalized_price - initial_normalized_price # 100에서 시작했으므로
                
                initial_actual_price = data['Close'].iloc[0]
                current_actual_price = data['Close'].iloc[-1]

                aw_performance_data.append({
                    '자산군': asset_name,
                    '시작 가격': f"${initial_actual_price:.2f}",
                    '현재 가격': f"${current_actual_price:.2f}",
                    '정규화된 시작': f"{initial_normalized_price:.2f}",
                    '정규화된 현재': f"{current_normalized_price:.2f}",
                    '총 수익률': f"{total_return:.2f}%"
                })

        if aw_performance_data:
            df_aw_performance = pd.DataFrame(aw_performance_data)
            st.dataframe(df_aw_performance, use_container_width=True)


    # 공통 정보
    st.markdown("---")
    st.header("ℹ️ 추가 정보")
    st.info("""
    **데이터 소스**: Yahoo Finance
    
    **주의사항**:
    - 이 데이터는 투자 조언이 아닙니다.
    - 실제 투자 전에 전문가와 상담하세요.
    - 과거 성과가 미래 성과를 보장하지 않습니다.
    - 시가총액 Top 10 기업 목록은 실시간으로 변동됩니다.
    - 레이 달리오 올웨더 포트폴리오 섹션은 포트폴리오를 구성하는 개별 자산군들의 가격 동향을 보여주는 것으로, 실제 포트폴리오의 복잡한 리밸런싱 및 자산 배분 전략을 반영하지 않습니다.
    - **경제 위기 기간은 일반적인 시장 상황을 기준으로 예시적으로 표시된 것이며, 모든 경제적 충격을 포함하지 않습니다.**
    """)

if __name__ == "__main__":
    main()
