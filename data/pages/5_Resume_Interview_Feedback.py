import streamlit as st
import pandas as pd
from utils import get_students, get_student_career_feedback


st.title("AI Resume Interview Feedback")

res = get_students()

if res.status_code != 200:
    st.error("Failed to fetch students")
    st.stop()

students = res.json()

if not students:
    st.info("No students available")
    st.stop()

student_map = {
    f"{student['id']} - {student['name']} ({student.get('domain', 'Unknown')})": student
    for student in students
}

selected = st.selectbox("Select Student", list(student_map.keys()))
student = student_map[selected]
student_id = student["id"]

profile_columns = [
    "name",
    "be_cgpa",
    "skills",
    "domain",
    "projects",
    "hackathons",
    "papers",
    "placed",
    "company",
    "salary",
]

profile = {column: student.get(column) for column in profile_columns}

st.subheader("Student Profile")
st.dataframe(
    pd.DataFrame([profile]),
    use_container_width=True,
    column_config={
        "be_cgpa": st.column_config.NumberColumn("BE CGPA", format="%.2f"),
        "salary": st.column_config.NumberColumn("Salary (LPA)", format="%.2f"),
    },
)

if st.button("Generate Resume Interview Feedback", key="generate_career_feedback"):
    with st.spinner("Generating personalized feedback..."):
        feedback_res = get_student_career_feedback(student_id)

    if feedback_res.status_code == 200:
        feedback = feedback_res.json().get("feedback", "")
        st.success("Feedback generated")
        st.markdown(feedback)
        st.download_button(
            "Download Resume Interview Feedback TXT",
            data=feedback.encode("utf-8"),
            file_name=f"resume_interview_feedback_{student_id}.txt",
            mime="text/plain",
            key=f"download_career_feedback_txt_{student_id}",
        )
    else:
        try:
            st.error(feedback_res.json().get("detail", feedback_res.text))
        except ValueError:
            st.error(feedback_res.text)
