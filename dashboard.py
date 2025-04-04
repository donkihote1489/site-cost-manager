
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
    df = df.fillna(0)
    df["손수익"] = df["기성금"] - df["투입비"]
    df["노무비비중"] = df["노무비"] / df["투입비"].replace(0, 1)

    st.dataframe(df)
    site = st.selectbox("📍 확인할 현장", df["현장명"].unique())
    df_site = df[df["현장명"] == site]

    st.subheader("📊 월별 비용 추이")
    st.bar_chart(df_site.set_index("월")[["기성금", "투입비", "노무비"]])

    st.subheader("📈 손수익 및 노무비 비중")
    st.line_chart(df_site.set_index("월")[["손수익", "노무비비중"]])
