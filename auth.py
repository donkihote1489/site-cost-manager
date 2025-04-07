import streamlit as st

USERS = {
    "siteuser1": {"password": "1234", "role": "현장"},
    "office1": {"password": "abcd", "role": "본사 공무팀"},
    "finance1": {"password": "pass", "role": "경영지원부"},
}

MAX_LOGIN_ATTEMPTS = 5

def login_view():
    st.sidebar.header("🔐 로그인")
    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0

    username = st.sidebar.text_input("사용자 ID")
    password = st.sidebar.text_input("비밀번호", type="password")

    if st.sidebar.button("로그인"):
        if st.session_state["login_attempts"] >= MAX_LOGIN_ATTEMPTS:
            st.sidebar.error("🚫 로그인 시도 횟수를 초과했습니다.")
            return

        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.session_state["role"] = user["role"]
            st.session_state["login_attempts"] = 0
            st.rerun()
        else:
            st.session_state["login_attempts"] += 1
            remaining = MAX_LOGIN_ATTEMPTS - st.session_state["login_attempts"]
            st.sidebar.error(f"❌ 로그인 실패. 남은 시도: {remaining}회")
            st.sidebar.write("DEBUG: role=", st.session_state.get("role"))

def check_login():
    return (
        st.session_state.get("logged_in", False)
        and "user" in st.session_state
        and "role" in st.session_state
    )
