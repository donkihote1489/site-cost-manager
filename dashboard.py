import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib import ticker, font_manager, rcParams
from db import get_connection
from db import fetch_summary_data

# ✅ NanumGothicLight.ttf 폰트 로딩 (Streamlit Cloud 호환 방식)
font_path = os.path.join(os.path.dirname(__file__), "assets", "NanumGothicLight.ttf")

if os.path.exists(font_path):
    try:
        font_manager.fontManager.addfont(font_path)
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        rcParams["font.family"] = font_name
        st.write(f"✅ 한글 폰트 적용됨: {font_name}")
    except Exception as e:
        st.warning(f"⚠️ 폰트 적용 중 오류 발생: {e}")
else:
    st.warning("⚠️ 한글 폰트 파일을 찾을 수 없습니다. 기본 폰트를 사용합니다.")


# 한글 폰트 설정

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

    df = pd.DataFrame(rows, columns=["현장명", "연도","월", "기성금", "노무비", "투입비"])
    df = df.fillna(0)
    df["투입비"] = df["투입비"].replace(0, 1)
    df["순수익"] = df["기성금"] - df["투입비"]
    df["손익율"] = df["순수익"] / df["기성금"] * 100
    df["노무비율"] = df["노무비"] / df["투입비"] * 100

    st.markdown("### 📊 현장별 비용 리포트")
    df_formatted = df.copy()
    for col in ["기성금", "투입비", "노무비", "순수익"]:
         df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x):,}")
    df_formatted["손익율"] = df["손익율"].apply(lambda x: f"{x:.2f}%")
    df_formatted["노무비율"] = df["노무비율"].apply(lambda x: f"{x:.2f}%")
    df_formatted = df_formatted.rename(columns={"순수익": "현장손익(기성금-투입비)"})

    st.dataframe(df_formatted, use_container_width=True)


    # 삭제 기능 추가
    delete_targets = df[["현장명", "월"]].drop_duplicates()
    selected = st.selectbox("🗑️ 삭제할 (현장 + 월) 데이터 선택", delete_targets.apply(lambda r: f"{r['현장명']} - {r['월']}", axis=1))
    if st.button("선택한 데이터 삭제"):
        site, month = selected.split(" - ")
        with get_connection() as conn:
            conn.execute("DELETE FROM 절차상태 WHERE 현장명=? AND 월=?", (site, month))
            conn.commit()
        st.success(f"✅ {selected} 삭제 완료!")
        st.rerun()

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
        total_기성금 = df_site["기성금"].sum()
        total_투입비 = df_site["투입비"].sum()
        total_노무비 = df_site["노무비"].sum()
        total_손익 = total_기성금 - total_투입비
        비율 = (total_투입비 / total_기성금 * 100) if total_기성금 != 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("기성금 누계", f"{int(total_기성금):,}원")
        col2.metric("투입비 누계", f"{int(total_투입비):,}원", f"{비율:.1f}%")
        col3.metric("노무비 누계", f"{int(total_노무비):,}원")
        col4.metric("현장손익 누계", f"{int(total_손익):,}원")

    # 월별 비용 추이
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
    ax1.set_xticklabels(df_plot1["월"], rotation=0)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax1.yaxis.grid(True, linestyle="--", alpha=0.3)
    st.pyplot(fig1)

    # 월별 누계 그래프
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

    # 월별 손익율 그래프
    st.subheader("📈 월별 손익율 그래프")
    df_site = df_site.sort_values("월").copy()
    max_val = df_site["순수익"].max()
    _, unit_label3, unit_div3 = format_unit(max_val)

    fig3, ax3 = plt.subplots(figsize=(6, 2))
    df_site["손익율"] = df_site["순수익"] / df_site["기성금"] * 100
    df_site.plot(x="월", y="손익율", kind="line", marker="s", color="purple", ax=ax3, label="손익율")
    ax3.set_ylabel("손익율 (%)")
    ax3.set_title("월별 손익율")
    ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
    ax3.yaxis.grid(True, linestyle="--", alpha=0.3)

    for i, row in df_site.iterrows():
        x = row["월"]
        y = row["손익율"]
        ax3.text(i, y, f"{y:.1f}%", fontsize=8, color="black", ha="center", va="bottom")

    st.pyplot(fig3)

