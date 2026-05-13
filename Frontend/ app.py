import streamlit as st
from auth import is_authenticated, login_form, logout_button


st.set_page_config(
    page_title="PragyanAI Student Analytics",
    layout="wide"
)

st.title("PragyanAI - Student Performance & Placement Analytics")

st.markdown("""
### Features:
- Upload CSV or Excel data
- Add and update students
- Analytics dashboard
- AI placement insights
- AI resume and interview feedback
- Export reports
""")

st.success("Use the sidebar to navigate")

logout_button()

if is_authenticated():
    st.info("Admin/faculty actions are unlocked for this session.")
else:
    st.info("Login is required for upload, add, update, and delete actions.")
    login_form()
