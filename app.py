
import sqlite3
import re
import io
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go


# =====================================
# 1. APP SETTINGS python -m streamlit run app.py
# =====================================

st.set_page_config(
    page_title="Placement Readiness Analyzer",
    page_icon="🎯",
    layout="wide"
)

DB_FILE = "placement_analyzer.db"


# =====================================
# 2. JOB ROLES AND REQUIRED SKILLS
# =====================================

ROLE_SKILLS = {
    "Python Developer": {
        "Python": ["python"],
        "SQL": ["sql", "sqlite", "mysql"],
        "Problem Solving": ["problem solving", "algorithms"],
        "Git": ["git", "github"],
        "REST API": ["rest api", "fastapi", "flask", "django"],
        "HTML/CSS": ["html", "css"],
        "Testing": ["pytest", "unittest", "testing"]
    },

    "Data Analyst": {
        "Python": ["python", "pandas", "numpy"],
        "SQL": ["sql", "mysql", "sqlite"],
        "Excel": ["excel"],
        "Statistics": ["statistics", "probability"],
        "Data Visualization": ["power bi", "tableau", "matplotlib"],
        "Data Cleaning": ["data cleaning"],
        "Communication": ["communication"]
    },

    "Full Stack Developer": {
        "HTML/CSS": ["html", "css"],
        "JavaScript": ["javascript"],
        "Frontend Framework": ["react", "angular", "vue"],
        "Backend": ["python", "node.js", "flask", "django"],
        "Database": ["sql", "mysql", "mongodb"],
        "REST API": ["rest api", "api"],
        "Git": ["git", "github"]
    },

    "Software Engineer": {
        "Programming": ["python", "java", "javascript"],
        "Data Structures": ["data structures", "arrays"],
        "Algorithms": ["algorithms", "sorting"],
        "SQL": ["sql", "mysql"],
        "Git": ["git", "github"],
        "OOP": ["object oriented", "oop", "inheritance"],
        "Problem Solving": ["problem solving", "leetcode"]
    }
}


# =====================================
# 3. CREATE DATABASE
# =====================================

def init_db():

    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            email TEXT,
            target_role TEXT,
            readiness_score INTEGER,
            matched_skills TEXT,
            missing_skills TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# =====================================
# 4. READ RESUME
# =====================================

def extract_text(file):

    name = file.name.lower()
    data = file.getvalue()

    if name.endswith(".pdf"):

        import fitz

        document = fitz.open(
            stream=data,
            filetype="pdf"
        )

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text

    elif name.endswith(".docx"):

        from docx import Document

        document = Document(io.BytesIO(data))

        text = ""

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        return text

    elif name.endswith(".txt"):

        return data.decode(
            "utf-8",
            errors="ignore"
        )

    else:

        raise ValueError("Unsupported resume format.")


# =====================================
# 5. FIND SKILLS IN RESUME
# =====================================

def find_skills(resume_text, required_skills):

    text = resume_text.lower()

    matched = []

    for skill, keywords in required_skills.items():

        for keyword in keywords:

            pattern = (
                r"(?<!\w)"
                + re.escape(keyword.lower())
                + r"(?!\w)"
            )

            if re.search(pattern, text):

                matched.append(skill)
                break

    return matched


# =====================================
# 6. CALCULATE READINESS SCORE
# =====================================

def calculate_score(matched, total):

    if total == 0:
        return 0

    return round((matched / total) * 100)


# =====================================
# 7. CREATE LEARNING ROADMAP
# =====================================

def get_roadmap(missing_skills):

    roadmap = []

    for skill in missing_skills:

        roadmap.append(
            f"Learn {skill} and practise it with a small project."
        )

    return roadmap


# =====================================
# 8. SAVE ASSESSMENT IN DATABASE
# =====================================

def save_assessment(analysis):

    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        INSERT INTO assessments (
            student_name,
            email,
            target_role,
            readiness_score,
            matched_skills,
            missing_skills,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis["name"],
        analysis["email"],
        analysis["role"],
        analysis["score"],
        ", ".join(analysis["matched"]),
        ", ".join(analysis["missing"]),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    conn.commit()
    conn.close()


# =====================================
# 9. SKILL COVERAGE DOUGHNUT CHART
# =====================================

def show_skill_chart(matched_count, missing_count, score):

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Matched Skills", "Missing Skills"],
                values=[matched_count, missing_count],
                hole=0.68,
                sort=False,
                marker=dict(
                    colors=["#55B6F5", "#555555"],
                    line=dict(
                        color="#222222",
                        width=3
                    )
                ),
                textinfo="label+value",
                textposition="outside",
                hovertemplate=(
                    "%{label}: %{value} skills"
                    "<extra></extra>"
                )
            )
        ]
    )

    fig.update_layout(
        height=370,
        showlegend=False,
        margin=dict(
            t=30,
            b=30,
            l=30,
            r=30
        ),
        annotations=[
            dict(
                text=f"<b>{score}%</b><br><span style='font-size:13px'>Coverage</span>",
                x=0.5,
                y=0.5,
                font=dict(size=25),
                showarrow=False
            )
        ]
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False}
    )


