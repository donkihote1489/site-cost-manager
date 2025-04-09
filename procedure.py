import streamlit as st
import pandas as pd
import json
import os
import smtplib
from email.mime.text import MIMEText
from db import update_step_status

SAVE_PATH = "절차상태저장.json"

COST_INPUT_CONDITIONS = {
    ("2. 기성금 청구 및 수금", 3): "기성금",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 3): "노무비",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 5): "투입비"
}

DEPARTMENT_EMAILS = {
    "현장": "beon333@kwansoo.biz",
    "본사 공무팀": "jaewon@kwansoo.biz",
    "경영지원부": "samin@kwansoo.biz"
}

def send_email(to_email, subject, body):
    from_email = "jaewon@kwansoo.biz"
    password = "kwansoo1234"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
        st.success(f"📧 이메일 전송 완료 → {to_email}")
    except Exception as e:
        st.error(f"📛 이메일 전송 실패: {e}")

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
            ("기성조서 작성", "현장"),
            ("예상 기성 확인", "본사 공무팀"),
            ("기성 확정", "현장"),
            ("발행 요청 확인", "본사 공무팀"),
            ("계산서 발행 및 협력사 등록", "경영지원부"),
            ("기성 금액 수금", "경영지원부"),
            ("Kiscon 등록", "본사 공무팀")
        ],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [
            ("노무대장 작성", "현장"),
            ("노무대장 확인", "본사 공무팀"),
            ("노무비 신고", "경영지원부"),
            ("보험료 확정분 및 노무대장 작성", "경영지원부"),
            ("하도급지킴이 등록", "현장"),
            ("하도급지킴이 확인", "본사 공무팀"),
            ("하도급지킴이 지급 확인,지급", "경영지원부")
        ],
        "4. 선금(외 기타)보증": [
            ("선금 공문 접수", "현장"),
            ("선금 공문 보고", "본사 공무팀"),
            ("선금신청 및 공문회신", "본사 공무팀"),
            ("보증 등 발행 협력사 등록", "경영지원부")
            ("원도급사 통보 Kiscon 등록", "본사 공무팀")
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
                st.success(f"✅ {label}이 저장되었습니다.")
                st.rerun()

            if label in state["amounts"]:
                st.info(f"💾 저장된 {label}: {state['amounts'][label]:,}원")
            else:
                st.warning(f"❗ 아직 {label}이 저장되지 않았습니다.")

        save_state_to_file()
    else:
        st.warning("⚠️ 이 단계는 귀하의 담당 부서가 아닙니다. 수정 권한이 없습니다.")

    if state["status"][current_step] == "완료":
         cost_key = (cost_type, state["current_step"])
         if cost_key in COST_INPUT_CONDITIONS:
              label = COST_INPUT_CONDITIONS[cost_key]
              if label not in state["amounts"]:
                    st.warning(f"⚠️ {label}을 저장한 뒤에 다음 단계로 이동할 수 있습니다.")
                    return

if st.button("다음 단계로 이동"):
    if state["current_step"] < state["total_steps"]:
        state["current_step"] += 1
        save_state_to_file()

        # 📧 이메일 알림 추가
        next_step, next_dept = steps[state["current_step"] - 1]
        to_email = DEPARTMENT_EMAILS.get(next_dept)
        if to_email:
            subject = f"[알림] '{site}' 현장 절차 알림"
            body = (
                f"{site} 현장의 '{current_step}' 단계가 완료되었습니다.\n"
                f"귀 부서에서 담당하는 다음 단계는 '{next_step}'입니다.\n\n"
                f"- 연도: {year} / 월: {month}\n"
                f"- 비용유형: {cost_type}"
            )
            send_email(to_email, subject, body)

        st.rerun()
    else:
        st.success("🎉 모든 단계가 완료되었습니다.")
        st.rerun()

    else:
        st.button("다음 단계로 이동", disabled=True)
