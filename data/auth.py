import streamlit as st
from config import ADMIN_USERNAME, ADMIN_PASSWORD


def is_authenticated():
    return st.session_state.get("authenticated", False)


def logout_button():
    if is_authenticated():
        st.sidebar.success(f"Logged in as {st.session_state.get('username', 'admin')}")
        if st.sidebar.button("Logout", key="auth_logout"):
            st.session_state["authenticated"] = False
            st.session_state["username"] = ""
            st.rerun()


def login_form():
    st.subheader("Admin / Faculty Login")
    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")

    if st.button("Login", key="auth_login"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")


def require_login():
    logout_button()
    if not is_authenticated():
        st.warning("Admin/faculty login is required for this action.")
        login_form()
        st.stop()
