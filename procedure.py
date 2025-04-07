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
        "1. 계약(변경)체결": [],
        "2. 기성금 청구 및 수금": [],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [],
        "4. 선금(외 기타)보증": []
    }

def initialize_procedure(site, year, month, cost_type):
    month = f"{int(month):02d}"
    insert_initial_steps(site, year, month, cost_type, get_procedure_flow()[cost_type])
    rows = load_procedure_steps(site, year, month, cost_type)
    if not rows:
        return None
    return pd.DataFrame(rows, columns=[
        "현장명", "연도", "월", "비용유형", "단계번호",
        "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
    ])

def get_current_step(df):
    df_pending = df[df["상태"] != "완료"].sort_values("단계번호")
    return df_pending.iloc[0] if not df_pending.empty else None

def is_my_department(부서):
    return 부서 == st.session_state.get("role", "")

def procedure_flow_view(site, year, month, cost_type):
    df = initialize_procedure(site, year, month, cost_type)
    if df is None:
        st.warning("해당 데이터가 없습니다.")
        return

    current = get_current_step(df)
    if current is None:
        st.success("모든 절차가 완료되었습니다.")
        return

    step_no = current["단계번호"]
    담당부서 = current["담당부서"]
    작업내용 = current["작업내용"]
    상태 = current["상태"]

    st.subheader(f"현재 단계: {step_no} - {작업내용}")
    st.markdown(f"담당 부서: **{담당부서}**")

    if is_my_department(담당부서):
        new_status = st.radio("진행 상태", ["진행중", "완료"], index=0 if 상태 == "진행중" else 1, horizontal=True)
        if new_status != 상태:
            update_step_status(site, year, month, cost_type, step_no, new_status)
            st.session_state["force_reload"] = True

        금액필드 = COST_INPUT_CONDITIONS.get((cost_type, step_no))
        if 금액필드:
            현재값 = current[금액필드]
            금액 = st.number_input(f"{금액필드} 입력", min_value=0, step=100000, value=int(현재값 or 0))
            if 금액 != 현재값:
                update_step_status(site, year, month, cost_type, step_no, 상태, 금액필드, 금액)
                st.session_state["force_reload"] = True

    if st.button("다음 단계로 이동"):
        latest = load_procedure_steps(site, year, month, cost_type)
        latest_df = pd.DataFrame(latest, columns=df.columns)
        latest_current = latest_df[latest_df["단계번호"] == step_no].iloc[0]
        if latest_current["상태"] == "완료":
            activate_next_step(site, year, month, cost_type, step_no)
            st.session_state["force_reload"] = True
        else:
            st.warning("'완료' 상태일 때만 다음 단계로 이동할 수 있습니다.")

    if st.session_state.get("force_reload"):
        del st.session_state["force_reload"]
        st.rerun()