# =====================================
# 10. START APPLICATION
# =====================================

init_db()

st.title("🎯 Placement Readiness & Skill Gap Analyzer")

st.write(
    "Upload your resume to identify matching skills, "
    "missing skills and your learning roadmap."
)

tab1, tab2 = st.tabs([
    "Resume Analysis",
    "Assessment History"
])


# =====================================
# 11. RESUME ANALYSIS
# =====================================

with tab1:

    st.subheader("Student Information")

    name = st.text_input("Student Name")

    email = st.text_input("Email Address")

    role = st.selectbox(
        "Select Job Role",
        list(ROLE_SKILLS.keys())
    )

    required_skills = ROLE_SKILLS[role]

    st.subheader("Upload Resume")

    uploaded_file = st.file_uploader(
        "Choose PDF, DOCX or TXT file",
        type=["pdf", "docx", "txt"]
    )

    manual_skills = st.multiselect(
        "Select additional skills if needed",
        list(required_skills.keys())
    )

    if st.button("Analyze Resume", type="primary"):

        if not name.strip():

            st.error("Please enter your name.")

        elif not uploaded_file and not manual_skills:

            st.error("Please upload a resume or select skills.")

        else:

            try:

                resume_text = ""

                if uploaded_file:
                    resume_text = extract_text(uploaded_file)

                detected = find_skills(
                    resume_text,
                    required_skills
                )

                matched = sorted(set(detected + manual_skills))

                missing = []

                for skill in required_skills:

                    if skill not in matched:
                        missing.append(skill)

                score = calculate_score(
                    len(matched),
                    len(required_skills)
                )

                st.session_state["analysis"] = {
                    "name": name.strip(),
                    "email": email.strip(),
                    "role": role,
                    "matched": matched,
                    "missing": missing,
                    "score": score
                }

            except Exception as error:

                st.error(f"Error reading resume: {error}")


    # =================================
    # 12. DISPLAY ANALYSIS REPORT
    # =================================

    analysis = st.session_state.get("analysis")

    if analysis:

        st.divider()

        st.subheader("Placement Readiness Report")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Readiness Score",
            str(analysis["score"]) + "%"
        )

        col2.metric(
            "Matched Skills",
            len(analysis["matched"])
        )

        col3.metric(
            "Missing Skills",
            len(analysis["missing"])
        )

        # Circular skill coverage chart

        st.subheader("Skill Coverage")

        show_skill_chart(
            len(analysis["matched"]),
            len(analysis["missing"]),
            analysis["score"]
        )

        # Matched skills

        st.subheader("Matched Skills")

        if analysis["matched"]:

            for skill in analysis["matched"]:
                st.success(skill)

        else:

            st.write("No matching skills found.")

        # Missing skills

        st.subheader("Missing Skills")

        if analysis["missing"]:

            for skill in analysis["missing"]:
                st.warning(skill)

        else:

            st.success("All checklist skills matched.")

        # Learning roadmap

        st.subheader("Learning Roadmap")

        roadmap = get_roadmap(analysis["missing"])

        if roadmap:

            for step in roadmap:
                st.write("•", step)

        else:

            st.write("No missing skills. Keep practising!")

        # Save assessment

        if st.button("Save Assessment"):

            save_assessment(analysis)

            st.success("Assessment saved successfully!")


# =====================================
# 13. ASSESSMENT HISTORY
# =====================================

with tab2:

    st.subheader("Saved Assessment History")

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.execute("""
        SELECT
            student_name,
            email,
            target_role,
            readiness_score,
            matched_skills,
            missing_skills,
            created_at
        FROM assessments
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    if records:

        history = []

        for row in records:

            history.append({
                "Student": row[0],
                "Email": row[1],
                "Job Role": row[2],
                "Score": str(row[3]) + "%",
                "Matched Skills": row[4],
                "Missing Skills": row[5],
                "Date": row[6]
            })

        st.dataframe(
            history,
            width="stretch",
            hide_index=True
        )

    else:

        st.info("No saved assessments yet.")


# =====================================
# 14. FOOTER
# =====================================

st.divider()

st.caption(
    "Placement Readiness & Skill Gap Analyzer | "
    "MCA Academic Project"
)
