import streamlit as st
from datetime import datetime
from auth import login_view, check_login
from db import init_db
from procedure import procedure_flow_view, get_procedure_flow, save_state_to_file

# ✅ 진입 확인 로그
st.write("✅ main.py 진입됨")

st.set_page_config(page_title="현장비용 관리 시스템", layout="wide")
st.title("🏗️ 관수이앤씨 현장비용 관리 시스템")

init_db()

# --- 🔒 로그인 제어 영역 ---
if st.sidebar.button("🔒 로그아웃", use_container_width=True):
    st.session_state.clear()
    st.rerun()

if not check_login():
    login_view()
    st.stop()

st.sidebar.success(f"✅ 로그인됨: {st.session_state.get('role')}")

# 이메일 전송 기능 토글
st.sidebar.markdown("---")
st.sidebar.header("📩 이메일 설정")
st.sidebar.checkbox("📧 이메일 알림 전송", value=True, key="email_enabled")

# --- 📂 입력 파라미터 선택 영역 ---
st.sidebar.markdown("---")
st.sidebar.header("📂 입력 파라미터 선택")

sites = ["화태백야", "제3연륙교"]
site = st.sidebar.selectbox("현장명", sites)
year = st.sidebar.text_input("연도", value=str(datetime.now().year))
month = st.sidebar.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
cost_type = st.sidebar.selectbox("비용유형", list(get_procedure_flow().keys()))

# --- 🧹 절차 초기화 섹션 ---
st.sidebar.markdown("---")
st.sidebar.header("🧹 절차 초기화 (개별)")

if "절차상태" in st.session_state:
    keys = list(st.session_state["절차상태"].keys())
    if keys:
        selected = st.sidebar.selectbox("초기화할 절차", keys, key="sidebar_reset")
        if st.sidebar.button("선택한 절차 초기화", use_container_width=True):
            st.session_state["절차상태"][selected]["current_step"] = 1
            st.session_state["절차상태"][selected]["status"] = {
                k: "진행중" for k in st.session_state["절차상태"][selected]["status"]
            }
            save_state_to_file()
            st.sidebar.success(f"✅ 초기화 완료: {selected}")
            st.rerun()
    else:
        st.sidebar.info("초기화할 절차가 없습니다.")

# --- ✅ 입력 유효성 검사 함수 ---
def is_valid_inputs():
    if not year.isdigit() or not (2000 <= int(year) <= 2100):
        st.sidebar.error("❌ 올바른 연도를 입력하세요 (예: 2024)")
        return False
    if site not in sites:
        st.sidebar.error("❌ 현장을 선택하세요")
        return False
    if cost_type not in get_procedure_flow():
        st.sidebar.error("❌ 유효한 비용 유형이 아닙니다.")
        return False
    return True

# --- 🚦 본문 영역 ---

st.markdown("---")

if is_valid_inputs():
    procedure_flow_view(site, year, month, cost_type)

st.markdown("---")

if st.checkbox("📊 결과 리포트 보기"):
    with st.container():
        from dashboard import summary_dashboard
        summary_dashboard()
