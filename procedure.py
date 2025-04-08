import streamlit as st
import pandas as pd
from db import (
    insert_initial_steps, load_procedure_steps,
    update_step_status, activate_next_step
)

# 금액 입력 대상 정의
COST_INPUT_CONDITIONS = {
    ("2. 기성금 청구 및 수금", 3): "기성금",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 3): "노무비",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 5): "투입비"
}

# 절차 흐름 정의
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
            (1, "기성내역서 작성", "현장"),
            (2, "기성내역 확인", "본사 공무팀"),
            (3, "청구서 제출", "현장"),
            (4, "기성청구 접수", "본사 공무팀"),
            (5, "수금 및 확인", "경영지원부")
        ],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [
            (1, "지급내역 정리", "현장"),
            (2, "지급 검토", "본사 공무팀"),
            (3, "노무비 입력", "현장"),
            (4, "협력업체 지급 확인", "경영지원부"),
            (5, "투입비 정산", "현장")
        ],
        "4. 선금(외 기타)보증": [
            (1, "요청 사유 작성", "현장"),
            (2, "내부 확인", "본사 공무팀"),
            (3, "보증서 발급", "경영지원부")
        ]
    }

def get_current_step(df):
    df_pending = df[df["상태"] == "진행중"].sort_values("단계번호")
    return df_pending.iloc[0] if not df_pending.empty else None

def is_my_department(부서):
    return st.session_state.get("role", "").strip() == 부서.strip()

def render_step_controls(row, site, year, month, cost_type):
    step_no = row["단계번호"]
    상태 = row["상태"]
    담당부서 = row["담당부서"]
    작업내용 = row["작업내용"]

    st.subheader(f"현재 단계: {step_no} - {작업내용}")
    st.markdown(f"담당 부서: `{담당부서}`")

    if is_my_department(담당부서):
        new_status = st.radio(
            "진행 상태", ["진행중", "완료"],
            index=0 if 상태 == "진행중" else 1,
            horizontal=True,
            key=f"radio_{step_no}"
        )

        if str(new_status).strip() != str(상태).strip():
            update_step_status(site, year, month, cost_type, step_no, new_status)
            st.session_state["step_completed"] = True
            st.rerun()

        금액필드 = COST_INPUT_CONDITIONS.get((cost_type, step_no))
        if 금액필드:
            입력값 = st.number_input(
                f"{금액필드} 입력", min_value=0, step=100000,
                value=int(row[금액필드] or 0), key=f"amt_{step_no}"
            )
            if 입력값 != row[금액필드]:
                update_step_status(site, year, month, cost_type, step_no, new_status, 금액필드, 입력값)
                st.session_state["step_completed"] = True
                st.rerun()
    else:
        st.info("이 단계는 귀하의 부서가 담당하지 않습니다.")

def render_next_step_button(row, site, year, month, cost_type):
    step_no = row["단계번호"]

    if not st.session_state.get("step_completed", False):
        st.info("✅ 상태를 '완료'로 저장한 뒤 다음 단계로 이동할 수 있습니다.")
        return

    if st.button("다음 단계로 이동", key=f"next_{step_no}"):
        steps = load_procedure_steps(site, year, month, cost_type)
        df = pd.DataFrame(steps, columns=[
            "현장명", "연도", "월", "비용유형", "단계번호",
            "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
        ])
        current = df[df["단계번호"] == step_no]
        if current.empty:
            st.error("❌ 단계를 찾을 수 없습니다.")
            return

        상태 = str(current.iloc[0]["상태"]).strip()
        if 상태 != "완료":
            st.warning(f"⚠️ 현재 단계 상태가 '완료'가 아닙니다. (현재 상태: {상태})")
            return

        activate_next_step(site, year, month, cost_type, step_no)
        st.success("✅ 다음 단계로 이동 완료")
        st.session_state.pop("step_completed", None)
        st.rerun()

def procedure_flow_view(site, year, month, cost_type):
    st.header("📋 절차 진행 현황")

    flow = get_procedure_flow().get(cost_type)
    if not flow:
        st.warning("❌ 해당 비용유형에 대한 절차 흐름이 없습니다.")
        return

    insert_initial_steps(site, year, month, cost_type, flow)

    df = pd.DataFrame(
        load_procedure_steps(site, year, month, cost_type),
        columns=["현장명", "연도", "월", "비용유형", "단계번호", "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"]
    )

    current_row = get_current_step(df)
    if current_row is None:
        st.success("✅ 모든 단계가 완료되었습니다.")
        return

    render_step_controls(current_row, site, year, month, cost_type)
    render_next_step_button(current_row, site, year, month, cost_type)



