
# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

st.set_page_config(page_title="현장비용 분석", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")

file_path = '현장비용_데이터.csv'

def format_korean_unit(value):
    if value >= 100000000:
        return f"{value // 100000000}억 원"
    elif value >= 10000:
        return f"{value // 10000}만 원"
    else:
        return f"{value:,} 원"

def won_formatter(x, pos):
    if x >= 1_000_000:
        return f'{int(x/1_000_000)}백만'
    elif x >= 10_000:
        return f'{int(x/10_000)}만'
    else:
        return f'{int(x)}'

if '현장목록' not in st.session_state:
    st.session_state.현장목록 = ['화태백야', '제3연륙교']

st.sidebar.header("📌 기본 정보 입력")
selected_site = st.sidebar.selectbox("현장명", st.session_state.현장목록)
year = st.sidebar.text_input("연도 입력 (예: 2025)", "2025")
month = st.sidebar.selectbox("월 선택", [f"{i:02d}" for i in range(1, 13)])

# 절차 상태 초기화
session_key = f"{selected_site}_{year}_{month}"
if '절차상태' not in st.session_state:
    st.session_state.절차상태 = {}
if session_key not in st.session_state.절차상태:
    st.session_state.절차상태[session_key] = {
        "current_step": 1,
        "step_status": {},
        "prev_selected_type": "",
        "completion_flag": False,
        "go_to_next_step": False
    }
state = st.session_state.절차상태[session_key]

selected_type = st.radio("비용 유형 선택", [
    "1. 계약(변경)체결",
    "2. 기성금 청구 및 수금",
    "3. 노무 및 협력업체 지급 및 투입비 입력",
    "4. 선금(외 기타)보증"
])

procedure_steps = {
    "1. 계약(변경)체결": [
        ("1. 계약(변경) 보고", "현장"),
        ("2. 계약(변경) 확인", "본사 공무팀"),
        ("3. 승인 요청 접수", "현장"),
        ("4. 계약 진행 요청", "본사 공무팀"),
        ("5. 보증 등록", "경영지원부"),
        ("6. Kiscon 등록", "본사 공무팀")
    ],
    "2. 기성금 청구 및 수금": [
        ("1. 기성 조서 작성", "현장"),
        ("2. 예상 기성 확인", "본사 공무팀"),
        ("3. 기성 확정", "현장"),
        ("4. 발행 요청 확인", "본사 공무팀"),
        ("5. 계산서 발행 협력사 등록", "경영지원부"),
        ("6. 기성금 수금", "경영지원부"),
        ("7. Kiscon 사이트 등록", "본사 공무팀")
    ],
    "3. 노무 및 협력업체 지급 및 투입비 입력": [
        ("1. 노무대장 작성", "현장"),
        ("2. 노무대장 확인", "본사 공무팀"),
        ("3. 노무비 신고", "경영지원부"),
        ("4. 보험료 확정", "경영지원부"),
        ("5. 하도급지킴이 등록 및 투입비 입력", "현장"),
        ("6. 하도급지킴이 확인", "본사 공무팀"),
        ("7. 지급 확인", "경영지원부")
    ],
    "4. 선금(외 기타)보증": [
        ("1. 선금 공문 접수", "현장"),
        ("2. 공문 보고", "본사 공무팀"),
        ("3. 보증 발행 등록", "경영지원부"),
        ("4. Kiscon 등록", "본사 공무팀")
    ]
}

if selected_type != state["prev_selected_type"]:
    state["current_step"] = 1
    state["step_status"] = {}
    state["completion_flag"] = False
    state["go_to_next_step"] = False
    state["prev_selected_type"] = selected_type

if '결과보기' not in st.session_state:
    st.session_state.결과보기 = False

if st.button("📊 결과 리포트"):
    st.session_state.결과보기 = True

# ---------------------------
# 절차 입력 화면
# ---------------------------
if not st.session_state.결과보기:
    steps = procedure_steps[selected_type]
    total_steps = len(steps)

    if state["completion_flag"]:
        st.success("✅ 모든 단계가 완료되었습니다.")
        if st.button("✏️ 수정하기"):
            state["current_step"] = 1
            state["completion_flag"] = False
    else:
        if state["current_step"] <= total_steps:
            step_text, 담당팀 = steps[state["current_step"] - 1]
            st.subheader(f"📍 현재 단계: {step_text}")
            st.markdown(f"**담당 부서:** `{담당팀}`")

            step_key = f"{selected_site}_{year}_{month}_{selected_type}_{step_text}"
            if step_key not in state["step_status"]:
                state["step_status"][step_key] = "진행중"

            상태 = st.radio("📌 진행 상태", ["진행중", "완료"],
                          index=0 if state["step_status"][step_key] == "진행중" else 1,
                          horizontal=True)
            state["step_status"][step_key] = 상태

            cost_inputs = {
                ("2. 기성금 청구 및 수금", "3. 기성 확정"): "기성금",
                ("3. 노무 및 협력업체 지급 및 투입비 입력", "3. 노무비 신고"): "노무비",
                ("3. 노무 및 협력업체 지급 및 투입비 입력", "5. 하도급지킴이 등록 및 투입비 입력"): "투입비"
            }

            key = (selected_type, step_text)
            if key in cost_inputs:
                field = cost_inputs[key]
                amount = st.number_input(f"💰 {field} 입력", min_value=0, step=100000, key="금액입력")
                st.caption(f"단위 환산: {format_korean_unit(amount)}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 금액 저장"):
                        new_record = {
                            '현장명': selected_site,
                            '연도': year,
                            '월': f"{year}-{month}",
                            '비용유형': selected_type,
                            '단계': step_text,
                            '담당팀': 담당팀,
                            '기성금': 0,
                            '노무비': 0,
                            '투입비': 0
                        }
                        new_record[field] = amount

                        if os.path.exists(file_path):
                            df = pd.read_csv(file_path)
                            condition = (
                                (df['현장명'] == selected_site) &
                                (df['연도'].astype(str) == str(year)) &
                                (df['월'] == f"{year}-{month}") &
                                (df['비용유형'] == selected_type) &
                                (df['단계'] == step_text)
                            )
                            df = df[~condition]
                            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                        else:
                            df = pd.DataFrame([new_record])

                        df.to_csv(file_path, index=False)
                        st.success(f"{field} 저장 완료!")

                with col2:
                    if st.button("🗑️ 입력값 삭제"):
                        if os.path.exists(file_path):
                            df = pd.read_csv(file_path)
                            condition = (
                                (df['현장명'] == selected_site) &
                                (df['연도'].astype(str) == str(year)) &
                                (df['월'] == f"{year}-{month}") &
                                (df['비용유형'] == selected_type) &
                                (df['단계'] == step_text)
                            )
                            df = df[~condition]
                            df.to_csv(file_path, index=False)
                            st.warning(f"{field} 입력값이 삭제되었습니다.")
                            st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ 이전 단계") and state["current_step"] > 1:
                    state["current_step"] -= 1
            with col2:
                if 상태 == "완료":
                    if st.button("다음 단계 ➡️"):
                        state["go_to_next_step"] = True

            if state["go_to_next_step"]:
                state["go_to_next_step"] = False
                if state["current_step"] < total_steps:
                    state["current_step"] += 1
                else:
                    state["completion_flag"] = True
                    st.rerun()


# ---------------------------
# 결과 리포트 화면
# ---------------------------
if st.session_state.결과보기:
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = df[['현장명', '연도', '월', '기성금', '노무비', '투입비']]
        df_filtered = df[df['현장명'] == selected_site].copy()

        st.subheader("📋 전체 데이터 (행 삭제 포함)")
        if not df_filtered.empty:
            df_editable = df_filtered.copy()
            df_editable['삭제'] = False
            edited = st.data_editor(
                df_editable,
                num_rows="dynamic",
                use_container_width=True,
                key="editable_table_unique"
            )

            delete_rows = edited[edited['삭제'] == True]
            if not delete_rows.empty:
                if st.button("🗑️ 체크한 행 삭제하기"):
                    df_all = pd.read_csv(file_path)
                    for _, row in delete_rows.iterrows():
                        df_all = df_all[~(
                            (df_all['현장명'] == row['현장명']) &
                            (df_all['연도'] == row['연도']) &
                            (df_all['월'] == row['월']) &
                            (df_all['기성금'] == row['기성금']) &
                            (df_all['노무비'] == row['노무비']) &
                            (df_all['투입비'] == row['투입비'])
                        )]
                    df_all.to_csv(file_path, index=False)
                    st.success("✅ 선택한 행이 삭제되었습니다.")
                    st.rerun()

        grouped = df_filtered.groupby('월').agg({
            '기성금': 'sum',
            '투입비': 'sum',
            '노무비': 'sum'
        }).reset_index()

        grouped['노무비비중'] = grouped['노무비'] / grouped['투입비'].replace(0, 1)
        grouped['손수익'] = grouped['기성금'] - grouped['투입비']
        grouped['기성금_누적'] = grouped['기성금'].cumsum()
        grouped['투입비_누적'] = grouped['투입비'].cumsum()
        grouped['노무비_누적'] = grouped['노무비'].cumsum()
        grouped['손수익_누적'] = grouped['손수익'].cumsum()
        grouped['기성금_증감률'] = grouped['기성금'].pct_change().fillna(0) * 100
        grouped['투입비_증감률'] = grouped['투입비'].pct_change().fillna(0) * 100
        grouped['노무비_증감률'] = grouped['노무비'].pct_change().fillna(0) * 100
        grouped['손수익_증감률'] = grouped['손수익'].pct_change().fillna(0) * 100
        grouped['월'] = grouped['월'].astype(str)

        st.subheader("📈 월별 분석")

        st.markdown("#### 💰 기성금 vs 투입비 (월별)")
        fig1, ax1 = plt.subplots(figsize=(5, 1.8))
        ax1.bar(grouped['월'], grouped['기성금'], label='기성금')
        ax1.bar(grouped['월'], grouped['투입비'], label='투입비', bottom=0)
        ax1.set_ylabel("금액", fontproperties='Malgun Gothic')
        ax1.set_xticks(range(len(grouped['월'])))
        ax1.set_xticklabels(grouped['월'], rotation=0)
        ax1.legend(prop={'family': 'Malgun Gothic'})
        st.pyplot(fig1)

        st.markdown("#### 📈 손수익 추이 및 증감률")
        fig2, ax2 = plt.subplots(figsize=(5, 1.8))
        ax2.plot(grouped['월'], grouped['손수익'], marker='o')
        ax2.set_ylabel("손수익", fontproperties='Malgun Gothic')
        ax2.set_xticks(range(len(grouped['월'])))
        ax2.set_xticklabels(grouped['월'], rotation=0)
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots(figsize=(5, 1.8))
        ax3.bar(grouped['월'], grouped['손수익_증감률'], color='orange')
        ax3.set_ylabel("증감률 (%", fontproperties='Malgun Gothic')
        ax3.set_xlabel("월", fontproperties='Malgun Gothic')
        ax3.set_xticks(range(len(grouped['월'])))
        ax3.set_xticklabels(grouped['월'], rotation=0)
        st.pyplot(fig3)

        st.markdown("#### 📊 노무비 비중")
        fig4, ax4 = plt.subplots(figsize=(5, 1.8))
        ax4.plot(grouped['월'], grouped['노무비비중'], color='green', marker='o')
        ax4.set_ylabel("노무비 비중", fontproperties='Malgun Gothic')
        ax4.set_xticks(range(len(grouped['월'])))
        ax4.set_xticklabels(grouped['월'], rotation=0)
        st.pyplot(fig4)

        st.markdown("#### 🧮 월별 원형 차트 (기성금 vs 투입비 vs 노무비)")
        st.markdown("#### 🧮 월별 원형 차트 (기성금 vs 투입비 vs 노무비)")
        pie_cols = st.columns(len(grouped))
        for i, row in enumerate(grouped.iterrows()):
            _, row = row
            labels = ['기성금', '투입비', '노무비']
            sizes = [row['기성금'], row['투입비'], row['노무비']]
            total = sum(sizes)
            sizes_pct = [s / total * 100 if total else 0 for s in sizes]
            fig, ax = plt.subplots(figsize=(1.8, 1.8))
            wedges, texts, autotexts = ax.pie(
                sizes_pct,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 7, 'fontproperties': 'Malgun Gothic'}
            )
            ax.set_title(f"{row['월']}", fontsize=8, fontproperties='Malgun Gothic')
            pie_cols[i].pyplot(fig)
            labels = ['기성금', '투입비', '노무비']
            sizes = [row['기성금'], row['투입비'], row['노무비']]
            total = sum(sizes)
            sizes_pct = [s / total * 100 if total else 0 for s in sizes]
            fig, ax = plt.subplots(figsize=(4, 2.5))
            wedges, texts, autotexts = ax.pie(
                sizes_pct,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 10}
            )
            ax.set_title(f"{row['월']} 비중 분석", fontsize=12, fontproperties='Malgun Gothic')
            st.pyplot(fig)

        st.markdown("#### 📄 요약 테이블")
        display_cols = ['월', '기성금', '기성금_증감률', '투입비', '투입비_증감률',
                        '노무비', '노무비_증감률', '노무비비중', '손수익', '손수익_증감률']
        st.dataframe(grouped[display_cols])
    else:
        st.warning("📂 저장된 데이터가 없습니다.")
