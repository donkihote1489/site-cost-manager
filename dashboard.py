# dashboard.py - 모든 그래프 y축 단위 자동화 적용 (천원, 백만 원, 억원)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc, ticker
from db import fetch_summary_data

font_path = "C:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc("font", family=font_name)


def format_unit(value):
    if value >= 1_0000_0000:
        return value / 1_0000_0000, "억원", 1_0000_0000
    elif value >= 1_000_000:
        return value / 1_000_000, "백만 원", 1_000_000
    else:
        return value / 1_000, "천원", 1_000

def summary_dashboard():
    rows = fetch_summary_data()
    if not rows:
        st.info("📭 아직 입력된 비용 데이터가 없습니다.")
        return

    df = pd.DataFrame(rows, columns=["현장명", "월", "기성금", "노무비", "투입비"])
    df = df.fillna(0)
    df["투입비"] = df["투입비"].replace(0, 1)
    df["순수익"] = df["기성금"] - df["투입비"]
    df["순수익비중"] = df["순수익"] / df["기성금"] * 100
    df["노무비비중"] = df["노무비"] / df["투입비"]

    st.markdown("### 📊 현장별 비용 리포트")
    st.dataframe(df, use_container_width=True)

    sites = df["현장명"].unique().tolist()
    if not sites:
        st.warning("선택할 수 있는 현장 데이터가 없습니다.")
        return

    selected_site = st.selectbox("📍 리포트 확인할 현장 선택", sites, key="dashboard_site")
    df_site = df[df["현장명"] == selected_site]

    if df_site.empty:
        st.warning("선택된 현장에 대한 데이터가 없습니다.")
        return

    with st.expander("📌 요약 수치 보기", expanded=True):
        latest = df_site.sort_values("월").iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("기성금", f"{latest['기성금']:,}원")
        col2.metric("투입비", f"{latest['투입비']:,}원")
        col3.metric("순수익", f"{latest['순수익']:,}원")

    st.subheader("📈 월별 비용 추이")
    fig1, ax1 = plt.subplots(figsize=(6, 2))
    max1 = df_site[["기성금", "투입비", "노무비"]].values.max()
    _, unit_label1, unit_div1 = format_unit(max1)
    df_plot1 = df_site.copy()
    df_plot1[["기성금", "투입비", "노무비"]] /= unit_div1

    df_plot1.set_index("월")[["기성금", "투입비", "노무비"]].plot(kind="bar", ax=ax1)
    ax1.set_ylabel(f"금액 ({unit_label1})")
    ax1.set_title("기성금 / 투입비 / 노무비", fontsize=12)
    ax1.legend(title="비용항목", labels=["기성금", "투입비", "노무비"], fontsize=9, title_fontsize=10)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax1.yaxis.grid(True, linestyle="--", alpha=0.3)
    st.pyplot(fig1)

    st.subheader("📈 월별 누계 그래프")
    df_cumsum = df_site.sort_values("월").copy()
    df_cumsum[["기성금", "투입비", "노무비"]] = df_cumsum[["기성금", "투입비", "노무비"]].cumsum()

    last = df_cumsum.iloc[-1]
    rate1 = last["투입비"] / last["기성금"] * 100 if last["기성금"] != 0 else 0
    rate2 = last["노무비"] / last["투입비"] * 100 if last["투입비"] != 0 else 0

    fig2, ax2 = plt.subplots(figsize=(6, 2))
    max2 = df_cumsum[["기성금", "투입비", "노무비"]].values.max()
    _, unit_label2, unit_div2 = format_unit(max2)
    df_plot2 = df_cumsum.copy()
    df_plot2[["기성금", "투입비", "노무비"]] /= unit_div2

    df_plot2.plot(x="월", y=["기성금", "투입비", "노무비"], kind="line", marker="o", ax=ax2)
    ax2.set_title("기성금 / 투입비 / 노무비 누계")
    ax2.set_ylabel(f"금액 ({unit_label2})")
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax2.legend(title="누계 항목")
    ax2.yaxis.grid(True, linestyle="--", alpha=0.3)

    ax2.text(x=len(df_cumsum)-1.1, y=df_plot2["투입비"].iloc[-1], s=f"투입비/기성금: {rate1:.1f}%", fontsize=8, color="black")
    ax2.text(x=len(df_cumsum)-1.1, y=df_plot2["노무비"].iloc[-1], s=f"노무비/투입비: {rate2:.1f}%", fontsize=8, color="black")
    st.pyplot(fig2)

    st.subheader("📈 월별 순수익 그래프")
    df_site = df_site.sort_values("월").copy()
    max_val = df_site["순수익"].max()
    _, unit_label3, unit_div3 = format_unit(max_val)

    fig3, ax3 = plt.subplots(figsize=(6, 2))
    df_site["순수익_단위"] = df_site["순수익"] / unit_div3
    df_site.plot(x="월", y="순수익_단위", kind="line", marker="s", color="purple", ax=ax3, label="순수익")
    ax3.set_ylabel(f"순수익 ({unit_label3})")
    ax3.set_title("월별 순수익")
    ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax3.yaxis.grid(True, linestyle="--", alpha=0.3)

    for i, row in df_site.iterrows():
        x = row["월"]
        y = row["순수익_단위"]
        비중 = row["순수익비중"]
        ax3.text(i, y, f"{비중:.1f}%", fontsize=8, color="black", ha="center", va="bottom")

    st.pyplot(fig3)
