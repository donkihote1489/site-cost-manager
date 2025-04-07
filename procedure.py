import streamlit as st
import pandas as pd
from db import (
    insert_initial_steps,
    load_procedure_steps,
    update_step_status,
    activate_next_step
)

# 금액 입력 조건 매핑: (비용유형, 단계번호): 금액컬럼
COST_INPUT_CONDITIONS = {
    ("2. 기성금 청구 및 수금", 3): "기성금",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 3): "노무비",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 5): "투입비"
}

# 전체 절차 정의
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

# 절차 플로우 UI 로직
def procedure_flow_view(site, year, month, cost_type):
    month = f"{int(month):02d}"
    flow = get_procedure_flow().get(cost_type, [])

    if not flow:
        st.error("❌ 정의되지 않은 비용유형입니다.")
        return

    # 초기 절차 생성 (중복 삽입 방지)
    insert_initial_steps(site, year, month, cost_type, flow)

    # 데이터 다시 로딩
    steps = load_procedure_steps(site, year, month, cost_type)

    if not steps:
        st.warning("📭 등록된 절차가 없습니다.")
        return

    # DataFrame 구성
    df = pd.DataFrame(steps, columns=[
        "현장명", "연도", "월", "비용유형", "단계번호",
        "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
    ])

    # 완료되지 않은 절차 중 가장 앞 단계
    df_pending = df[df["상태"] != "완료"].sort_values("단계번호")
    if df_pending.empty:
        st.success("🎉 모든 절차가 완료되었습니다.")
        return

    # 현재 진행 중인 단계 로딩
    row = df_pending.iloc[0]
    step_no = row["단계번호"]
    담당부서 = row["담당부서"]
    상태 = row["상태"]
    작업내용 = row["작업내용"]

    st.subheader(f"📍 현재 단계: {step_no} - {작업내용}")
    st.markdown(f"**담당 부서:** `{담당부서}`")

    is_my_role = (담당부서 == st.session_state.get("role", ""))

    if is_my_role:
        # 진행 상태 선택
        new_status = st.radio("📌 진행 상태", ["진행중", "완료"], index=0 if 상태 == "진행중" else 1, horizontal=True)

        # 금액 입력 조건 확인
        key = (cost_type, step_no)
        금액필드 = COST_INPUT_CONDITIONS.get(key)
        금액입력 = None
        if 금액필드:
            금액입력 = st.number_input(f"💰 {금액필드} 입력", min_value=0, step=100000, key=f"{금액필드}_{step_no}")

        # 저장 버튼
        if st.button("💾 저장", key="save_btn"):
            update_step_status(
                site, year, month, cost_type, step_no,
                상태=new_status,
                금액컬럼=금액필드 if 금액입력 is not None else None,
                금액=금액입력 if 금액입력 is not None else None
            )
            st.success("✅ 저장되었습니다.")
            st.rerun()

        # 저장 후 상태가 DB에 반영되었는지 다시 로드해서 판단해야 하므로
        # 아래 버튼은 조건에 따라 다시 나타나야 함

        # 데이터 최신화
        steps_updated = load_procedure_steps(site, year, month, cost_type)
        df_updated = pd.DataFrame(steps_updated, columns=df.columns)
        updated_row = df_updated[df_updated["단계번호"] == step_no].iloc[0]
        updated_status = updated_row["상태"]

        if updated_status == "완료":
            if st.button("➡️ 다음 단계로 이동", key="next_btn"):
                activate_next_step(site, year, month, cost_type, step_no)
                st.success("✅ 다음 단계로 이동하였습니다.")
                st.rerun()

    else:
        st.info("🔒 이 단계는 귀하의 부서가 담당하지 않습니다.")

