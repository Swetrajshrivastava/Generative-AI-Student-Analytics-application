import os
from groq import Groq
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path, override=True)

def generate_insights(data):
    """Generate AI insights using Groq API. If API key is invalid, returns placeholder analysis."""
    groq_api_key = os.getenv("GROQ_API_KEY", "gsk_placeholder_add_your_key_here")
    
    # Check if API key is configured
    if not groq_api_key or groq_api_key == "gsk_placeholder_add_your_key_here":
        return generate_placeholder_insights(data)
    
    try:
        client = Groq(api_key=groq_api_key)
        
        prompt = f"""
        Analyze student performance and placement data:

        {data}

        Return a complete markdown report with these exact sections:
        1. Top Performers
        2. Students At Risk
        3. Placement Readiness
        4. Skill Gap Analysis
        5. Suggestions for Improvement

        The Suggestions for Improvement section is mandatory. Include at least
        8 clear action points covering academics, skills, projects, hackathons,
        placement training, and domain-specific preparation.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096
        )

        return response.choices[0].message.content
    
    except Exception as e:
        print(f"⚠️ Groq API Error: {str(e)}")
        return generate_placeholder_insights(data)


def generate_student_feedback(student_data):
    """Generate resume and interview readiness feedback for one student."""
    groq_api_key = os.getenv("GROQ_API_KEY", "gsk_placeholder_add_your_key_here")

    if not groq_api_key or groq_api_key == "gsk_placeholder_add_your_key_here":
        return generate_placeholder_student_feedback(student_data)

    try:
        client = Groq(api_key=groq_api_key)

        prompt = f"""
        You are a placement mentor and resume reviewer.

        Analyze this student's profile:
        {student_data}

        Return a complete markdown report with these exact sections:
        1. Resume Strengths
        2. Resume Improvement Tips
        3. Missing Skills
        4. Interview Readiness Score
        5. Interview Preparation Plan
        6. Project Improvement Ideas
        7. Final Action Plan

        Make the feedback specific to the student's domain, skills, CGPA,
        projects, hackathons, papers, and placement status. Include practical
        steps the student can complete in the next 30 days.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Groq Student Feedback Error: {str(e)}")
        return generate_placeholder_student_feedback(student_data)


def generate_placeholder_insights(data):
    """Generate placeholder insights when Groq API is not available."""
    return """
    🤖 AI Insights (Demo Mode - Add Groq API Key for Real Analysis)
    
    To enable real AI-powered insights, add your Groq API key to .env file:
    https://console.groq.com/keys
    
    Demo Analysis Summary:
    - Students are being analyzed based on CGPA, projects, and placement status
    - Top performers are identified by high CGPA and completed projects
    - At-risk students have lower CGPA and fewer projects
    - Skill gap analysis would recommend domain-specific training
    
    Note: Real AI analysis will be available once Groq API key is configured.
    """


def generate_placeholder_student_feedback(student_data):
    """Generate fallback feedback when Groq API is not available."""
    return f"""
    ## Resume and Interview Feedback Demo

    Real Groq feedback is not available right now.

    ### Resume Improvement Tips
    - Highlight CGPA, projects, hackathons, papers, and domain skills clearly.
    - Add measurable project outcomes and tools used.
    - Keep skills grouped by programming, databases, cloud, and domain tools.

    ### Missing Skills
    - Add domain-specific tools based on the selected student's target role.
    - Add one strong project that proves practical job readiness.

    ### Interview Preparation Plan
    - Revise fundamentals for the student's domain.
    - Practice project explanation and resume-based questions.
    - Solve coding/problem-solving questions daily for 30 days.

    Student data used:
    {student_data}
    """
