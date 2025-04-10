import sqlite3
from contextlib import contextmanager

DB_PATH = "database.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
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
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM 절차상태
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=?
            ORDER BY 단계번호
        ''', (site, year, month, cost_type))
        return cursor.fetchall()

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

def activate_next_step(site, year, month, cost_type, current_step_no):
    month = f"{int(month):02d}"
    with get_connection() as conn:
        conn.execute('''
            UPDATE 절차상태
            SET 상태='완료'
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
        ''', (site, year, month, cost_type, current_step_no))

        conn.execute('''
            UPDATE 절차상태
            SET 상태='진행중'
            WHERE 현장명=? AND 연도=? AND 월=? AND 비용유형=? AND 단계번호=?
              AND 상태 != '완료'
        ''', (site, year, month, cost_type, current_step_no + 1))

        conn.commit()

def fetch_summary_data():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 현장명, 연도, 월,
                   SUM(기성금) AS 기성금,
                   SUM(노무비) AS 노무비,
                   SUM(투입비) AS 투입비
            FROM 절차상태
            GROUP BY 현장명, 연도, 월
            ORDER BY 현장명, 연도, 월
        ''')
        return cursor.fetchall()
