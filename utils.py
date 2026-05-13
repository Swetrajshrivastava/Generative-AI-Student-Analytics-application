import streamlit as st
import requests
from config import API_URL, ADMIN_TOKEN
#Common REST API - POST / GET / PUT / PATCH / DELETE


def admin_headers():
    if not st.session_state.get("authenticated", False):
        return {}

    return {"X-Admin-Token": ADMIN_TOKEN}


# -----------------------------
# Upload CSV
# -----------------------------
def upload_csv(file):
    # REST API - POST
    upload_file = (
        file.name,
        file.getvalue(),
        file.type,
    )

    return requests.post(
        f"{API_URL}/upload",
        files={"file": upload_file},
        headers=admin_headers()
    )
# It will call backend - REST API  - URL End Point
# -----------------------------
# Get Students
# -----------------------------
def get_students():
    #REST API - GET
    return requests.get(f"{API_URL}/students")

# -----------------------------
# Add Student
# -----------------------------
def add_student(data):
    # REST API - POST
    return requests.post(f"{API_URL}/students", json=data, headers=admin_headers())

# -----------------------------
# Update Student
# -----------------------------
def update_student(student_id, data):
    return requests.put(f"{API_URL}/students/{student_id}", json=data, headers=admin_headers())

# -----------------------------
# Delete Student

def delete_student(student_id):
    return requests.delete(f"{API_URL}/students/{student_id}", headers=admin_headers())

# -----------------------------
# Delete All Students

def delete_all_students():
    return requests.delete(f"{API_URL}/students", headers=admin_headers())

# -----------------------------
# Analytics
# -----------------------------
def get_analytics():
    st.info(" Before Calling BackEnd")
    return requests.get(f"{API_URL}/analytics")

# -----------------------------
# AI Insights
# -----------------------------
def get_ai_insights():
    return requests.get(f"{API_URL}/ai-insights")


# -----------------------------
# Student Career Feedback
# -----------------------------
def get_student_career_feedback(student_id):
    return requests.get(f"{API_URL}/students/{student_id}/career-feedback")
