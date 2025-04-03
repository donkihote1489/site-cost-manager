# main.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="현장비용 분석", layout="wide")
st.title("🏗️ 전문건설 현장비용 관리 시스템")

DB_PATH = 'database.db'

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

# 데이터 삭제
def delete_data(조건):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM 비용데이터", conn)
        df = df[~조건(df)]
        df.to_sql('비용데이터', conn, index=False, if_exists='replace')

# 데이터 불러오기
def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM 비용데이터", conn)

init_db()

st.sidebar.header("📌 기본 정보 입력")
if '현장목록' not in st.session_state:
    st.session_state.현장목록 = ['화태백야', '제3연륙교']

selected_site = st.sidebar.selectbox("현장명", st.session_state.현장목록)
year = st.sidebar.text_input("연도 입력 (예: 2025)", "2025")
month = st.sidebar.selectbox("월 선택", [f"{i:02d}" for i in range(1, 13)])

selected_type = st.radio("비용 유형 선택", [
    "2. 기성금 청구 및 수금",
    "3. 노무 및 협력업체 지급 및 투입비 입력"
])

if selected_type == "2. 기성금 청구 및 수금":
    amount = st.number_input("💰 기성금 입력", min_value=0, step=100000)
    if st.button("저장하기"):
        save_data({
            '현장명': selected_site,
            '연도': year,
            '월': f"{year}-{month}",
            '비용유형': selected_type,
            '단계': "기성 확정",
            '담당팀': "현장",
            '기성금': amount,
            '노무비': 0,
            '투입비': 0
        })
        st.success("기성금 저장 완료!")

elif selected_type == "3. 노무 및 협력업체 지급 및 투입비 입력":
    labor = st.number_input("💰 노무비 입력", min_value=0, step=100000)
    input_cost = st.number_input("💰 투입비 입력", min_value=0, step=100000)
    if st.button("저장하기"):
        save_data({
            '현장명': selected_site,
            '연도': year,
            '월': f"{year}-{month}",
            '비용유형': selected_type,
            '단계': "노무 및 투입비 입력",
            '담당팀': "현장",
            '기성금': 0,
            '노무비': labor,
            '투입비': input_cost
        })
        st.success("노무비/투입비 저장 완료!")

st.markdown("---")
st.subheader("📊 월별 현황 리포트")
data = load_data()
data = data[data['현장명'] == selected_site]
if not data.empty:
    grouped = data.groupby('월').agg({
        '기성금': 'sum',
        '노무비': 'sum',
        '투입비': 'sum'
    }).reset_index()
    grouped['노무비비중'] = grouped['노무비'] / grouped['투입비'].replace(0, 1)
    grouped['손수익'] = grouped['기성금'] - grouped['투입비']

    st.dataframe(grouped)

    st.markdown("#### 📈 손수익 추이")
    fig, ax = plt.subplots()
    ax.plot(grouped['월'], grouped['손수익'], marker='o')
    ax.set_title("손수익 추이")
    st.pyplot(fig)
else:
    st.info("데이터가 없습니다. 입력을 먼저 진행해주세요.")
