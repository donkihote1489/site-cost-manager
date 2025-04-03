# main.py (역할별 입력 항목 제어 반영)
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

DB_PATH = 'database.db'

# 사용자 계정 정보 (데모용)
USERS = {
    "siteuser1": {"password": "1234", "role": "현장"},
    "office1": {"password": "abcd", "role": "본사 공무팀"},
    "finance1": {"password": "pass", "role": "경영지원부"}
}

# 로그인 처리
def login():
    st.sidebar.header("🔐 로그인")
    username = st.sidebar.text_input("사용자 ID")
    password = st.sidebar.text_input("비밀번호", type="password")
    if st.sidebar.button("로그인"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = user["role"]
            st.success(f"{user['role']} 계정으로 로그인되었습니다.")
            st.experimental_rerun()
        else:
            st.sidebar.error("❌ 로그인 실패: 아이디 또는 비밀번호가 올바르지 않습니다.")

# DB 초기화
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

# 데이터 저장
def save_data(data):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM 비용데이터", conn)
        condition = (
            (df['현장명'] == data['현장명']) &
            (df['연도'] == data['연도']) &
            (df['월'] == data['월']) &
            (df['비용유형'] == data['비용유형']) &
            (df['단계'] == data['단계'])
        )
        df = df[~condition]
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_sql('비용데이터', conn, index=False, if_exists='replace')

# ------------------- 앱 시작 -------------------
st.set_page_config(page_title="현장비용 분석", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")
init_db()

# 로그인 상태 확인
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    login()
    st.stop()

# 로그인 성공 후 사용자 정보
role = st.session_state.role
st.sidebar.success(f"🔓 {role} 로그인됨")

# 공통 입력 항목
st.sidebar.header("📌 기본 정보 입력")
if '현장목록' not in st.session_state:
    st.session_state.현장목록 = ['화태백야', '제3연륙교']
selected_site = st.sidebar.selectbox("현장명", st.session_state.현장목록)
year = st.sidebar.text_input("연도 입력 (예: 2025)", "2025")
month = st.sidebar.selectbox("월 선택", [f"{i:02d}" for i in range(1, 13)])

# 역할에 따라 화면 분기
if role == "현장":
    st.subheader("📥 비용 입력 - 현장")
    selected_type = st.radio("비용 유형 선택", [
        "기성금", "투입비"
    ])
    if selected_type == "기성금":
        amount = st.number_input("💰 기성금 입력", min_value=0, step=100000)
        if st.button("기성금 저장"):
            save_data({
                '현장명': selected_site,
                '연도': year,
                '월': f"{year}-{month}",
                '비용유형': "기성금",
                '단계': "기성 확정",
                '담당팀': "현장",
                '기성금': amount,
                '노무비': 0,
                '투입비': 0
            })
            st.success("기성금 저장 완료!")

    elif selected_type == "투입비":
        input_cost = st.number_input("💰 투입비 입력", min_value=0, step=100000)
        if st.button("투입비 저장"):
            save_data({
                '현장명': selected_site,
                '연도': year,
                '월': f"{year}-{month}",
                '비용유형': "투입비",
                '단계': "투입비 입력",
                '담당팀': "현장",
                '기성금': 0,
                '노무비': 0,
                '투입비': input_cost
            })
            st.success("투입비 저장 완료!")

elif role == "경영지원부":
    st.subheader("📥 비용 입력 - 경영지원부")
    labor = st.number_input("💰 노무비 입력", min_value=0, step=100000)
    if st.button("노무비 저장"):
        save_data({
            '현장명': selected_site,
            '연도': year,
            '월': f"{year}-{month}",
            '비용유형': "노무비",
            '단계': "노무비 입력",
            '담당팀': "경영지원부",
            '기성금': 0,
            '노무비': labor,
            '투입비': 0
        })
        st.success("노무비 저장 완료!")

elif role == "본사 공무팀":
    st.subheader("📊 보고 및 승인 뷰 - 본사 공무팀")
    st.info("이 화면은 본사 전용 보고서 및 승인 기능이 제공됩니다.")

else:
    st.warning("권한이 확인되지 않았습니다.")
