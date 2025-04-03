# main.py - 단계별 진행 흐름 제어 (단일 단계 표시 + 권한제한)
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

DB_PATH = 'database.db'

USERS = {
    "siteuser1": {"password": "1234", "role": "현장"},
    "office1": {"password": "abcd", "role": "본사 공무팀"},
    "finance1": {"password": "pass", "role": "경영지원부"}
}

# 로그인 처리 함수
def login_view():
    st.sidebar.header("🔐 로그인")
    username = st.sidebar.text_input("사용자 ID")
    password = st.sidebar.text_input("비밀번호", type="password")
    if st.sidebar.button("로그인"):
        user_info = USERS.get(username)
        if user_info and user_info['password'] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = user_info['role']
            st.success(f"{user_info['role']} 계정으로 로그인되었습니다.")
            st.rerun()
        else:
            st.sidebar.error("❌ 로그인 실패: 아이디 또는 비밀번호가 올바르지 않습니다.")

# DB 초기화 함수
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS 절차상태 (
                현장명 TEXT,
                연도 TEXT,
                월 TEXT,
                비용유형 TEXT,
                단계번호 INTEGER,
                작업내용 TEXT,
                담당부서 TEXT,
                상태 TEXT DEFAULT '진행중',
                기성금 INTEGER DEFAULT 0,
                노무비 INTEGER DEFAULT 0,
                투입비 INTEGER DEFAULT 0,
                PRIMARY KEY (현장명, 연도, 월, 비용유형, 단계번호)
            )
        ''')

# 계약체결 절차 흐름 정의
CONTRACT_FLOW = [
    (1, '계약(변경)보고', '현장'),
    (2, '계약(변경)확인', '본사 공무팀'),
    (3, '계약 승인 요청 접수', '현장'),
    (4, '계약 진행 요청', '본사 공무팀'),
    (5, '보증 등 발행 협력사 등록', '경영지원부'),
    (6, 'Kiscon사이트 등록', '본사 공무팀')
]

# 절차 초기화 함수
def initialize_procedure(site, year, month, type_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for step_no, task, dept in CONTRACT_FLOW:
            cursor.execute("""
                INSERT OR IGNORE INTO 절차상태 (현장명, 연도, 월, 비용유형, 단계번호, 작업내용, 담당부서)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (site, year, month, type_name, step_no, task, dept))
        conn.commit()

# 절차 상태 로드
def load_procedure(site, year, month, type_name):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("""
            SELECT * FROM 절차상태
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=?
            ORDER BY 단계번호
        """, conn, params=(site, year, month, type_name))
    return df

# 절차 상태 업데이트
def update_step_status(site, year, month, type_name, step_no, 상태):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE 절차상태
            SET 상태=?
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
        """, (상태, site, year, month, type_name, step_no))
        conn.commit()

# --- 앱 실행 ---
st.set_page_config(page_title="현장비용 분석", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")
init_db()

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    login_view()
    st.stop()

user_role = st.session_state.role
st.sidebar.success(f"🔓 {user_role} 로그인됨")

# 기본 입력
st.sidebar.header("📌 기본 정보 입력")
site = st.sidebar.selectbox("현장명", ['화태백야', '제3연륙교'])
year = st.sidebar.text_input("연도", value=str(datetime.now().year))
month = st.sidebar.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
type_name = st.sidebar.selectbox("비용유형", ['1. 계약(변경)체결'])

# 절차 초기화 및 상태 불러오기
initialize_procedure(site, year, month, type_name)
df_proc = load_procedure(site, year, month, type_name)

# 현재 보여줄 단계 찾기
latest_completed = df_proc[df_proc['상태'] == '완료']['단계번호'].max()
next_step_no = 1 if pd.isna(latest_completed) else int(latest_completed) + 1
current_step = df_proc[df_proc['단계번호'] == next_step_no]

if current_step.empty:
    st.success("🎉 모든 절차가 완료되었습니다!")
else:
    row = current_step.iloc[0]
    st.subheader(f"📍 현재 단계: {row['단계번호']} - {row['작업내용']}")
    st.markdown(f"**담당 부서:** `{row['담당부서']}`  |  **상태:** `{row['상태']}`")

    if row['담당부서'] == user_role:
        new_status = st.radio("📌 상태 변경", ['진행중', '완료'],
                              index=0 if row['상태'] == '진행중' else 1,
                              horizontal=True)
        if new_status != row['상태']:
            update_step_status(site, year, month, type_name, row['단계번호'], new_status)
            st.success("✅ 상태가 업데이트되었습니다.")
            st.rerun()
    else:
        st.info(f"이 단계는 `{row['담당부서']}`만 완료 처리할 수 있습니다.")
