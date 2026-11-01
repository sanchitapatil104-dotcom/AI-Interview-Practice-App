# InterviewIQ — AI Interview Practice App

A beginner-friendly FAL micro-project built with Python, Streamlit, and the Google Gemini API.

## Features
- Role-specific interview question generation
- Choose interview type, difficulty, experience level, and question count
- Submit written answers and get AI feedback
- Practice score, strengths, improvement suggestions, and sample answer
- Session summary and simple practice-history view
- Professional dashboard-style interface

## 1. Requirements
- Python 3.10 or newer (Python 3.11 is a good choice)
- VS Code
- Internet connection for Gemini API requests
- A Gemini API key

Get a Gemini API key from Google AI Studio:
https://aistudio.google.com/app/apikey

Keep your API key private. Do not share it in screenshots or upload it to GitHub.

## 2. Open the project in VS Code
1. Extract the ZIP file.
2. Open VS Code.
3. Select **File → Open Folder** and choose `ai_interview_practice_app`.
4. Open **Terminal → New Terminal**.

## 3. Create a virtual environment

### Windows (PowerShell or VS Code terminal)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt in VS Code and run:
```bat
.venv\Scripts\activate.bat
```

If `py` is not recognised, try `python` instead.

## 4. Install packages
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Add your Gemini API key
1. In the project folder, copy `.env.example`.
2. Rename the copy to `.env` (the filename must be exactly `.env`, not `.env.txt`).
3. Open `.env` and replace `your_gemini_api_key_here` with your real API key:
```text
GEMINI_API_KEY=your_real_key_here
```
Do not add quotes unless needed, and do not share the key.

## 6. Run the application
In the VS Code terminal, from the project folder:
```bash
streamlit run app.py
```
The terminal should show a local URL, usually:
`http://localhost:8501`

Hold **Ctrl** and click the URL, or copy it into your browser. Leave the terminal running while you use the app.

To stop the app, click the terminal and press **Ctrl+C**.

## Troubleshooting
- **`streamlit` is not recognised:** run `python -m streamlit run app.py`.
- **No API key found:** confirm `.env` is in the same folder as `app.py` and contains `GEMINI_API_KEY=...`; restart Streamlit.
- **API error / quota error:** check that your key is valid, the API is available to your account, and your usage quota has not been reached.
- **Module not found:** activate `.venv` and run `pip install -r requirements.txt`.
- **Port is in use:** run `python -m streamlit run app.py --server.port 8502`.

## Project folder
```text
ai_interview_practice_app/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── .streamlit/
    └── config.toml
```

## How the code works (simple explanation)
1. `st.set_page_config()` sets the browser page title and layout.
2. The CSS styles make the app look like a modern dashboard.
3. `st.session_state` remembers the current interview, answers, feedback, and progress while the app session is active.
4. `generate_questions()` sends the selected role and settings to Gemini and asks for questions in JSON format.
5. `evaluate_answer()` sends one question and the student's answer to Gemini and asks for structured feedback.
6. `parse_json()` converts the model's JSON text into Python data.
7. Streamlit displays the questions, feedback, scores, and progress.
8. `requirements.txt` lists the Python packages needed to run the project.


