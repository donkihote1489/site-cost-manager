import streamlit as st
from datetime import datetime
from auth import login_view, check_login
from db import init_db
from procedure import procedure_flow_view, get_procedure_flow, save_state_to_file

st.set_page_config(page_title="현장비용 관리 시스템", layout="wide")
st.title("🏗️ 관수이앤씨 현장비용 관리 시스템")

init_db()

# 세션 상태 점검
if not check_login():
    login_view()
    st.stop()

st.sidebar.success(f"✅ 로그인됨: {st.session_state.get('role')}")

sites = ["화태백야", "제3연륙교"]
site = st.sidebar.selectbox("현장명", sites)
year = st.sidebar.text_input("연도", value=str(datetime.now().year))
month = st.sidebar.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
cost_type = st.sidebar.selectbox("비용유형", list(get_procedure_flow().keys()))

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

# ✅ 개별 절차 초기화 기능 삽입
st.markdown("### 🧹 개별 절차 초기화")

if "절차상태" in st.session_state:
    keys = list(st.session_state["절차상태"].keys())
    if keys:
        selected = st.selectbox("초기화할 절차를 선택하세요", keys, key="절차초기화")
        if st.button("선택한 절차 초기화"):
            st.session_state["절차상태"][selected]["current_step"] = 1
            st.session_state["절차상태"][selected]["status"] = {
                k: "진행중" for k in st.session_state["절차상태"][selected]["status"]
            }
            save_state_to_file()
            st.success(f"✅ '{selected}' 절차가 초기화되었습니다.")
            st.rerun()
    else:
        st.info("초기화할 절차가 없습니다.")
else:
    st.info("초기화할 절차가 없습니다.")

# 절차 UI 실행
if is_valid_inputs():
    procedure_flow_view(site, year, month, cost_type)

# 결과 리포트 보기
if st.checkbox("📊 결과 리포트 보기"):
    from dashboard import summary_dashboard
    summary_dashboard()
