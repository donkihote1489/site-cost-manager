# main.py - 수정된 패치 버전 (단계 완료 후 다음 단계 갱신 오류 해결)
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

DB_PATH = 'database.db'

USERS = {
    "siteuser1": {"password": "1234", "role": "현장"},
    "office1": {"password": "abcd", "role": "본사 공무팀"},
    "finance1": {"password": "pass", "role": "경영지원부"}
}

def get_procedure_flow():
    return {
        "1. 계약(변경)체결": [
            (1, '계약(변경)보고', '현장'),
            (2, '계약(변경)확인', '본사 공무팀'),
            (3, '계약 승인 요청 접수', '현장'),
            (4, '계약 진행 요청', '본사 공무팀'),
            (5, '보증 등 발행 협력사 등록', '경영지원부'),
            (6, 'Kiscon사이트 등록', '본사 공무팀')
        ],
        "2. 기성금 청구 및 수금": [
            (1, '기성 조서 작성', '현장'),
            (2, '예상 기성 확인', '본사 공무팀'),
            (3, '기성 확정', '현장'),
            (4, '발행 요청 확인', '본사 공무팀'),
            (5, '계산서 발행 협력사 등록', '경영지원부'),
            (6, '기성금 수금', '경영지원부'),
            (7, 'Kiscon 사이트 등록', '본사 공무팀')
        ],
        "3. 노무 및 협력업체 지급 및 투입비 입력": [
            (1, '노무대장 작성', '현장'),
            (2, '노무대장 확인', '본사 공무팀'),
            (3, '노무비 신고', '경영지원부'),
            (4, '보험료 확정', '경영지원부'),
            (5, '하도급지킴이 등록 및 투입비 입력', '현장'),
            (6, '하도급지킴이 확인', '본사 공무팀'),
            (7, '지급 확인', '경영지원부')
        ],
        "4. 선금(외 기타)보증": [
            (1, '선금 공문 접수', '현장'),
            (2, '공문 보고', '본사 공무팀'),
            (3, '보증 발행 등록', '경영지원부'),
            (4, 'Kiscon 등록', '본사 공무팀')
        ]
    }

def login_view():
    st.sidebar.header("🔐 로그인")
    username = st.sidebar.text_input("사용자 ID")
    password = st.sidebar.text_input("비밀번호", type="password")
    if st.sidebar.button("로그인"):
        user = USERS.get(username)
        if user and user['password'] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = user['role']
            st.rerun()
        else:
            st.sidebar.error("❌ 로그인 실패")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS 절차상태 (
                현장명 TEXT, 연도 TEXT, 월 TEXT, 비용유형 TEXT,
                단계번호 INTEGER, 작업내용 TEXT, 담당부서 TEXT,
                상태 TEXT DEFAULT '진행중',
                기성금 INTEGER DEFAULT 0, 노무비 INTEGER DEFAULT 0, 투입비 INTEGER DEFAULT 0,
                PRIMARY KEY (현장명, 연도, 월, 비용유형, 단계번호)
            )
        ''')

def initialize_procedure(site, year, month, cost_type):
    flow = get_procedure_flow()[cost_type]
    with sqlite3.connect(DB_PATH) as conn:
        for step_no, task, dept in flow:
            conn.execute("""
                INSERT OR IGNORE INTO 절차상태
                (현장명, 연도, 월, 비용유형, 단계번호, 작업내용, 담당부서)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (site, year, month, cost_type, step_no, task, dept))
        conn.commit()

def load_steps(site, year, month, cost_type):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("""
            SELECT * FROM 절차상태
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=?
            ORDER BY 단계번호
        """, conn, params=(site, year, month, cost_type))
    return df

def update_step(site, year, month, cost_type, step_no, 상태, 금액컬럼=None, 금액=None):
    with sqlite3.connect(DB_PATH) as conn:
        if 금액컬럼:
            conn.execute(f"""
                UPDATE 절차상태
                SET 상태=?, {금액컬럼}=?
                WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
            """, (상태, 금액, site, year, month, cost_type, step_no))
        else:
            conn.execute("""
                UPDATE 절차상태
                SET 상태=?
                WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
            """, (상태, site, year, month, cost_type, step_no))
        conn.commit()

COST_INPUT_CONDITIONS = {
    ("2. 기성금 청구 및 수금", 3): "기성금",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 3): "노무비",
    ("3. 노무 및 협력업체 지급 및 투입비 입력", 5): "투입비"
}

st.set_page_config(page_title="현장비용 관리", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")
init_db()

if 'logged_in' not in st.session_state:
    login_view()
    st.stop()

role = st.session_state.role
st.sidebar.success(f"{role} 계정 로그인됨")

st.sidebar.header("📌 기본 정보 입력")
site = st.sidebar.selectbox("현장명", ["화태백야", "제3연륙교"])
year = st.sidebar.text_input("연도", value=str(datetime.now().year))
month = st.sidebar.selectbox("월", [f"{i:02d}" for i in range(1, 13)])
cost_type = st.sidebar.selectbox("비용유형 선택", list(get_procedure_flow().keys()))

initialize_procedure(site, year, month, cost_type)
df_steps = load_steps(site, year, month, cost_type)

latest_done = df_steps[df_steps['상태'] == '완료']['단계번호'].max()
next_step = 1 if pd.isna(latest_done) else int(latest_done) + 1
current = df_steps[df_steps['단계번호'] == next_step]

if current.empty:
    st.success("✅ 모든 절차가 완료되었습니다!")
else:
    row = current.iloc[0]
    st.subheader(f"📍 현재 단계: {row['단계번호']} - {row['작업내용']}")
    st.markdown(f"**담당 부서:** `{row['담당부서']}`  |  **상태:** `{row['상태']}`")

    editable = (row['담당부서'] == role)
    if editable:
        상태 = st.radio("📌 상태", ["진행중", "완료"], index=0 if row['상태'] == '진행중' else 1, horizontal=True)
        key = (cost_type, row['단계번호'])
        if key in COST_INPUT_CONDITIONS:
            field = COST_INPUT_CONDITIONS[key]
            금액 = st.number_input(f"💰 {field} 입력", min_value=0, step=100000)
            if st.button("저장 및 완료"):
                update_step(site, year, month, cost_type, row['단계번호'], 상태, field, 금액)
                st.rerun()
        else:
            if st.button("단계 완료 저장"):
                update_step(site, year, month, cost_type, row['단계번호'], 상태)
                st.rerun()
    else:
        st.info("이 단계는 귀하의 부서가 담당하지 않습니다.")

if st.checkbox("📊 결과 리포트 보기"):
    with sqlite3.connect(DB_PATH) as conn:
        df_all = pd.read_sql("SELECT * FROM 절차상태", conn)
    df_all['월'] = df_all['연도'] + '-' + df_all['월']
    df_summary = df_all.groupby(['현장명', '월']).agg({
        '기성금': 'sum', '노무비': 'sum', '투입비': 'sum'
    }).reset_index()
    df_summary['손수익'] = df_summary['기성금'] - df_summary['투입비']
    df_summary['노무비비중'] = df_summary['노무비'] / df_summary['투입비'].replace(0, 1)
    st.dataframe(df_summary)
# 📌 디버깅용: 현재 절차 상태 전체 확인
if st.checkbox("🛠 디버그: 절차상태 전체 보기"):
    with sqlite3.connect(DB_PATH) as conn:
        df_debug = pd.read_sql("SELECT * FROM 절차상태", conn)
    st.dataframe(df_debug)
