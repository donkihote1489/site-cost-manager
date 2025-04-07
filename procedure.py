
import streamlit as st
import pandas as pd
from db import (
    insert_initial_steps, load_procedure_steps,
    update_step_status, activate_next_step, get_next_step
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
        "2. 기성금 청구 및 수금": [...],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [...],
        "4. 선금(외 기타)보증": [...]
    }

def get_current_step(df):
    df_pending = df[df["상태"] == "진행중"].sort_values("단계번호")
    return df_pending.iloc[0] if not df_pending.empty else None

def is_my_department(부서):
    return 부서 == st.session_state.get("role", "")

def render_step_controls(row, site, year, month, cost_type):
    step_no = row["단계번호"]
    상태 = row["상태"]
    담당부서 = row["담당부서"]
    작업내용 = row["작업내용"]
    st.subheader(f"현재 단계: {step_no} - {작업내용}")
    st.markdown(f"담당 부서: `{담당부서}`")

    if is_my_department(담당부서):
        new_status = st.radio("진행 상태", ["진행중", "완료"], index=0 if 상태 == "진행중" else 1, horizontal=True)
        if new_status != 상태:
            update_step_status(site, year, month, cost_type, step_no, new_status)
            st.rerun()

        key = (cost_type, step_no)
        금액필드 = COST_INPUT_CONDITIONS.get(key)
        if 금액필드:
            금액 = st.number_input(f"{금액필드} 입력", min_value=0, step=100000, value=int(row[금액필드] or 0))
            if 금액 != row[금액필드]:
                update_step_status(site, year, month, cost_type, step_no, new_status, 금액필드, 금액)
                st.rerun()
    else:
        st.info("이 단계는 귀하의 부서가 담당하지 않습니다.")

def render_next_step_button(row, site, year, month, cost_type):
    step_no = row["단계번호"]
    if st.button("다음 단계로 이동"):
        # 상태 강제 저장 (완료 확인이 느릴 경우 보완)
        if row["상태"] != "완료":
            update_step_status(site, year, month, cost_type, step_no, "완료")

        latest = load_procedure_steps(site, year, month, cost_type)
        latest_df = pd.DataFrame(latest, columns=[
            "현장명", "연도", "월", "비용유형", "단계번호",
            "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
        ])
        latest_current = latest_df[latest_df["단계번호"] == step_no].iloc[0]
        if latest_current["상태"] == "완료":
            activate_next_step(site, year, month, cost_type, step_no)
            st.rerun()
        else:
            st.warning("'완료' 상태일 때만 다음 단계로 이동할 수 있습니다.")

def procedure_flow_view(site, year, month, cost_type):
    st.header("📋 절차 진행 현황")
    flow = get_procedure_flow().get(cost_type)
    if not flow:
        st.warning("해당 비용유형에 대한 절차 흐름이 정의되지 않았습니다.")
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
