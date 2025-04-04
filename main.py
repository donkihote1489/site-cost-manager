import streamlit as st
from datetime import datetime
from auth import login_view, check_login
from db import init_db
from procedure import procedure_flow_view, get_procedure_flow
from dashboard import summary_dashboard

st.set_page_config(page_title="현장비용 관리 시스템", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")

init_db()

if not check_login():
    login_view()
    st.stop()

st.sidebar.success(f"✅ 로그인됨: {st.session_state['role']}")

st.sidebar.header("📌 기본 정보 입력")
sites = ["화태백야", "제3연륙교"]
site = st.sidebar.selectbox("현장명", sites)

this_year = datetime.now().year
def is_valid_year(input_text):
    return input_text.isdigit() and 2000 <= int(input_text) <= this_year + 2

def validate_inputs():
    if not is_valid_year(year):
        st.sidebar.error("❌ 올바른 연도를 입력하세요 (예: 2024)")
        return False
    if site not in sites:
        st.sidebar.error("❌ 현장을 선택하세요")
        return False
    if cost_type not in get_procedure_flow().keys():
        st.sidebar.error("❌ 유효한 비용 유형이 아닙니다")
        return False
    return True

year = st.sidebar.text_input("연도", value=str(this_year))
month = st.sidebar.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
cost_type = st.sidebar.selectbox("비용유형", list(get_procedure_flow().keys()))

if validate_inputs():
    procedure_flow_view(site, year, month, cost_type)
    if st.checkbox("📊 결과 리포트 보기"):
        summary_dashboard()
