import streamlit as st
from datetime import datetime
from auth import login_view, check_login
from db import init_db
from procedure import procedure_flow_view, get_procedure_flow

if st.session_state.get("manual_rerun", False):
    st.session_state["manual_rerun"] = False
    st.rerun()

st.set_page_config(page_title="현장비용 관리 시스템", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")
st.write("📦 현재 세션 상태:", st.session_state)

init_db()

if not check_login():

    login_view()
    st.stop()

st.sidebar.success(f"✅ 로그인됨: {st.session_state.get('role')}")

sites = ["화태백야", "제3연륙교"]
site = st.sidebar.selectbox("현장명", sites)
year = st.sidebar.text_input("연도", value=str(datetime.now().year))
month = st.sidebar.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
cost_type = st.sidebar.selectbox("비용유형", list(get_procedure_flow().keys()))

def validate_inputs():
    if not year.isdigit():
        st.sidebar.error("연도는 숫자여야 합니다.")
        return False
    if site not in sites:
        st.sidebar.error("올바른 현장을 선택하세요.")
        return False
    return True

if validate_inputs():
    procedure_flow_view(site, year, month, cost_type)
