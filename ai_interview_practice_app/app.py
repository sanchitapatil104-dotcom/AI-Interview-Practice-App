import json
import os
import re
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="InterviewIQ | AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #f5f7fb; }
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1250px; }
    [data-testid="stSidebar"] { background: #101a34; }
    [data-testid="stSidebar"] * { color: #eef2ff !important; }
    .brand { font-family: 'Manrope', sans-serif; font-size: 1.45rem; font-weight: 800; color: #fff; }
    .brand span { color: #8ea7ff; }
    .side-note { color: #b8c3e2; font-size: .85rem; line-height: 1.5; }
    .hero {
        background: linear-gradient(120deg, #17264b 0%, #344fa2 65%, #6179d9 100%);
        border-radius: 22px; padding: 28px 32px; color: white; margin-bottom: 22px;
        box-shadow: 0 12px 30px rgba(31, 54, 120, .12);
    }
    .hero h1 { font-family: 'Manrope', sans-serif; font-size: 2.1rem; line-height: 1.15; margin: 0 0 10px 0; color: white; }
    .hero p { color: #e1e8ff; margin: 0; font-size: 1rem; }
    .eyebrow { text-transform: uppercase; letter-spacing: .12em; font-weight: 700; font-size: .72rem; color: #b9c9ff; margin-bottom: 9px; }
    .section-title { font-family: 'Manrope', sans-serif; font-size: 1.25rem; font-weight: 800; color: #192747; margin: 8px 0 12px 0; }
    .metric-card { background: white; border: 1px solid #e6eaf3; border-radius: 16px; padding: 17px 18px; min-height: 110px; }
    .metric-label { color: #71809e; font-size: .82rem; font-weight: 600; }
    .metric-value { color: #1b2a4b; font-family: 'Manrope', sans-serif; font-size: 1.8rem; font-weight: 800; margin-top: 5px; }
    .metric-help { color: #8591a9; font-size: .78rem; }
    .info-card { background: white; border: 1px solid #e6eaf3; border-radius: 16px; padding: 20px; }
    .tag { display: inline-block; padding: 5px 10px; border-radius: 999px; background: #e9efff; color: #344fa2; font-weight: 700; font-size: .75rem; }
    .small-muted { color: #71809e; font-size: .88rem; }
    div.stButton > button[kind="primary"] { background: #3858c8; border: 0; border-radius: 10px; font-weight: 700; min-height: 2.8rem; }
    div.stButton > button[kind="secondary"] { border-radius: 10px; min-height: 2.6rem; }
    .stTextArea textarea, .stTextInput input { border-radius: 10px; }
    div[data-testid="stForm"] { background: white; border: 1px solid #e6eaf3; padding: 18px; border-radius: 16px; }
    .footer { text-align: center; color: #8994aa; font-size: .8rem; padding: 22px 0 0; }
</style>
""", unsafe_allow_html=True)

# ---------- Session state ----------
defaults = {
    "page": "Dashboard",
    "profile": {"name": "", "role": "Data Analyst", "experience": "Student / Fresher",
                "interview_type": "Technical", "difficulty": "Beginner", "question_count": 5},
    "questions": [],
    "question_index": 0,
    "answers": [],
    "feedback": [],
    "session_started": False,
    "session_finished": False,
    "history": [],
    "last_error": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def get_api_key():
    """Read the Gemini key from Streamlit secrets or the local .env file."""
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("GEMINI_API_KEY", "")

def get_client():
    key = get_api_key()
    if not key:
        return None
    return genai.Client(api_key=key)

def call_gemini(prompt, response_schema=None):
    """Send a prompt to Gemini and return its text response."""
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Gemini API key not found. Add GEMINI_API_KEY to your .env file, then restart the app."
        )
    config = types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type="application/json" if response_schema else "text/plain",
        response_schema=response_schema,
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    return response.text or ""

def parse_json(text):
    """Parse JSON returned by the AI, including if it adds code fences."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)

def generate_questions(profile):
    prompt = f"""
You are a thoughtful interview coach. Create exactly {profile['question_count']} interview questions.
Role/domain: {profile['role']}
Candidate experience: {profile['experience']}
Interview type: {profile['interview_type']}
Difficulty: {profile['difficulty']}

Return only valid JSON as an array of objects. Each object must have:
- "question": one clear interview question
- "category": short category name
- "what_it_tests": one short sentence describing the skill being tested
- "answer_guide": 3 to 5 key points a strong answer should include
Avoid duplicate questions. Make the questions appropriate for a student or fresher when applicable.
"""
    raw = call_gemini(prompt)
    data = parse_json(raw)
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("The AI returned an unexpected question format. Please try again.")
    return data[:profile["question_count"]]

def evaluate_answer(question, answer, profile):
    prompt = f"""
You are a supportive but honest interview coach. Evaluate the candidate's answer.
Role/domain: {profile['role']}
Interview type: {profile['interview_type']}
Difficulty: {profile['difficulty']}
Question: {question['question']}
What the question tests: {question.get('what_it_tests', '')}
Suggested answer points: {question.get('answer_guide', [])}
Candidate answer: {answer}

Score the answer from 0 to 100 based on relevance, correctness, clarity, and completeness.
Do not reward length alone. If the answer is blank or extremely short, score it accordingly.
Return JSON with exactly these fields:
{{
  "score": integer,
  "verdict": "Strong" or "Good start" or "Needs improvement",
  "strengths": array of 1-3 short strings,
  "improvements": array of 1-3 short strings,
  "sample_answer": string,
  "next_tip": string
}}
Keep feedback encouraging and specific. Do not claim that this score predicts real hiring outcomes.
"""
    raw = call_gemini(prompt)
    result = parse_json(raw)
    result["score"] = max(0, min(100, int(result.get("score", 0))))
    return result

def reset_interview():
    st.session_state.questions = []
    st.session_state.question_index = 0
    st.session_state.answers = []
    st.session_state.feedback = []
    st.session_state.session_started = False
    st.session_state.session_finished = False
    st.session_state.last_error = ""

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand">Interview<span>IQ</span> 🎯</div>', unsafe_allow_html=True)
    st.markdown('<p class="side-note">Your personal AI interview practice coach.</p>', unsafe_allow_html=True)
    st.divider()
    nav = st.radio(
        "WORKSPACE",
        ["Dashboard", "Practice Interview", "Progress & Tips", "About Project"],
        index=["Dashboard", "Practice Interview", "Progress & Tips", "About Project"].index(st.session_state.page),
        label_visibility="visible",
    )
    st.session_state.page = nav
    st.divider()
    api_status = "Connected" if get_api_key() else "API key needed"
    st.markdown(f"**AI status:** {api_status}")
    st.markdown('<p class="side-note">Your answers are processed by the AI service when you request feedback. Avoid entering passwords or sensitive personal information.</p>', unsafe_allow_html=True)

# ---------- Header ----------
def hero(title, subtitle, eyebrow="AI INTERVIEW COACH"):
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )

def metric(label, value, help_text):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-help">{help_text}</div></div>',
        unsafe_allow_html=True,
    )

# ---------- Pages ----------
if st.session_state.page == "Dashboard":
    name = st.session_state.profile.get("name", "").strip()
    greeting = f"Welcome back, {name}!" if name else "Practice today. Improve tomorrow."
    hero(greeting, "Build confidence one interview question at a time. Get useful, AI-powered feedback on every answer.")
    completed = len(st.session_state.history)
    avg_score = round(sum(x["average"] for x in st.session_state.history) / completed) if completed else 0
    best_score = max((x["average"] for x in st.session_state.history), default=0)
    c1, c2, c3 = st.columns(3)
    with c1: metric("PRACTICE SESSIONS", completed, "Completed interview sessions")
    with c2: metric("AVERAGE SCORE", f"{avg_score}%" if completed else "—", "Across completed sessions")
    with c3: metric("PERSONAL BEST", f"{best_score}%" if completed else "—", "Your highest session average")
    st.markdown('<div class="section-title">Your practice workspace</div>', unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="info-card"><span class="tag">RECOMMENDED NEXT STEP</span><h3>Start a mock interview</h3><p class="small-muted">Choose your target role, select a difficulty level, and answer questions at your own pace. Your report will highlight what you did well and what to improve.</p></div>', unsafe_allow_html=True)
        if st.button("Start practising →", type="primary", use_container_width=True):
            st.session_state.page = "Practice Interview"
            st.rerun()
    with right:
        st.markdown('<div class="info-card"><h3>What you will practise</h3><p>🧠 Role-specific questions</p><p>✍️ Clear, structured answers</p><p>📊 Personalised feedback and scoring</p><p>🚀 Practical improvement tips</p></div>', unsafe_allow_html=True)
    st.markdown("")
    st.info("This is a practice tool, not a hiring assessment. AI feedback can be imperfect, so use it as guidance rather than a definitive judgement.")

elif st.session_state.page == "Practice Interview":
    hero("Your mock interview", "Set up a practice round, then answer each question in your own words.", "PRACTICE ROOM")

    with st.expander("1 · Candidate and interview settings", expanded=not st.session_state.session_started):
        p = st.session_state.profile
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Your name (optional)", value=p["name"], placeholder="e.g. Sanchita")
                role = st.selectbox("Target role / domain",
                    ["Data Analyst", "Python Developer", "AI / Machine Learning Intern",
                     "Data Scientist", "Software Developer", "Web Developer", "Cybersecurity Intern",
                     "HR / General Interview", "Custom / Other"],
                    index=["Data Analyst", "Python Developer", "AI / Machine Learning Intern",
                     "Data Scientist", "Software Developer", "Web Developer", "Cybersecurity Intern",
                     "HR / General Interview", "Custom / Other"].index(p["role"]) if p["role"] in
                     ["Data Analyst", "Python Developer", "AI / Machine Learning Intern", "Data Scientist",
                      "Software Developer", "Web Developer", "Cybersecurity Intern", "HR / General Interview", "Custom / Other"] else 0)
                experience = st.selectbox("Experience level",
                    ["Student / Fresher", "Internship experience", "1–3 years", "3+ years"],
                    index=["Student / Fresher", "Internship experience", "1–3 years", "3+ years"].index(p["experience"]))
            with col2:
                interview_type = st.selectbox("Interview type", ["Technical", "HR / Behavioural", "Mixed"],
                    index=["Technical", "HR / Behavioural", "Mixed"].index(p["interview_type"]))
                difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"],
                    index=["Beginner", "Intermediate", "Advanced"].index(p["difficulty"]))
                question_count = st.slider("Number of questions", min_value=3, max_value=8, value=int(p["question_count"]))
            submitted = st.form_submit_button("Save interview settings", use_container_width=True)
            if submitted:
                st.session_state.profile = {"name": name, "role": role, "experience": experience,
                    "interview_type": interview_type, "difficulty": difficulty, "question_count": question_count}
                st.success("Settings saved.")

    if not st.session_state.session_started and not st.session_state.session_finished:
        st.markdown('<div class="section-title">2 · Ready when you are</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><p class="small-muted">The AI will prepare fresh questions for your selected role. Make sure your Gemini API key is configured.</p></div>', unsafe_allow_html=True)
        if st.button("✨ Generate questions & start interview", type="primary", use_container_width=True):
            try:
                with st.spinner("Preparing your interview questions..."):
                    st.session_state.questions = generate_questions(st.session_state.profile)
                st.session_state.question_index = 0
                st.session_state.answers = [""] * len(st.session_state.questions)
                st.session_state.feedback = [None] * len(st.session_state.questions)
                st.session_state.session_started = True
                st.session_state.session_finished = False
                st.session_state.last_error = ""
                st.rerun()
            except Exception as e:
                st.session_state.last_error = str(e)
                st.error(f"Could not start the interview: {e}")
                st.caption("Check your API key and internet connection, then try again.")

    if st.session_state.last_error and not st.session_state.session_started:
        st.warning(st.session_state.last_error)

    if st.session_state.session_started and not st.session_state.session_finished:
        idx = st.session_state.question_index
        questions = st.session_state.questions
        q = questions[idx]
        st.progress((idx + 1) / len(questions), text=f"Question {idx + 1} of {len(questions)}")
        st.markdown(f'<div class="info-card"><span class="tag">{q.get("category", "INTERVIEW QUESTION")}</span><h3 style="color:#1b2a4b; margin-top:14px;">{q["question"]}</h3><p class="small-muted">{q.get("what_it_tests", "")}</p></div>', unsafe_allow_html=True)
        with st.form(f"answer_form_{idx}"):
            answer = st.text_area("Your answer", value=st.session_state.answers[idx],
                placeholder="Structure your answer clearly. Include an example where possible...",
                height=180, key=f"answer_text_{idx}")
            st.caption("Tip: For behavioural questions, explain the situation, your action, and the result.")
            evaluate_clicked = st.form_submit_button("Evaluate my answer", type="primary", use_container_width=True)
        if evaluate_clicked:
            st.session_state.answers[idx] = answer.strip()
            if not answer.strip():
                st.warning("Please enter an answer before requesting feedback.")
            else:
                try:
                    with st.spinner("Reviewing your answer..."):
                        result = evaluate_answer(q, answer.strip(), st.session_state.profile)
                    st.session_state.feedback[idx] = result
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not evaluate the answer: {e}")
                    st.caption("Check your API key and connection, then try again.")
        fb = st.session_state.feedback[idx]
        if fb:
            st.markdown('<div class="section-title">AI feedback</div>', unsafe_allow_html=True)
            a, b = st.columns([1, 2])
            with a:
                st.metric("Practice score", f"{fb['score']}/100", fb.get("verdict", "Feedback"))
            with b:
                st.markdown("**What went well**")
                for item in fb.get("strengths", []): st.markdown(f"- {item}")
                st.markdown("**How to improve**")
                for item in fb.get("improvements", []): st.markdown(f"- {item}")
            with st.expander("View a sample answer"):
                st.write(fb.get("sample_answer", ""))
            st.info(f"**Next tip:** {fb.get('next_tip', 'Keep practising and use specific examples.')}")
            nav1, nav2 = st.columns(2)
            with nav1:
                if idx > 0 and st.button("← Previous question", use_container_width=True):
                    st.session_state.question_index -= 1
                    st.rerun()
            with nav2:
                label = "Finish interview" if idx == len(questions) - 1 else "Next question →"
                if st.button(label, type="primary", use_container_width=True):
                    if idx < len(questions) - 1:
                        st.session_state.question_index += 1
                    else:
                        scores = [f["score"] for f in st.session_state.feedback if f]
                        average = round(sum(scores) / len(scores)) if scores else 0
                        st.session_state.history.append({
                            "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                            "role": st.session_state.profile["role"],
                            "type": st.session_state.profile["interview_type"],
                            "average": average,
                            "count": len(scores),
                        })
                        st.session_state.session_finished = True
                        st.session_state.session_started = False
                    st.rerun()
        elif idx > 0 and st.button("← Previous question", use_container_width=True):
            st.session_state.question_index -= 1
            st.rerun()

    if st.session_state.session_finished:
        scores = [f["score"] for f in st.session_state.feedback if f]
        avg = round(sum(scores) / len(scores)) if scores else 0
        hero("Interview complete!", "Review your results, reflect on the feedback, and keep building your confidence.", "SESSION REPORT")
        c1, c2, c3 = st.columns(3)
        with c1: metric("AVERAGE SCORE", f"{avg}%", "Across evaluated answers")
        with c2: metric("QUESTIONS REVIEWED", len(scores), "Answers evaluated by AI")
        with c3: metric("TARGET ROLE", st.session_state.profile["role"], "Your selected practice area")
        st.markdown('<div class="section-title">Question-by-question review</div>', unsafe_allow_html=True)
        for i, q in enumerate(st.session_state.questions):
            fb = st.session_state.feedback[i]
            with st.expander(f"Q{i+1}. {q['question']} — {fb['score']}/100" if fb else f"Q{i+1}. {q['question']} — Not evaluated"):
                st.markdown("**Your answer**")
                st.write(st.session_state.answers[i] or "No answer submitted.")
                if fb:
                    st.markdown("**Feedback**")
                    st.write(fb.get("verdict", ""))
                    st.markdown("**Sample answer**")
                    st.write(fb.get("sample_answer", ""))
        if st.button("Start a new interview", type="primary", use_container_width=True):
            reset_interview()
            st.rerun()

elif st.session_state.page == "Progress & Tips":
    hero("Progress & improvement", "Use each practice round to spot patterns and improve your answers.", "YOUR DEVELOPMENT")
    history = st.session_state.history
    if not history:
        st.markdown('<div class="info-card"><h3>Your progress will appear here</h3><p class="small-muted">Complete an interview session to see your average scores and practice history.</p></div>', unsafe_allow_html=True)
        if st.button("Go to practice room", type="primary"):
            st.session_state.page = "Practice Interview"
            st.rerun()
    else:
        st.markdown('<div class="section-title">Session history</div>', unsafe_allow_html=True)
        st.dataframe([{"Date": h["date"], "Role": h["role"], "Interview type": h["type"],
                       "Average score": f'{h["average"]}%', "Questions reviewed": h["count"]} for h in history],
                     use_container_width=True, hide_index=True)
        scores = [h["average"] for h in history]
        st.line_chart({"Average score (%)": scores}, y_label="Score", x_label="Practice session")
        st.markdown('<div class="section-title">Four ways to improve</div>', unsafe_allow_html=True)
        tips = [
            ("Be specific", "Use a real example instead of only defining a concept."),
            ("Structure your answer", "For behavioural questions, try Situation → Task → Action → Result."),
            ("Explain your reasoning", "For technical questions, explain why you chose a solution."),
            ("Review feedback", "Choose one improvement to focus on in your next practice round."),
        ]
        cols = st.columns(2)
        for i, (title, body) in enumerate(tips):
            with cols[i % 2]:
                st.markdown(f'<div class="info-card"><h4>{title}</h4><p class="small-muted">{body}</p></div>', unsafe_allow_html=True)
                st.write("")
    st.caption("Progress history is kept in the current Streamlit session. It resets when the app session is restarted.")

elif st.session_state.page == "About Project":
    hero("About InterviewIQ", "A Python-based AI application that helps students practise interviews and receive structured feedback.", "FAL MICRO-PROJECT")
    st.markdown('<div class="section-title">Project overview</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
    <p><b>Problem statement</b><br>Students may have limited access to interview practice and personalised feedback before placements.</p>
    <p><b>Proposed solution</b><br>A web application that generates role-specific interview questions, reviews submitted answers with an AI model, and provides a practice score and actionable suggestions.</p>
    <p><b>Objectives</b></p>
    <ul>
      <li>Generate questions for selected roles and difficulty levels.</li>
      <li>Provide structured, immediate feedback on written answers.</li>
      <li>Help learners identify strengths and improvement areas.</li>
      <li>Display a simple summary of practice performance.</li>
    </ul>
    <p><b>Technology stack</b><br>Python, Streamlit, Google Gemini API, python-dotenv, optional session-based history.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="section-title">How the AI is used</div>', unsafe_allow_html=True)
    st.write("The app sends the selected interview context and answer to Gemini. The model returns questions or feedback in a structured format. The app then displays that result in the interface.")
    st.warning("AI-generated questions and scores may contain mistakes or bias. Do not use this prototype to make real hiring decisions.")
    st.markdown('<div class="section-title">Suggested future enhancements</div>', unsafe_allow_html=True)
    st.markdown("- Speech-to-text and spoken-answer practice\n- Downloadable PDF report\n- Login and persistent database\n- Question bank for specific subjects\n- More detailed analytics across sessions")

st.markdown('<div class="footer">InterviewIQ · FAL Micro-Project · Built with Python and Streamlit</div>', unsafe_allow_html=True)
