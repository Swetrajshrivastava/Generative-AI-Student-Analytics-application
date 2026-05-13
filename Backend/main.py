## FastAPI, SQL
import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
# Basic Data Processing
import pandas as pd
import io
## File 
import models, schemas
from database import engine, SessionLocal
from groq_ai import generate_insights, generate_student_feedback

# -----------------------------
# INIT DB
# -----------------------------
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database Connected")
except Exception as e:
    print("❌ DB Error:", str(e))

# -----------------------------
# INIT APP
# -----------------------------
app = FastAPI(
    title="PragyanAI - Student Analytics API",
    version="2.0"
)
# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------
# DB DEPENDENCY
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_admin_token(x_admin_token: str | None = Header(default=None)):
    admin_token = os.getenv("ADMIN_TOKEN", "student-analytics-admin-token")

    if x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Admin authentication required")

    return True

# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def home():
    return {"message": " PragyanAI - Student Analytics API Running "}

# -----------------------------
# FILE UPLOAD
# -----------------------------
def parse_float(value, default=0.0):
    if pd.isna(value) or value == "":
        return default

    cleaned_value = (
        str(value)
        .replace(",", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("rs.", "")
        .replace("LPA", "")
        .replace("lpa", "")
        .strip()
    )

    return float(cleaned_value) if cleaned_value else default


def parse_bool(value, default=False):
    if pd.isna(value) or value == "":
        return default

    normalized_value = str(value).strip().lower()

    if normalized_value in ["true", "1", "yes", "y", "placed", "selected"]:
        return True

    if normalized_value in ["false", "0", "no", "n", "not placed", "unplaced"]:
        return False

    return default


def read_student_file(file_name, contents):
    extension = (file_name or "").lower().rsplit(".", 1)[-1]
    file_buffer = io.BytesIO(contents)

    if extension == "csv":
        return pd.read_csv(file_buffer)

    if extension in ["xlsx", "xls"]:
        return pd.read_excel(file_buffer)

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Please upload a CSV, XLSX, or XLS file."
    )


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    try:
        # Read CSV or Excel
        contents = await file.read()
        df = read_student_file(file.filename, contents)

        # Normalize headers so different CSV formats still work
        column_map = {
            "name": "name",
            "student name": "name",
            "10th %": "tenth",
            "10th": "tenth",
            "tenth": "tenth",
            "12th %": "twelfth",
            "12th": "twelfth",
            "twelfth": "twelfth",
            "be cgpa": "be_cgpa",
            "be_cgpa": "be_cgpa",
            "cgpa": "be_cgpa",
            "skills": "skills",
            "domain": "domain",
            "projects": "projects",
            "hackathons": "hackathons",
            "papers": "papers",
            "placed": "placed",
            "company": "company",
            "salary": "salary",
            "salary lpa": "salary",
            "salary (lpa)": "salary",
            "package": "salary",
            "package lpa": "salary",
            "package (lpa)": "salary",
            "ctc": "salary",
            "ctc lpa": "salary",
            "ctc (lpa)": "salary",
            "company type": "company_type",
            "company_type": "company_type",
        }

        df.columns = [column_map.get(col.strip().lower(), col.strip().lower()) for col in df.columns]

        students = []

        for _, row in df.iterrows():
            salary = parse_float(row.get("salary", 0))
            company = None if pd.isna(row.get("company")) or row.get("company") == "" else str(row.get("company"))

            student = models.Student(
                name=str(row.get("name", "") if not pd.isna(row.get("name", "")) else ""),

                tenth=parse_float(row.get("tenth", 0)),
                twelfth=parse_float(row.get("twelfth", 0)),
                be_cgpa=parse_float(row.get("be_cgpa", 0)),

                skills=str(row.get("skills", "") if not pd.isna(row.get("skills", "")) else ""),
                domain=str(row.get("domain", "") if not pd.isna(row.get("domain", "")) else ""),

                projects=int(row.get("projects", 0) or 0),
                hackathons=int(row.get("hackathons", 0) or 0),
                papers=int(row.get("papers", 0) or 0),

                placed=parse_bool(row.get("placed", ""), default=bool(company or salary > 0)),

                company=company,
                salary=salary,
                company_type=None if pd.isna(row.get("company_type")) or row.get("company_type") == "" else str(row.get("company_type")),
            )

            students.append(student)

        # Bulk insert
        db.bulk_save_objects(students)
        db.commit()

        return {
            "message": f"{len(students)} students uploaded successfully"
        }

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------
# ADD STUDENT
# -----------------------------
@app.post("/students", response_model=schemas.StudentResponse)
def add_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):

    new_student = models.Student(**student.dict())

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student

