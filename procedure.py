import streamlit as st
import pandas as pd
from db import (
    insert_initial_steps,
    load_procedure_steps,
    update_step_status,
    activate_next_step
)

# -------------------------------
# 1차: 절차 흐름 정의 및 초기화
# -------------------------------

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
    month = f"{int(month):02d}"
    flow = get_procedure_flow().get(cost_type, [])
    if not flow:
        st.error("정의되지 않은 비용유형입니다.")
        return None
    insert_initial_steps(site, year, month, cost_type, flow)
    steps = load_procedure_steps(site, year, month, cost_type)
    if not steps:
        st.warning("등록된 절차가 없습니다.")
        return None
    df = pd.DataFrame(steps, columns=[
        "현장명", "연도", "월", "비용유형", "단계번호",
        "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
    ])
    return df

# -------------------------------
# 2차: 현재 단계 탐색 및 상태 판별
# -------------------------------

def get_current_step(df):
    df_pending = df[df["상태"] != "완료"].sort_values("단계번호")
    if df_pending.empty:
        return None
    return df_pending.iloc[0]

def is_my_department(담당부서):
    return 담당부서 == st.session_state.get("role", "")

# -------------------------------
# 3차: 상태 및 금액 자동 저장 처리
# -------------------------------

def handle_auto_save(site, year, month, cost_type, step_row):
    step_no = step_row["단계번호"]
    상태 = step_row["상태"]
    담당부서 = step_row["담당부서"]
    작업내용 = step_row["작업내용"]

    st.subheader(f"현재 단계: {step_no} - {작업내용}")
    st.markdown(f"담당 부서: **{담당부서}**")

    key = (cost_type, step_no)
    금액필드 = COST_INPUT_CONDITIONS.get(key)
    금액입력 = None

    if 금액필드:
        금액입력 = st.number_input(
            f"{금액필드} 입력",
            min_value=0,
            step=100000,
            key=f"금액입력_{step_no}"
        )
        if 금액입력 is not None and 금액입력 != step_row[금액필드]:
            update_step_status(site, year, month, cost_type, step_no, 상태, 금액필드, 금액입력)
            st.success(f"{금액필드} 자동 저장 완료")

    if is_my_department(담당부서):
        new_status = st.radio(
            "진행 상태 (자동 저장)",
        ["진행중", "완료"],
        index=0 if 상태 == "진행중" else 1,
        horizontal=True,
        key=f"status_radio_{step_no}"
        )

        if new_status != 상태:
            update_step_status(site, year, month, cost_type, step_no, new_status)
            st.success("진행 상태 자동 저장 완료")
            st.rerun()

    
# -------------------------------
# 4차: 단계 전환 제어
# -------------------------------

def render_next_step_button(site, year, month, cost_type, step_no):
    st.markdown("---")
    if st.button("다음 단계로 이동", key=f"next_step_btn_{step_no}"):
        steps = load_procedure_steps(site, year, month, cost_type)
        df = pd.DataFrame(steps, columns=[
            "현장명", "연도", "월", "비용유형", "단계번호",
            "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
        ])
        df = df[df["단계번호"] == step_no].reset_index(drop=True)
        current = df.iloc[0]
        if current["상태"].strip() != "완료":
            st.warning("현재 단계를 '완료'로 변경해야 다음 단계로 이동할 수 있습니다.")
            return
        activate_next_step(site, year, month, cost_type, step_no)
        st.success("다음 단계로 이동 완료")
        st.rerun()

# -------------------------------
# 5차: 확장 예외 및 UI 동기화
# -------------------------------

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

    if is_my_department(담당부서):
        handle_auto_save(site, year, month, cost_type, current)
    else:
        st.info("이 단계는 귀하의 부서가 담당하지 않습니다.")

    # 권한과 관계없이 항상 다음 단계 전환 버튼은 표시
    render_next_step_button(site, year, month, cost_type, step_no)
