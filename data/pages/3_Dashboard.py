import streamlit as st
import pandas as pd
from utils import get_students, get_analytics, delete_student, delete_all_students
from auth import is_authenticated, login_form, logout_button


def csv_download(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")


st.title("PragyanAI Student Analytics Dashboard")
logout_button()

st.subheader("All Students")
res = get_students()

if res.status_code == 200:
    df = pd.DataFrame(res.json())
    if not df.empty:
        preferred_columns = [
            "id",
            "name",
            "tenth",
            "twelfth",
            "be_cgpa",
            "skills",
            "domain",
            "projects",
            "hackathons",
            "papers",
            "placed",
            "company",
            "salary",
            "company_type",
        ]
        display_columns = [column for column in preferred_columns if column in df.columns]
        df = df[display_columns]

        df["domain"] = df["domain"].fillna("Unknown").astype(str)
        df["company_type"] = df["company_type"].fillna("Unknown").astype(str)
        df["salary"] = df["salary"].fillna(0.0)
        df["be_cgpa"] = df["be_cgpa"].fillna(0.0)

        with st.expander("Filter students", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                search_query = st.text_input(
                    "Search by name or domain",
                    "",
                    key="dashboard_search_query",
                )
                placed_filter = st.selectbox(
                    "Placement status",
                    ["All", "Placed", "Not Placed"],
                    index=0,
                    key="dashboard_placed_filter",
                )

            with col2:
                domain_options = sorted(df["domain"].dropna().unique())
                selected_domains = st.multiselect(
                    "Domain",
                    options=domain_options,
                    default=domain_options,
                    key="dashboard_domain_filter",
                )

                company_type_options = sorted(df["company_type"].dropna().unique())
                selected_company_types = st.multiselect(
                    "Company Type",
                    options=company_type_options,
                    default=company_type_options,
                    key="dashboard_company_type_filter",
                )

            with col3:
                cgpa_min = float(df["be_cgpa"].min())
                cgpa_max = float(df["be_cgpa"].max())
                cgpa_range = st.slider(
                    "CGPA range",
                    min_value=0.0,
                    max_value=10.0,
                    value=(cgpa_min, cgpa_max),
                    step=0.1,
                    key="dashboard_cgpa_range",
                )

                salary_min = float(df["salary"].min())
                salary_max = float(df["salary"].max())
                salary_range = st.slider(
                    "Salary range (LPA)",
                    min_value=0.0,
                    max_value=max(salary_max, 0.0),
                    value=(salary_min, salary_max),
                    step=0.5,
                    key="dashboard_salary_range",
                )

            if st.button("Clear filters", key="dashboard_clear_filters"):
                st.session_state.dashboard_search_query = ""
                st.session_state.dashboard_placed_filter = "All"
                st.session_state.dashboard_domain_filter = domain_options
                st.session_state.dashboard_company_type_filter = company_type_options
                st.session_state.dashboard_cgpa_range = (cgpa_min, cgpa_max)
                st.session_state.dashboard_salary_range = (salary_min, salary_max)
                st.experimental_rerun()

        filtered_df = df.copy()
        if placed_filter != "All":
            filtered_df = filtered_df[filtered_df["placed"] == (placed_filter == "Placed")]

        if selected_domains:
            filtered_df = filtered_df[filtered_df["domain"].isin(selected_domains)]

        if selected_company_types:
            filtered_df = filtered_df[filtered_df["company_type"].isin(selected_company_types)]

        filtered_df = filtered_df[
            filtered_df["be_cgpa"].between(cgpa_range[0], cgpa_range[1])
            & filtered_df["salary"].between(salary_range[0], salary_range[1])
        ]

        if search_query:
            search_value = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["name"].astype(str).str.lower().str.contains(search_value)
                | filtered_df["domain"].astype(str).str.lower().str.contains(search_value)
            ]

        df = filtered_df

        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "salary": st.column_config.NumberColumn("Salary (LPA)", format="%.2f"),
                "be_cgpa": st.column_config.NumberColumn("BE CGPA", format="%.2f"),
                "tenth": st.column_config.NumberColumn("10th %", format="%.2f"),
                "twelfth": st.column_config.NumberColumn("12th %", format="%.2f"),
            },
        )
        st.download_button(
            "Download All Students CSV",
            data=csv_download(df),
            file_name="all_students.csv",
            mime="text/csv",
            key="download_all_students_csv",
        )

        if is_authenticated():
            with st.expander("Delete a student record"):
                student_map = {f"{row['id']} - {row.get('name', '')}": row["id"] for _, row in df.iterrows()}
                selected = st.selectbox("Select student to delete", list(student_map.keys()))
                student_id = student_map[selected]

                if st.button("Delete Selected Student", key="dashboard_delete_selected"):
                    delete_res = delete_student(student_id)
                    if delete_res.status_code == 200:
                        st.success("Student deleted successfully")
                        st.info("Refresh the page to see the updated student list.")
                    else:
                        st.error(f"Delete failed: {delete_res.text}")

            st.markdown("---")
            st.warning("Delete all student records will remove every row from the database.")
            if st.button("Delete All Students", key="dashboard_delete_all"):
                delete_all_res = delete_all_students()
                if delete_all_res.status_code == 200:
                    st.success(delete_all_res.json().get("message", "All students deleted"))
                    st.info("Refresh the page to see the updated table.")
                else:
                    st.error(f"Delete all failed: {delete_all_res.text}")
        else:
            with st.expander("Admin / Faculty Login for Delete Actions"):
                login_form()
            st.info("Login is required to delete student records.")
    else:
        st.write("No Student")

