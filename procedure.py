import streamlit as st
import pandas as pd
import json
import os
from db import update_step_status

SAVE_PATH = "절차상태저장.json"

COST_INPUT_CONDITIONS = {
    ("2. 기성금 청구 및 수금", 3): "기성금",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 3): "노무비",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 5): "투입비"
}

def get_procedure_flow():
    return {
        "1. 계약(변경)체결": [
            ("계약(변경)보고", "현장"),
            ("계약(변경)확인", "본사 공무팀"),
            ("계약 승인 요청 접수", "현장"),
            ("계약 진행 요청", "본사 공무팀"),
            ("보증 등 발행 협력사 등록", "경영지원부"),
            ("Kiscon사이트 등록", "본사 공무팀")
        ],
        "2. 기성금 청구 및 수금": [
            ("기성내역서 작성", "현장"),
            ("기성내역 확인", "본사 공무팀"),
            ("청구서 제출", "현장"),
            ("기성청구 접수", "본사 공무팀"),
            ("수금 및 확인", "경영지원부")
        ],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [
            ("지급내역 정리", "현장"),
            ("지급 검토", "본사 공무팀"),
            ("노무비 입력", "현장"),
            ("협력업체 지급 확인", "경영지원부"),
            ("투입비 정산", "현장")
        ],
        "4. 선금(외 기타)보증": [
            ("요청 사유 작성", "현장"),
            ("내부 확인", "본사 공무팀"),
            ("보증서 발급", "경영지원부")
        ]
    }

def save_state_to_file():
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.절차상태, f, ensure_ascii=False, indent=2)

def load_state_from_file():
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def procedure_flow_view(site, year, month, cost_type):
    key = f"{site}_{year}_{month}_{cost_type}"

    if "절차상태" not in st.session_state:
        st.session_state.절차상태 = load_state_from_file()

    if key not in st.session_state.절차상태:
        steps = get_procedure_flow()[cost_type]
        st.session_state.절차상태[key] = {
            "current_step": 1,
            "status": {label: "진행중" for label, _ in steps},
            "amounts": {},
            "total_steps": len(steps)
        }

    state = st.session_state.절차상태[key]
    steps = get_procedure_flow()[cost_type]

    st.subheader(f"📌 비용유형: {cost_type}")   
    st.header("📋 절차 진행 현황")
    st.button("🔒 로그아웃", on_click=lambda: st.session_state.clear())

    current_index = state["current_step"] - 1

    if current_index >= len(steps):
        st.success("🎉 모든 단계가 완료되었습니다.")
        return

    current_step, 담당부서 = steps[current_index]
    step_label = f"{current_index+1}. {current_step}"
    st.subheader(f"📍 현재 단계: {step_label}")
    st.markdown(f"담당 부서: `{담당부서}`")

    my_role = st.session_state.get("role", "")
    is_authorized = (my_role == 담당부서)

    if is_authorized:
        상태 = st.radio("진행 상태", ["진행중", "완료"],
                    index=0 if state["status"][current_step] == "진행중" else 1)
        state["status"][current_step] = 상태

        update_step_status(
            site=site,
            year=year,
            month=month,
            cost_type=cost_type,
            step_no=state["current_step"],
            상태=상태
        )

        cost_key = (cost_type, state["current_step"])
        if cost_key in COST_INPUT_CONDITIONS:
            label = COST_INPUT_CONDITIONS[cost_key]
            current_value = state["amounts"].get(label, 0)
            입력값 = st.number_input(f"💰 {label} 입력", min_value=0, step=100000, value=current_value)
            if st.button(f"💾 {label} 저장"):
                state["amounts"][label] = 입력값

                update_step_status(
                      site=site,
                      year=year,
                      month=month,
                      cost_type=cost_type,
                      step_no=state["current_step"],
                      상태=상태,
                      금액컬럼=label,
                      금액=입력값
                )

                save_state_to_file()
                st.success(f"{label}이 저장되었습니다.")
                st.rerun()

            if 입력값 != current_value:
                state["amounts"][label] = 입력값

                update_step_status(
                    site=site,
                    year=year,
                    month=month,
                    cost_type=cost_type,
                    step_no=state["current_step"],
                    상태=상태,
                    금액컬럼=label,
                    금액=입력값
                )

        save_state_to_file()
    else:
        st.warning("⚠️ 이 단계는 귀하의 담당 부서가 아닙니다. 수정 권한이 없습니다.")

    if state["status"][current_step] == "완료":
        if st.button("다음 단계로 이동"):
            if state["current_step"] < state["total_steps"]:
                state["current_step"] += 1
                save_state_to_file()
                st.rerun()
            else:
                st.success("🎉 모든 단계가 완료되었습니다.")
                st.rerun()
    else:
        st.button("다음 단계로 이동", disabled=True)
