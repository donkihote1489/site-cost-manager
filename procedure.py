import streamlit as st
import pandas as pd
from db import (
    insert_initial_steps,
    load_procedure_steps,
    update_step_status,
    activate_next_step
)

COST_INPUT_CONDITIONS = {
    ("2. 기성금 청구 및 수금", 3): "기성금",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 3): "노무비",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 5): "투입비"
}

def get_procedure_flow():
    return {
        "1. 계약(변경)체결": [
            (1, "계약(변경)보고", "현장"),
            (2, "계약(변경)확인", "본사 공무팀"),
            (3, "계약 승인 요청 접수", "현장"),
            (4, "계약 진행 요청", "본사 공무팀"),
            (5, "보증 등 발행 협력사 등록", "경영지원부"),
            (6, "Kiscon사이트 등록", "본사 공무팀")
        ],
        "2. 기성금 청구 및 수금": [
            (1, "기성 조서 작성", "현장"),
            (2, "예상 기성 확인", "본사 공무팀"),
            (3, "기성 확정", "현장"),
            (4, "발행 요청 확인", "본사 공무팀"),
            (5, "계산서 발행 협력사 등록", "경영지원부"),
            (6, "기성금 수금", "경영지원부"),
            (7, "Kiscon 사이트 등록", "본사 공무팀")
        ],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [
            (1, "노무대장 작성", "현장"),
            (2, "노무대장 확인", "본사 공무팀"),
            (3, "노무비 신고", "경영지원부"),
            (4, "보험료 확정", "경영지원부"),
            (5, "하도급지킴이 등록 및 투입비 입력", "현장"),
            (6, "하도급지킴이 확인", "본사 공무팀"),
            (7, "지급 확인", "경영지원부")
        ],
        "4. 선금(외 기타)보증": [
            (1, "선금 공문 접수", "현장"),
            (2, "공문 보고", "본사 공무팀"),
            (3, "보증 발행 등록", "경영지원부"),
            (4, "Kiscon 등록", "본사 공무팀")
        ]
    }

def procedure_flow_view(site, year, month, cost_type):
    month = f"{int(month):02d}"
    flow = get_procedure_flow().get(cost_type, [])

    if not flow:
        st.error("❌ 정의되지 않은 비용유형입니다.")
        return

    insert_initial_steps(site, year, month, cost_type, flow)
    steps = load_procedure_steps(site, year, month, cost_type)

    if not steps:
        st.warning("📭 등록된 절차가 없습니다.")
        return

    df = pd.DataFrame(steps, columns=[
        "현장명", "연도", "월", "비용유형", "단계번호",
        "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
    ])

    df_pending = df[df["상태"] != "완료"].sort_values("단계번호")
    if df_pending.empty:
        st.success("🎉 모든 절차가 완료되었습니다.")
        return

    row = df_pending.iloc[0]
    step_no = row["단계번호"]
    담당부서 = row["담당부서"]
    상태 = row["상태"]
    작업내용 = row["작업내용"]

    st.subheader(f"📍 현재 단계: {step_no} - {작업내용}")
    st.markdown(f"**담당 부서:** `{담당부서}`")

    is_my_role = (담당부서 == st.session_state.get("role", ""))

    if is_my_role:
        key = (cost_type, step_no)
        금액필드 = COST_INPUT_CONDITIONS.get(key)
        금액입력 = None

        if 금액필드:
            금액입력 = st.number_input(f"💰 {금액필드} 입력", min_value=0, step=100000, key=f"{금액필드}_{step_no}")
            if 금액입력 is not None:
                update_step_status(site, year, month, cost_type, step_no, 상태=상태,
                                   금액컬럼=금액필드, 금액=금액입력)

        # 자동 저장용 라디오 버튼
        new_status = st.radio("📌 진행 상태 (자동저장)", ["진행중", "완료"],
                              index=0 if 상태 == "진행중" else 1,
                              horizontal=True,
                              key=f"status_radio_{step_no}")

        # 변경되었을 경우 즉시 저장
        if new_status != 상태:
            update_step_status(site, year, month, cost_type, step_no, 상태=new_status)
            st.experimental_rerun()

        # 다음 단계로 이동 버튼은 항상 표시
        if st.button(➡️ 다음 단계로 이동", key="next_btn"):
            current_data = load_procedure_steps(site, year, month, cost_type)
            current_df = pd.DataFrame(current_data, columns=df.columns)
            current_row = current_df[current_df["단계번호"] == step_no].iloc[0]
            if current_row["상태"] == "완료":
                activate_next_step(site, year, month, cost_type, step_no)
                st.success("✅ 다음 단계로 이동하였습니다.")
                st.experimental_rerun()
            else:
                st.warning("❗ 진행 상태를 '완료'로 변경해야 다음 단계로 이동할 수 있습니다.")

    else:
        st.info("🔒 이 단계는 귀하의 부서가 담당하지 않습니다.")
