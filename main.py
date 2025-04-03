# main.py (안정성 향상된 전체 버전 - st.rerun 적용, 명확한 변수명 등)
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

DB_PATH = 'database.db'

# ---------------- 사용자 계정 정의 ----------------
USERS = {
    "siteuser1": {"password": "1234", "role": "현장"},
    "office1": {"password": "abcd", "role": "본사 공무팀"},
    "finance1": {"password": "pass", "role": "경영지원부"}
}

# ---------------- 로그인 처리 ----------------
def login_view():
    st.sidebar.header("🔐 로그인")
    username = st.sidebar.text_input("사용자 ID")
    password = st.sidebar.text_input("비밀번호", type="password")
    login_btn = st.sidebar.button("로그인")

    if login_btn:
        user_info = USERS.get(username)
        if user_info and user_info['password'] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = user_info['role']
            st.success(f"{user_info['role']} 계정으로 로그인되었습니다.")
            st.rerun()
        else:
            st.sidebar.error("❌ 로그인 실패: 아이디 또는 비밀번호가 올바르지 않습니다.")

# ---------------- DB 초기화 ----------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS 비용데이터 (
                현장명 TEXT,
                연도 TEXT,
                월 TEXT,
                비용유형 TEXT,
                단계 TEXT,
                담당팀 TEXT,
                기성금 INTEGER,
                노무비 INTEGER,
                투입비 INTEGER
            )
        ''')

# ---------------- 데이터 저장 ----------------
def save_cost_record(record: dict):
    with sqlite3.connect(DB_PATH) as conn:
        df_existing = pd.read_sql("SELECT * FROM 비용데이터", conn)
        condition = (
            (df_existing['현장명'] == record['현장명']) &
            (df_existing['연도'] == record['연도']) &
            (df_existing['월'] == record['월']) &
            (df_existing['비용유형'] == record['비용유형']) &
            (df_existing['단계'] == record['단계'])
        )
        df_existing = df_existing[~condition]
        df_updated = pd.concat([df_existing, pd.DataFrame([record])], ignore_index=True)
        df_updated.to_sql('비용데이터', conn, index=False, if_exists='replace')

# ---------------- 앱 실행 시작 ----------------
st.set_page_config(page_title="현장비용 분석", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")

# DB 초기화
init_db()

# 로그인 세션 체크
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    login_view()
    st.stop()

# 사용자 정보
user_role = st.session_state.role
st.sidebar.success(f"🔓 {user_role} 로그인됨")

# 공통 입력 요소
st.sidebar.header("📌 기본 정보 입력")
if '현장목록' not in st.session_state:
    st.session_state.현장목록 = ['화태백야', '제3연륙교']

selected_site = st.sidebar.selectbox("현장명", st.session_state.현장목록)
input_year = st.sidebar.text_input("연도 입력 (예: 2025)", str(datetime.now().year))
input_month = st.sidebar.selectbox("월 선택", [f"{i:02d}" for i in range(1, 13)])
input_ym = f"{input_year}-{input_month}"

# ---------------- 역할별 화면 ----------------
if user_role == "현장":
    st.subheader("📥 비용 입력 - 현장")
    cost_type = st.radio("입력할 항목 선택", ["기성금", "투입비"])

    if cost_type == "기성금":
        value = st.number_input("💰 기성금 입력", min_value=0, step=100000)
        if st.button("기성금 저장"):
            save_cost_record({
                '현장명': selected_site,
                '연도': input_year,
                '월': input_ym,
                '비용유형': "기성금",
                '단계': "기성 확정",
                '담당팀': "현장",
                '기성금': value,
                '노무비': 0,
                '투입비': 0
            })
            st.success("✅ 기성금 저장 완료")

    elif cost_type == "투입비":
        value = st.number_input("💰 투입비 입력", min_value=0, step=100000)
        if st.button("투입비 저장"):
            save_cost_record({
                '현장명': selected_site,
                '연도': input_year,
                '월': input_ym,
                '비용유형': "투입비",
                '단계': "투입비 입력",
                '담당팀': "현장",
                '기성금': 0,
                '노무비': 0,
                '투입비': value
            })
            st.success("✅ 투입비 저장 완료")

elif user_role == "경영지원부":
    st.subheader("📥 비용 입력 - 경영지원부")
    value = st.number_input("💰 노무비 입력", min_value=0, step=100000)
    if st.button("노무비 저장"):
        save_cost_record({
            '현장명': selected_site,
            '연도': input_year,
            '월': input_ym,
            '비용유형': "노무비",
            '단계': "노무비 입력",
            '담당팀': "경영지원부",
            '기성금': 0,
            '노무비': value,
            '투입비': 0
        })
        st.success("✅ 노무비 저장 완료")

elif user_role == "본사 공무팀":
    st.subheader("📊 보고 및 승인 뷰 - 본사 공무팀")
    st.info("이 화면은 추후 승인 프로세스 및 리포트 기능이 탑재될 예정입니다.")

else:
    st.warning("⚠️ 정의되지 않은 사용자 역할입니다.")
