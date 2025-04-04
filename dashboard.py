import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from db import fetch_summary_data

def summary_dashboard():
    rows = fetch_summary_data()
    if not rows:
        st.info("📭 아직 입력된 비용 데이터가 없습니다.")
        return

    df = pd.DataFrame(rows, columns=["현장명", "월", "기성금", "노무비", "투입비"])

    # 결측값 및 음수 방지 처리
    df = df.fillna(0)
    df["기성금"] = df["기성금"].clip(lower=0)
    df["노무비"] = df["노무비"].clip(lower=0)
    df["투입비"] = df["투입비"].clip(lower=1)  # 0으로 나눗셈 방지

    df["손수익"] = df["기성금"] - df["투입비"]
    df["노무비비중"] = df["노무비"] / df["투입비"]

    st.markdown("### 📊 현장별 비용 리포트")
    st.dataframe(df, use_container_width=True)

    sites = df["현장명"].unique()
    if len(sites) == 0:
        st.warning("⚠️ 선택할 수 있는 현장 데이터가 없습니다.")
        return

    selected_site = st.selectbox("📍 리포트 확인할 현장 선택", sites)
    df_site = df[df["현장명"] == selected_site]

    if df_site.empty:
        st.warning("📭 선택된 현장에 대한 데이터가 없습니다.")
        return

    with st.expander("📌 요약 수치 보기", expanded=True):
        latest = df_site.sort_values("월").iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("기성금", f"{latest['기성금']:,}원")
        col2.metric("투입비", f"{latest['투입비']:,}원")
        col3.metric("손수익", f"{latest['손수익']:,}원")

    st.subheader("📈 월별 비용 추이")
    fig1, ax1 = plt.subplots()
    df_site.plot(x="월", y=["기성금", "투입비", "노무비"], kind="bar", ax=ax1)
    ax1.set_ylabel("금액")
    ax1.set_title("기성금 / 투입비 / 노무비")
    st.pyplot(fig1)

    st.subheader("📊 손수익 및 노무비 비중")
    fig2, ax2 = plt.subplots()
    df_site.plot(x="월", y=["손수익"], kind="line", marker="o", ax=ax2)
    ax2.set_ylabel("손수익")

    ax3 = ax2.twinx()
    df_site.plot(x="월", y=["노무비비중"], kind="line", marker="s", color="orange", ax=ax3)
    ax3.set_ylabel("노무비 비중")

    st.pyplot(fig2)
