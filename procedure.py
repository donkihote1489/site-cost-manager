import streamlit as st
import pandas as pd
from db import insert_initial_steps, load_procedure_steps, update_step_status, activate_next_step

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
    step_list = get_procedure_flow().get(cost_type, [])
    if not step_list:
        st.error("❌ 비용 유형에 대한 절차 흐름이 정의되지 않았습니다.")
        return

    insert_initial_steps(site, year, month, cost_type, step_list)
    rows = load_procedure_steps(site, year, month, cost_type)
    if not rows:
        st.warning("⚠️ 절차 단계가 없습니다.")
        return

    df = pd.DataFrame(rows, columns=["현장명", "연도", "월", "비용유형", "단계번호", "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"])
    df_active = df[df["상태"] != "완료"].sort_values("단계번호")

    if df_active.empty:
        st.success("✅ 모든 절차가 완료되었습니다!")
        return

    row = df_active.iloc[0]
    st.subheader(f"📍 현재 단계: {row['단계번호']} - {row['작업내용']}")
    st.markdown(f"**담당 부서:** `{row['담당부서']}`")

    if row["담당부서"] == st.session_state["role"]:
        # 진행 상태 선택
        상태 = st.radio("📌 진행 상태", ["진행중", "완료"], index=0 if row["상태"] == "진행중" else 1, horizontal=True)
        key = (cost_type, row["단계번호"])
        저장됨 = False

        if key in COST_INPUT_CONDITIONS:
            field = COST_INPUT_CONDITIONS[key]
            금액 = st.number_input(f"💰 {field} 입력", min_value=0, step=100000, key=f"{field}_{row['단계번호']}")
            if st.button("💾 저장"):
                update_step_status(site, year, month, cost_type, row["단계번호"], 상태, field, 금액)
                저장됨 = True
                st.success("✅ 저장 완료")
                st.rerun()
        else:
            if st.button("💾 저장"):
                update_step_status(site, year, month, cost_type, row["단계번호"], 상태)
                저장됨 = True
                st.success("✅ 저장 완료")
                st.rerun()

        # 항상 다음 단계 이동 버튼 표시
        if 상태 == "완료" or row["상태"] == "완료":
            if st.button("➡️ 다음 단계로 이동"):
                # 다시 한 번 완료 처리 강제 반영 후 다음 단계 이동
                update_step_status(site, year, month, cost_type, row["단계번호"], "완료")
                activate_next_step(site, year, month, cost_type, row["단계번호"])
                st.success("✅ 다음 단계로 이동 완료")
                st.rerun()
    else:
        st.info("ℹ️ 이 단계는 귀하의 부서가 담당하지 않습니다.")