st.subheader("Students Analytics")

res = get_analytics()

if res.status_code == 200:
    data = res.json()

    st.subheader("Key Metrics")

    salary_summary = data.get("salary_summary", {})
    activity_summary = data.get("activity_summary", {})
    academic_trends = data.get("academic_trends", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Avg CGPA", round(data["avg_cgpa"], 2))

    with col2:
        st.metric("Placement Rate", round(data["placement_rate"], 2))

    with col3:
        st.metric("Avg Readiness Score", round(data["avg_readiness_score"], 2))

    with col4:
        st.metric("Avg Salary (LPA)", round(salary_summary.get("avg_salary", 0), 2))

    activity_col1, activity_col2, activity_col3 = st.columns(3)

    with activity_col1:
        st.metric("Avg Hackathons", round(activity_summary.get("avg_hackathons", 0), 2))

    with activity_col2:
        st.metric("Avg Papers", round(activity_summary.get("avg_papers", 0), 2))

    with activity_col3:
        st.metric("Students With Salary", salary_summary.get("students_with_salary", 0))

    summary_df = pd.DataFrame([
        {
            "avg_cgpa": data["avg_cgpa"],
            "placement_rate": data["placement_rate"],
            "avg_readiness_score": data["avg_readiness_score"],
            "avg_salary": salary_summary.get("avg_salary", 0),
            "min_salary": salary_summary.get("min_salary", 0),
            "max_salary": salary_summary.get("max_salary", 0),
            "students_with_salary": salary_summary.get("students_with_salary", 0),
            "avg_projects": activity_summary.get("avg_projects", 0),
            "avg_hackathons": activity_summary.get("avg_hackathons", 0),
            "avg_papers": activity_summary.get("avg_papers", 0),
            "avg_tenth": academic_trends.get("avg_tenth", 0),
            "avg_twelfth": academic_trends.get("avg_twelfth", 0),
            "avg_be_cgpa": academic_trends.get("avg_be_cgpa", 0),
        }
    ])

    st.download_button(
        "Download Analytics Summary CSV",
        data=csv_download(summary_df),
        file_name="analytics_summary.csv",
        mime="text/csv",
        key="download_analytics_summary_csv",
    )

    st.subheader("Visual Analytics")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        placement_df = pd.DataFrame(data.get("placement_summary", []))
        if not placement_df.empty:
            st.markdown("Placement Status")
            st.bar_chart(placement_df, x="status", y="count")

    with chart_col2:
        cgpa_dist_df = pd.DataFrame(data.get("cgpa_distribution", []))
        if not cgpa_dist_df.empty:
            st.markdown("CGPA Distribution")
            st.bar_chart(cgpa_dist_df, x="cgpa_range", y="count")

    domain_df = pd.DataFrame(data.get("domain_performance", []))
    if not domain_df.empty:
        st.markdown("Domain-wise Performance")
        st.bar_chart(domain_df.set_index("domain")[["avg_cgpa", "avg_readiness_score"]])
        st.dataframe(
            domain_df,
            use_container_width=True,
            column_config={
                "avg_cgpa": st.column_config.NumberColumn("Avg CGPA", format="%.2f"),
                "placement_rate": st.column_config.NumberColumn("Placement Rate (%)", format="%.2f"),
                "avg_readiness_score": st.column_config.NumberColumn("Avg Readiness Score", format="%.2f"),
            },
        )
        st.download_button(
            "Download Domain Performance CSV",
            data=csv_download(domain_df),
            file_name="domain_performance.csv",
            mime="text/csv",
            key="download_domain_performance_csv",
        )

    company_type_df = pd.DataFrame(data.get("company_type_summary", []))
    if not company_type_df.empty:
        st.markdown("Company Type Analytics")
        st.bar_chart(company_type_df.set_index("company_type")[["avg_salary", "placement_rate"]])
        st.dataframe(
            company_type_df,
            use_container_width=True,
            column_config={
                "avg_salary": st.column_config.NumberColumn("Avg Salary (LPA)", format="%.2f"),
                "placement_rate": st.column_config.NumberColumn("Placement Rate (%)", format="%.2f"),
            },
        )
        st.download_button(
            "Download Company Type Analytics CSV",
            data=csv_download(company_type_df),
            file_name="company_type_analytics.csv",
            mime="text/csv",
            key="download_company_type_analytics_csv",
        )

    skill_df = pd.DataFrame(data.get("skill_summary", []))
    if not skill_df.empty:
        st.markdown("Top Skills")
        st.bar_chart(skill_df.set_index("skill")[["students"]])
        st.dataframe(
            skill_df,
            use_container_width=True,
            column_config={
                "placement_rate": st.column_config.NumberColumn("Placement Rate (%)", format="%.2f"),
                "avg_readiness_score": st.column_config.NumberColumn("Avg Readiness Score", format="%.2f"),
            },
        )
        st.download_button(
            "Download Skill Analytics CSV",
            data=csv_download(skill_df),
            file_name="skill_analytics.csv",
            mime="text/csv",
            key="download_skill_analytics_csv",
        )

    st.subheader("Salary Analytics")
    salary_col1, salary_col2, salary_col3 = st.columns(3)

    with salary_col1:
        st.metric("Min Salary (LPA)", round(salary_summary.get("min_salary", 0), 2))

    with salary_col2:
        st.metric("Max Salary (LPA)", round(salary_summary.get("max_salary", 0), 2))

    with salary_col3:
        st.metric("Avg Salary (LPA)", round(salary_summary.get("avg_salary", 0), 2))

    st.subheader("Academic Trends")
    academic_df = pd.DataFrame(
        [
            {"stage": "10th", "score": academic_trends.get("avg_tenth", 0)},
            {"stage": "12th", "score": academic_trends.get("avg_twelfth", 0)},
            {"stage": "BE CGPA x10", "score": academic_trends.get("avg_be_cgpa", 0) * 10},
        ]
    )
    st.bar_chart(academic_df, x="stage", y="score")
    st.metric("Avg 12th - 10th Change", round(academic_trends.get("avg_12th_minus_10th", 0), 2))

    st.subheader("Activity Leaders")
    leader_col1, leader_col2 = st.columns(2)

    with leader_col1:
        st.markdown("Top Hackathon Students")
        hackathon_df = pd.DataFrame(data.get("top_hackathon_students", []))
        st.dataframe(hackathon_df, use_container_width=True)
        if not hackathon_df.empty:
            st.download_button(
                "Download Hackathon Leaders CSV",
                data=csv_download(hackathon_df),
                file_name="top_hackathon_students.csv",
                mime="text/csv",
                key="download_hackathon_leaders_csv",
            )

    with leader_col2:
        st.markdown("Top Research Students")
        research_df = pd.DataFrame(data.get("top_research_students", []))
        st.dataframe(research_df, use_container_width=True)
        if not research_df.empty:
            st.download_button(
                "Download Research Leaders CSV",
                data=csv_download(research_df),
                file_name="top_research_students.csv",
                mime="text/csv",
                key="download_research_leaders_csv",
            )

    st.subheader("Placement Ready Students")
    ready_df = pd.DataFrame(data["placement_ready_students"])
    st.dataframe(ready_df)
    if not ready_df.empty:
        st.download_button(
            "Download Placement Ready Students CSV",
            data=csv_download(ready_df),
            file_name="placement_ready_students.csv",
            mime="text/csv",
            key="download_ready_students_csv",
        )

    st.subheader("Top Students")
    top_df = pd.DataFrame(data["top_students"])
    st.dataframe(top_df)
    if not top_df.empty:
        st.download_button(
            "Download Top Students CSV",
            data=csv_download(top_df),
            file_name="top_students.csv",
            mime="text/csv",
            key="download_top_students_csv",
        )

    st.subheader("At Risk Students")
    risk_df = pd.DataFrame(data["at_risk_students"])
    st.dataframe(risk_df)
    if not risk_df.empty:
        st.download_button(
            "Download At Risk Students CSV",
            data=csv_download(risk_df),
            file_name="at_risk_students.csv",
            mime="text/csv",
            key="download_at_risk_students_csv",
        )
else:
    st.error("Failed to fetch data")
    st.write(res.status_code)
