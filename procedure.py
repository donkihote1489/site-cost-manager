# 2단계: procedure.py 완전 재작성 – 월/연도 상태 공유 방지 + 다음 단계 정확 이동
from pathlib import Path

fixed_procedure_code = """
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
    month = f"{int(month):02d}"  # 월 통일
    step_list = get_procedure_flow().get(cost_type, [])
    if not step_list:
        st.error("❌ 해당 비용유형에 대한 절차 흐름이 정의되어 있지 않습니다.")
        return

    insert_initial_steps(site, year, month, cost_type, step_list)
    rows = load_procedure_steps(site, year, month, cost_type)
    if not rows:
        st.warning("📭 절차 단계가 없습니다.")
        return

    df = pd.DataFrame(rows, columns=[
        "현장명", "연도", "월", "비용유형", "단계번호",
        "작업내용", "담당부서", "상태", "기성금", "노무비", "투입비"
    ])
    df_active = df[df["상태"] != "완료"].sort_values("단계번호")

    if df_active.empty:
        st.success("🎉 모든 절차가 완료되었습니다.")
        return

    row = df_active.iloc[0]
    st.subheader(f"📍 현재 단계: {row['단계번호']} - {row['작업내용']}")
    st.markdown(f"**담당 부서:** `{row['담당부서']}`")

    if row["담당부서"] == st.session_state["role"]:
        상태 = st.radio("📌 진행 상태", ["진행중", "완료"],
                        index=0 if row["상태"] == "진행중" else 1,
                        horizontal=True)

        key = (cost_type, row["단계번호"])

        if key in COST_INPUT_CONDITIONS:
            field = COST_INPUT_CONDITIONS[key]
            금액 = st.number_input(f"💰 {field} 입력", min_value=0, step=100000, key=f"{field}_{row['단계번호']}")
        else:
            금액 = None
            field = None

        if st.button("💾 저장"):
            update_step_status(
                site, year, month, cost_type,
                row["단계번호"], 상태,
                금액컬럼=field if 금액 is not None else None,
                금액=금액 if 금액 is not None else None
            )
            st.success("✅ 상태가 저장되었습니다.")
            st.rerun()

        if row["상태"] == "완료":
            if st.button("➡️ 다음 단계로 이동"):
                update_step_status(site, year, month, cost_type, row["단계번호"], "완료")
                activate_next_step(site, year, month, cost_type, row["단계번호"])
                st.rerun()
    else:
        st.info("🔒 이 단계는 귀하의 부서가 담당하지 않습니다.")
"""

# 저장
path = Path("/mnt/data/procedure_full_fix_final.py")
path.write_text(fixed_procedure_code.strip(), encoding="utf-8")
path
