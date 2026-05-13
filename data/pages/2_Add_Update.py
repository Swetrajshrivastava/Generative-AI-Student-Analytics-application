import streamlit as st
from utils import add_student, get_students, update_student, delete_student
from auth import require_login

require_login()


def calculate_readiness_score(student_data):
    skill_count = len([
        skill for skill in str(student_data.get("skills", "")).split(",") if skill.strip()
    ])
    cgpa_score = min((student_data.get("be_cgpa", 0) or 0) / 10 * 40, 40)
    project_score = min((student_data.get("projects", 0) or 0) * 5, 20)
    hackathon_score = min((student_data.get("hackathons", 0) or 0) * 4, 16)
    paper_score = min((student_data.get("papers", 0) or 0) * 4, 12)
    skill_score = min(skill_count * 3, 12)

    return round(cgpa_score + project_score + hackathon_score + paper_score + skill_score, 2)


def readiness_label(score):
    if score >= 70:
        return "Strong placement readiness. Keep building practical experience."
    if score >= 50:
        return "Moderate readiness. Focus on projects, hackathons, and skills."
    return "Needs improvement. Strengthen academics and extracurricular experience."

tab1, tab2 = st.tabs(["➕ Add Student", "✏️ Update Student"])

with tab1:
    st.subheader("➕ Add Student")
    # Read Data from User
    name = st.text_input("Name", key="add_student_name")
    tenth = st.number_input("10th %", 0.0, 100.0, key="add_student_tenth")
    twelfth = st.number_input("12th %", 0.0, 100.0, key="add_student_twelfth")
    cgpa = st.number_input("BE CGPA", 0.0, 10.0, key="add_student_cgpa")
    
    skills = st.text_input("Skills", key="add_student_skills")
    domain = st.text_input("Domain", key="add_student_domain")
    
    projects = st.number_input("Projects", 0, key="add_student_projects")
    hackathons = st.number_input("Hackathons", 0, key="add_student_hackathons")
    papers = st.number_input("Papers", 0, key="add_student_papers")
    
    placed = st.checkbox("Placed", value=False, key="add_student_placed")
    # https://docs.streamlit.io/develop/api-reference/widgets
    company = st.text_input("Company", key="add_student_company")
    salary = st.number_input("Salary", 0.0, key="add_student_salary")
    
    company_type = st.selectbox(
        "Company Type",
        ["Product", "Service", "Support"],
        key="add_student_company_type"
    )

    add_data = {
        "name": name,
        "tenth": tenth,
        "twelfth": twelfth,
        "be_cgpa": cgpa,
        "skills": skills,
        "domain": domain,
        "projects": projects,
        "hackathons": hackathons,
        "papers": papers,
        "placed": placed,
        "company": company,
        "salary": salary,
        "company_type": company_type
    }

    readiness_score = calculate_readiness_score(add_data)
    st.metric("Estimated Readiness Score", readiness_score)
    st.info(readiness_label(readiness_score))
    
    if st.button("Add Student", key="add_student_button"):
        res = add_student(add_data)
    
        if res.status_code == 200:
            st.success("Student added ✅")
            st.json(res.json())
        else:
            st.error(res.text)

with tab2:
    st.subheader("✏️ Update Student")

    # Load students for dropdown
    res = get_students()
    
    if res.status_code == 200:
        students = res.json()
    
        if students:
            student_map = {f"{s['id']} - {s['name']}": s for s in students}
    
            selected = st.selectbox("Select Student", list(student_map.keys()), key="update_student_select")
            data = student_map[selected]
    
            student_id = data["id"]
    
            # Pre-filled form
            name = st.text_input("Name", value=data.get("name", ""), key=f"update_student_name_{student_id}")
            tenth = st.number_input("10th %", 0.0, 100.0, value=float(data.get("tenth", 0)), key=f"update_student_tenth_{student_id}")
            twelfth = st.number_input("12th %", 0.0, 100.0, value=float(data.get("twelfth", 0)), key=f"update_student_twelfth_{student_id}")
            cgpa = st.number_input("BE CGPA", 0.0, 10.0, value=float(data.get("be_cgpa", 0)), key=f"update_student_cgpa_{student_id}")
    
            skills = st.text_input("Skills", value=data.get("skills", ""), key=f"update_student_skills_{student_id}")
            domain = st.text_input("Domain", value=data.get("domain", ""), key=f"update_student_domain_{student_id}")
    
            projects = st.number_input("Projects", 0, value=int(data.get("projects", 0)), key=f"update_student_projects_{student_id}")
            hackathons = st.number_input("Hackathons", 0, value=int(data.get("hackathons", 0)), key=f"update_student_hackathons_{student_id}")
            papers = st.number_input("Papers", 0, value=int(data.get("papers", 0)), key=f"update_student_papers_{student_id}")
    
            placed = st.checkbox("Placed", value=data.get("placed", False), key=f"update_student_placed_{student_id}")
    
            company = st.text_input("Company", value=data.get("company", ""), key=f"update_student_company_{student_id}")
            salary = st.number_input("Salary", 0.0, value=float(data.get("salary", 0)), key=f"update_student_salary_{student_id}")
    
            company_type = st.selectbox(
                "Company Type",
                ["Product", "Service", "Support"],
                index=["Product", "Service", "Support"].index(data.get("company_type", "Product")),
                key=f"update_student_company_type_{student_id}"
            )

            update_data = {
                "name": name,
                "tenth": tenth,
                "twelfth": twelfth,
                "be_cgpa": cgpa,
                "skills": skills,
                "domain": domain,
                "projects": projects,
                "hackathons": hackathons,
                "papers": papers,
                "placed": placed,
                "company": company if company else None,
                "salary": salary if placed else None,
                "company_type": company_type if placed else None
            }

            readiness_score = calculate_readiness_score(update_data)
            st.metric("Estimated Readiness Score", readiness_score)
            st.info(readiness_label(readiness_score))

            if st.button("Update Student", key=f"update_student_button_{student_id}"):
                res = update_student(student_id, update_data)
    
                if res.status_code == 200:
                    st.success("Student updated ✅")
                    st.json(res.json())
                else:
                    st.error(res.text)

            if st.button("Delete Student", key=f"delete_student_button_{student_id}"):
                res = delete_student(student_id)
                if res.status_code == 200:
                    st.success("Student deleted ✅")
                    st.write(res.json())
                else:
                    st.error(res.text)
