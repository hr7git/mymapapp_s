# (중략) 기존 import 구문들 그대로 유지

# 사계절 포트폴리오 구성
ALL_WEATHER_ETFS = {
    "미국 장기 국채 (TLT)": "TLT",
    "미국 주식 (VTI)": "VTI",
    "중기 국채 (IEF)": "IEF",
    "금 (GLD)": "GLD",
    "원자재 (DBC)": "DBC"
}

# (중략) main() 함수 내부

    # --- 사계절 포트폴리오 보기 옵션 ---
    st.sidebar.header("추가 분석")
    show_all_weather = st.sidebar.checkbox("사계절 포트폴리오 보기")

    if show_all_weather:
        st.header("🌦️ 레이 달리오의 사계절 포트폴리오 (All Weather Portfolio)")

        with st.spinner("ETF 데이터를 불러오는 중..."):
            aw_data = {}
            for label, ticker in ALL_WEATHER_ETFS.items():
                df = get_stock_data(ticker, period_options[selected_period])
                if df is not None and not df.empty:
                    aw_data[label] = df

        if aw_data:
            # 성과 테이블
            performance_data = []
            for label, data in aw_data.items():
                start_price = data['Close'].iloc[0]
                end_price = data['Close'].iloc[-1]
                total_return = ((end_price - start_price) / start_price) * 100
                volatility = data['Close'].std()

                performance_data.append({
                    '자산': label,
                    '시작 가격': f"${start_price:.2f}",
                    '현재 가격': f"${end_price:.2f}",
                    '총 수익률': f"{total_return:.2f}%",
                    '변동성': f"{volatility:.2f}"
                })

            df_aw = pd.DataFrame(performance_data)
            st.subheader("📊 사계절 포트폴리오 성과")
            st.dataframe(df_aw, use_container_width=True)

            # 라인 차트
            fig_aw = go.Figure()
            colors_aw = px.colors.qualitative.Pastel[:len(aw_data)]

            for i, (label, data) in enumerate(aw_data.items()):
                fig_aw.add_trace(go.Scatter(
                    x=data.index,
                    y=data["Close"],
                    name=label,
                    mode="lines",
                    line=dict(color=colors_aw[i], width=2),
                    hovertemplate=f"<b>{label}</b><br>Date: %{x}<br>Price: $%{{y:.2f}}<extra></extra>"
                ))

            fig_aw.update_layout(
                title=f"사계절 포트폴리오 구성 ETF 주가 추이 - {selected_period}",
                xaxis_title="날짜",
                yaxis_title="가격 (USD)",
                hovermode="x unified",
                height=500,
                template="plotly_white"
            )
            st.plotly_chart(fig_aw, use_container_width=True)
        else:
            st.warning("ETF 데이터를 불러오는 데 실패했습니다.")
