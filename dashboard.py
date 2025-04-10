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
