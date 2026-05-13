import streamlit as st
from utils import get_ai_insights

st.title(" AI Placement Insights")

st.write("Click below to analyze student data using AI")

if st.button("Generate Insights"):

    with st.spinner("Analyzing..."):

        res = get_ai_insights()

        if res.status_code == 200:

            insights = res.json().get("insights", "")

            st.success("Insights Generated ✅")

            st.markdown("### AI Student Analysis")
            st.markdown(insights)
            st.download_button(
                "Download AI Insights TXT",
                data=insights.encode("utf-8"),
                file_name="ai_student_insights.txt",
                mime="text/plain",
                key="download_ai_insights_txt",
            )

        else:
            st.error("Failed to fetch AI insights")
