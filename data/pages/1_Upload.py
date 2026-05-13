import streamlit as st
from utils import upload_csv
from auth import require_login

st.title(" Upload Student Data")
require_login()

file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], accept_multiple_files=False)
# st.file_uploader(label, type=None, accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None, *, max_upload_size=None, disabled=False, label_visibility="visible", width="stretch")
if file:
    st.info("File ready") ## st.info / st.write -- print
    if st.button("Upload & Store"):
        with st.spinner("Uploading..."):
            res = upload_csv(file)
            if res.status_code == 200:
                st.success("Uploaded successfully ✅")
                st.json(res.json())
            else:
                try:
                    st.error(res.json().get("detail", res.text))
                except ValueError:
                    st.error(res.text)
