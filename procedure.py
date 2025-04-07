
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

def initialize_procedure(site, year, month, cost_type):
    try:
        flow = get_procedure_flow().get(cost_type)
        if not flow:
            st.warning(f"[초기화 실패] '{cost_type}'에 대한 절차 흐름이 정의되지 않았습니다.")
            return None
        st.info(f"[초기화] '{cost_type}' - 단계 {len(flow)}개 등록 시도")
        insert_initial_steps(site, year, month, cost_type, flow)
        rows = load_procedure_steps(site, year, month, cost_type)
        if not rows:
            st.warning(f"[DB 조회 실패] 조건(site={site}, year={year}, month={month}, type={cost_type})로 불러온 절차 데이터가 없습니다.")
            return None
        return pd.DataFrame(rows, columns=[
            "현장명", "연도", "월", "비용유형", "단계번호",
            "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
        ])
    except Exception as e:
        st.error(f"[initialize_procedure 에러] {e}")
        return None

def get_current_step(df):
    df_pending = df[df["상태"] != "완료"].sort_values("단계번호")
    return df_pending.iloc[0] if not df_pending.empty else None

def is_my_department(부서):
    return 부서 == st.session_state.get("role", "")

def procedure_flow_view(site, year, month, cost_type):
    df = initialize_procedure(site, year, month, cost_type)
    if df is None:
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
