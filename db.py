
import sqlite3
from contextlib import contextmanager
import streamlit as st

DB_PATH = "database.db"

@contextmanager
def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        yield conn
    except sqlite3.Error as e:
        st.error(f"❌ DB 연결 오류: {e}")
        raise e
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS 절차상태 (
                현장명 TEXT, 연도 TEXT, 월 TEXT, 비용유형 TEXT,
                단계번호 INTEGER, 작업내용 TEXT, 담당부서 TEXT,
                상태 TEXT DEFAULT '진행중',
                기성금 INTEGER DEFAULT 0, 노무비 INTEGER DEFAULT 0, 투입비 INTEGER DEFAULT 0,
                PRIMARY KEY (현장명, 연도, 월, 비용유형, 단계번호)
            )
        ''')
        conn.commit()

def insert_initial_steps(site, year, month, cost_type, step_list):
    month = f"{int(month):02d}"
    with get_connection() as conn:
        for step_no, task, dept in step_list:
            conn.execute('''
                INSERT OR IGNORE INTO 절차상태
                (현장명, 연도, 월, 비용유형, 단계번호, 작업내용, 담당부서)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (site, year, month, cost_type, step_no, task, dept))
        conn.commit()

def load_procedure_steps(site, year, month, cost_type):
    month = f"{int(month):02d}"
    with get_connection() as conn:
        return conn.execute('''
            SELECT * FROM 절차상태
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=?
            ORDER BY 단계번호
        ''', (site, year, month, cost_type)).fetchall()

def update_step_status(site, year, month, cost_type, step_no, 상태, 금액컬럼=None, 금액=None):
    month = f"{int(month):02d}"
    with get_connection() as conn:
        if 금액컬럼:
            conn.execute(f'''
                UPDATE 절차상태
                SET 상태=?, {금액컬럼}=?
                WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
            ''', (상태, 금액, site, year, month, cost_type, step_no))
        else:
            conn.execute('''
                UPDATE 절차상태
                SET 상태=?
                WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
            ''', (상태, site, year, month, cost_type, step_no))
        conn.commit()

def activate_next_step(site, year, month, cost_type, step_no):
    month = f"{int(month):02d}"
    with get_connection() as conn:
        conn.execute('''
            UPDATE 절차상태
            SET 상태='완료'
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
        ''', (site, year, month, cost_type, step_no))

        conn.execute('''
            UPDATE 절차상태
            SET 상태='진행중'
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
        ''', (site, year, month, cost_type, step_no + 1))
        conn.commit()