# -----------------------------
# UPDATE STUDENT
# -----------------------------
@app.put("/students/{id}")
def update_student(
    id: int,
    data: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):

    student = db.query(models.Student).filter(models.Student.id == id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, value in data.dict().items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)

    return student

# -----------------------------
# DELETE STUDENT
@app.delete("/students/{id}")
def delete_student(
    id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    student = db.query(models.Student).filter(models.Student.id == id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully"}

# -----------------------------
# DELETE ALL STUDENTS
@app.delete("/students")
def delete_all_students(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    deleted = db.query(models.Student).delete()
    db.commit()
    return {"message": f"Deleted {deleted} student(s)"}

# -----------------------------
# GET STUDENTS
# -----------------------------
@app.get("/students", response_model=list[schemas.StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()

# -----------------------------
# ANALYTICS ENGINE
# -----------------------------
def calculate_readiness_score(student):
    cgpa_score = min((student.be_cgpa or 0) / 10 * 40, 40)
    project_score = min((student.projects or 0) * 5, 20)
    hackathon_score = min((student.hackathons or 0) * 4, 16)
    paper_score = min((student.papers or 0) * 4, 12)
    skill_count = len([skill for skill in (student.skills or "").split(",") if skill.strip()])
    skill_score = min(skill_count * 3, 12)

    return round(cgpa_score + project_score + hackathon_score + paper_score + skill_score, 2)


@app.get("/analytics")
def analytics(db: Session = Depends(get_db)):

    students = db.query(models.Student).all()

    if not students:
        return {
            "avg_cgpa": 0,
            "placement_rate": 0,
            "top_students": [],
            "at_risk_students": [],
            "avg_projects": 0,
            "avg_readiness_score": 0,
            "placement_ready_students": [],
            "placement_summary": [],
            "cgpa_distribution": [],
            "domain_performance": [],
            "company_type_summary": [],
            "skill_summary": [],
            "salary_summary": {},
            "academic_trends": {},
            "activity_summary": {},
            "top_hackathon_students": [],
            "top_research_students": []
        }

    df = pd.DataFrame([
        {
            "name": s.name,
            "be_cgpa": s.be_cgpa or 0,
            "placed": "Yes" if s.placed else "No",
            "placed_value": 1 if s.placed else 0,
            "domain": s.domain or "Unknown",
            "projects": s.projects or 0,
            "hackathons": s.hackathons or 0,
            "papers": s.papers or 0,
            "salary": s.salary or 0,
            "company_type": s.company_type or "Unknown",
            "skills": s.skills or "",
            "readiness_score": calculate_readiness_score(s)
        }
        for s in students
    ])

    cgpa_bins = [0, 6, 7, 8, 9, 10]
    cgpa_labels = ["Below 6", "6-7", "7-8", "8-9", "9-10"]
    df["cgpa_range"] = pd.cut(
        df["be_cgpa"],
        bins=cgpa_bins,
        labels=cgpa_labels,
        include_lowest=True
    )

    placement_summary = (
        df["placed"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
        .to_dict(orient="records")
    )

    cgpa_distribution = (
        df["cgpa_range"]
        .value_counts(sort=False)
        .rename_axis("cgpa_range")
        .reset_index(name="count")
    )
    cgpa_distribution["cgpa_range"] = cgpa_distribution["cgpa_range"].astype(str)

    domain_performance = (
        df.groupby("domain")
        .agg(
            students=("name", "count"),
            avg_cgpa=("be_cgpa", "mean"),
            placement_rate=("placed_value", lambda values: values.mean() * 100),
            avg_readiness_score=("readiness_score", "mean")
        )
        .reset_index()
        .sort_values("students", ascending=False)
    )

    company_type_summary = (
        df.groupby("company_type")
        .agg(
            students=("name", "count"),
            avg_salary=("salary", "mean"),
            placement_rate=("placed_value", lambda values: values.mean() * 100)
        )
        .reset_index()
        .sort_values("students", ascending=False)
    )

    skill_rows = []
    for _, row in df.iterrows():
        for skill in str(row["skills"]).split(","):
            skill_name = skill.strip()
            if skill_name:
                skill_rows.append({
                    "skill": skill_name,
                    "placed_value": row["placed_value"],
                    "readiness_score": row["readiness_score"]
                })

    if skill_rows:
        skill_df = pd.DataFrame(skill_rows)
        skill_summary = (
            skill_df.groupby("skill")
            .agg(
                students=("skill", "count"),
                placement_rate=("placed_value", lambda values: values.mean() * 100),
                avg_readiness_score=("readiness_score", "mean")
            )
            .reset_index()
            .sort_values(["students", "placement_rate"], ascending=False)
            .head(15)
        )
    else:
        skill_summary = pd.DataFrame(columns=["skill", "students", "placement_rate", "avg_readiness_score"])

    placed_salary_df = df[(df["placed_value"] == 1) & (df["salary"] > 0)]
    salary_summary = {
        "avg_salary": float(placed_salary_df["salary"].mean()) if not placed_salary_df.empty else 0,
        "max_salary": float(placed_salary_df["salary"].max()) if not placed_salary_df.empty else 0,
        "min_salary": float(placed_salary_df["salary"].min()) if not placed_salary_df.empty else 0,
        "students_with_salary": int(len(placed_salary_df))
    }

    academic_trends = {
        "avg_tenth": float(pd.Series([s.tenth or 0 for s in students]).mean()),
        "avg_twelfth": float(pd.Series([s.twelfth or 0 for s in students]).mean()),
        "avg_be_cgpa": float(df["be_cgpa"].mean()),
        "avg_12th_minus_10th": float(pd.Series([(s.twelfth or 0) - (s.tenth or 0) for s in students]).mean()),
    }

    activity_summary = {
        "avg_projects": float(df["projects"].mean()),
        "avg_hackathons": float(df["hackathons"].mean()),
        "avg_papers": float(df["papers"].mean()),
        "max_projects": int(df["projects"].max()),
        "max_hackathons": int(df["hackathons"].max()),
        "max_papers": int(df["papers"].max())
    }

    return {
        "avg_cgpa": float(df["be_cgpa"].mean()),
        "placement_rate": float(df["placed_value"].mean() * 100),
        "top_students": df.sort_values("be_cgpa", ascending=False)
                          .drop(columns=["placed_value"])
                          .head(5)
                          .to_dict(orient="records"),
        "at_risk_students": df[df["be_cgpa"] < 6]
                          .drop(columns=["placed_value"])
                          .to_dict(orient="records"),
        "avg_projects": float(df["projects"].mean()),
        "avg_readiness_score": float(df["readiness_score"].mean()),
        "placement_ready_students": df[df["readiness_score"] >= 70]
                          .sort_values("readiness_score", ascending=False)
                          .drop(columns=["placed_value"])
                          .to_dict(orient="records"),
        "placement_summary": placement_summary,
        "cgpa_distribution": cgpa_distribution.to_dict(orient="records"),
        "domain_performance": domain_performance.to_dict(orient="records"),
        "company_type_summary": company_type_summary.to_dict(orient="records"),
        "skill_summary": skill_summary.to_dict(orient="records"),
        "salary_summary": salary_summary,
        "academic_trends": academic_trends,
        "activity_summary": activity_summary,
        "top_hackathon_students": df.sort_values("hackathons", ascending=False)
                          .drop(columns=["placed_value"])
                          .head(5)
                          .to_dict(orient="records"),
        "top_research_students": df.sort_values("papers", ascending=False)
                          .drop(columns=["placed_value"])
                          .head(5)
                          .to_dict(orient="records")
    }
# -----------------------------
# AI INSIGHTS
# -----------------------------
def build_ai_insight_payload(students):
    df = pd.DataFrame([
        {
            "name": s.name,
            "cgpa": s.be_cgpa or 0,
            "skills": s.skills or "",
            "domain": s.domain or "Unknown",
            "projects": s.projects or 0,
            "hackathons": s.hackathons or 0,
            "papers": s.papers or 0,
            "placed": bool(s.placed),
            "salary": s.salary or 0,
            "readiness_score": calculate_readiness_score(s)
        }
        for s in students
    ])

    skill_counts = {}
    for skills in df["skills"]:
        for skill in str(skills).split(","):
            skill_name = skill.strip()
            if skill_name:
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1

    return {
        "summary": {
            "total_students": int(len(df)),
            "average_cgpa": round(float(df["cgpa"].mean()), 2),
            "placement_rate": round(float(df["placed"].mean() * 100), 2),
            "average_projects": round(float(df["projects"].mean()), 2),
            "average_hackathons": round(float(df["hackathons"].mean()), 2),
            "average_papers": round(float(df["papers"].mean()), 2),
            "average_readiness_score": round(float(df["readiness_score"].mean()), 2),
            "average_salary_for_placed_students": round(float(df[df["placed"]]["salary"].mean()), 2),
        },
        "domain_summary": df.groupby("domain")
            .agg(
                students=("name", "count"),
                avg_cgpa=("cgpa", "mean"),
                placement_rate=("placed", lambda values: values.mean() * 100),
                avg_readiness_score=("readiness_score", "mean")
            )
            .round(2)
            .reset_index()
            .sort_values("students", ascending=False)
            .head(10)
            .to_dict(orient="records"),
        "top_skills": sorted(
            [{"skill": skill, "students": count} for skill, count in skill_counts.items()],
            key=lambda item: item["students"],
            reverse=True
        )[:15],
        "top_performers": df.sort_values("cgpa", ascending=False)
            .head(10)
            .to_dict(orient="records"),
        "at_risk_students": df[df["cgpa"] < 6]
            .sort_values("cgpa")
            .head(10)
            .to_dict(orient="records"),
        "high_readiness_students": df.sort_values("readiness_score", ascending=False)
            .head(10)
            .to_dict(orient="records"),
    }


@app.get("/ai-insights")
def ai_insights(db: Session = Depends(get_db)):

    students = db.query(models.Student).all()

    if not students:
        return {"message": "No data available"}

    data = build_ai_insight_payload(students)

    insights = generate_insights(data)

    return {"insights": insights}


@app.get("/students/{id}/career-feedback")
def student_career_feedback(id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student_data = {
        "name": student.name,
        "tenth": student.tenth,
        "twelfth": student.twelfth,
        "be_cgpa": student.be_cgpa,
        "skills": student.skills,
        "domain": student.domain,
        "projects": student.projects,
        "hackathons": student.hackathons,
        "papers": student.papers,
        "placed": student.placed,
        "company": student.company,
        "salary": student.salary,
        "company_type": student.company_type,
        "readiness_score": calculate_readiness_score(student)
    }

    feedback = generate_student_feedback(student_data)

    return {
        "student_id": id,
        "student_name": student.name,
        "feedback": feedback
    }
