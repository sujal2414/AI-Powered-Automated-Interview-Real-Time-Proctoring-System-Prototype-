# app.py (with follow-up question generation)
import os
import json
import sqlite3
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("backend")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# templates/static directories must exist
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
if not TEMPLATES_DIR.exists():
    log.error("Missing templates folder: %s", TEMPLATES_DIR)
if not STATIC_DIR.exists():
    log.error("Missing static folder: %s", STATIC_DIR)

# question bank file (create default if missing/empty)
QUESTION_BANK_FILE = BASE_DIR / "question_bank.json"
if not QUESTION_BANK_FILE.exists() or QUESTION_BANK_FILE.stat().st_size == 0:
    log.warning("question_bank.json missing or empty; creating default bank at %s", QUESTION_BANK_FILE)
    default_bank = {
        "General Aptitude": [
            "Tell me about a time you solved a difficult problem.",
            "Why do you want this position?",
            "Describe your strengths and weaknesses."
        ],
        "Computer Science": [
            "Explain the difference between a process and a thread.",
            "What is a RESTful API?",
            "Describe how a hash table works."
        ]
    }
    QUESTION_BANK_FILE.write_text(json.dumps(default_bank, indent=2), encoding="utf-8")

# load question bank
try:
    with open(QUESTION_BANK_FILE, "r", encoding="utf-8") as f:
        QUESTION_BANK = json.load(f)
except Exception as e:
    log.exception("Failed to load question bank; using small fallback in memory. Error: %s", e)
    QUESTION_BANK = {
        "General Aptitude": ["Why do you want this position?"]
    }

# DB initialization
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                subject TEXT,
                started_at TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                session_id TEXT PRIMARY KEY,
                questions_json TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question TEXT,
                answer TEXT,
                ts TEXT
            )
        ''')
        conn.commit()
    except Exception:
        log.exception("Error initializing DB")
    finally:
        try:
            conn.close()
        except Exception:
            pass

init_db()

# optional imports: question generator and face detection
try:
    from question_generator import generate_questions_for_subject
    log.info("Loaded question_generator module.")
except Exception as e:
    log.info("question_generator not available (%s). Falling back to local bank.", e)
    def generate_questions_for_subject(subject: str, n: int = 5):
        return QUESTION_BANK.get(subject, QUESTION_BANK.get("General Aptitude", []))[:n]

try:
    from face_detection import detect_face_from_base64
    log.info("Loaded face_detection module.")
except Exception as e:
    log.info("face_detection not available (%s). Using no-op.", e)
    def detect_face_from_base64(b64: str):
        return {"faces_detected": 0, "status": "no-op"}

# Optional OpenAI integration (for follow-up generation)
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")  # set this in your environment to enable LLM follow-ups
openai = None
if OPENAI_KEY:
    try:
        import openai as _openai
        _openai.api_key = OPENAI_KEY
        openai = _openai
        log.info("OpenAI library loaded; follow-up question generation enabled.")
    except Exception as e:
        log.exception("OpenAI import failed; follow-up will use fallback. Error: %s", e)
        openai = None
else:
    log.info("OPENAI_API_KEY not found in environment; follow-up generation will use fallback heuristics.")

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)

# Helper: get JSON body or form
def get_request_json_flexible():
    """Return JSON-like dict from JSON body or fallback to form fields."""
    data = {}
    try:
        j = request.get_json(silent=True)
        if isinstance(j, dict):
            return j
    except Exception:
        pass
    # fallback to form or args
    for k, v in request.form.items():
        data[k] = v
    for k, v in request.args.items():
        data.setdefault(k, v)
    return data

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        if not name or not email or not subject:
            return render_template("register.html", error="Please complete all fields.", subjects=QUESTION_BANK.keys())
        session_id = str(uuid.uuid4())
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO sessions (id,name,email,subject,started_at) VALUES (?,?,?,?,?)",
                        (session_id, name, email, subject, datetime.utcnow().isoformat()))
            conn.commit()

            # generate questions (openai fallback to local)
            try:
                qlist = generate_questions_for_subject(subject, n=5)
                if not isinstance(qlist, list) or not qlist:
                    raise ValueError("Invalid question list from generator")
            except Exception as e:
                log.info("Question generation failed: %s -- falling back", e)
                qlist = QUESTION_BANK.get(subject, QUESTION_BANK.get("General Aptitude", []))[:5]

            cur.execute("INSERT OR REPLACE INTO questions (session_id,questions_json) VALUES (?,?)",
                        (session_id, json.dumps(qlist)))
            conn.commit()
        except Exception:
            log.exception("Failed to create session")
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return redirect(url_for("interview", session_id=session_id))
    return render_template("register.html", subjects=QUESTION_BANK.keys())

@app.route("/interview/<session_id>")
def interview(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name,subject FROM sessions WHERE id=?", (session_id,))
        row = cur.fetchone()
    except Exception:
        log.exception("DB error fetching session")
        row = None
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if not row:
        return "Session not found", 404
    name, subject = row
    return render_template("interview.html", session_id=session_id, name=name, subject=subject)

@app.route("/get_question", methods=["POST"])
def get_question():
    data = get_request_json_flexible() or {}
    session_id = data.get("session_id")
    index_raw = data.get("index", 0)
    try:
        index = int(index_raw)
    except Exception:
        index = 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT questions_json FROM questions WHERE session_id=?", (session_id,))
        row = cur.fetchone()
    except Exception:
        log.exception("DB error in get_question")
        row = None
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if not row:
        return jsonify({"error": "session not found"}), 404
    try:
        qlist = json.loads(row[0])
    except Exception:
        qlist = []
    if index < 0 or index >= len(qlist):
        return jsonify({"done": True})
    return jsonify({"done": False, "question": qlist[index], "index": index, "total": len(qlist)})

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    data = get_request_json_flexible() or {}
    session_id = data.get("session_id")
    question = data.get("question", "")
    answer = data.get("answer", "")
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO answers (session_id,question,answer,ts) VALUES (?,?,?,?)",
                    (session_id, question, answer, datetime.utcnow().isoformat()))
        conn.commit()
    except Exception:
        log.exception("Failed to save answer")
        return jsonify({"ok": False, "error": "db_error"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return jsonify({"ok": True})

@app.route("/generate_followup", methods=["POST"])
def generate_followup():
    """
    Generate a single, concise follow-up question based on the candidate's answer.
    Expects JSON: { session_id, question, answer, history(optional:list of strings) }
    Returns: { ok: true, follow_up: "<text>" } or error.
    """
    data = get_request_json_flexible() or {}
    session_id = data.get("session_id")
    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()
    history = data.get("history") or []

    if not session_id or not answer:
        return jsonify({"ok": False, "error": "missing session_id or answer"}), 400

    # Build context for LLM / fallback
    # Keep prompt concise and instruct model to return a single short follow-up question.
    prompt_system = (
        "You are an expert interviewer. Generate exactly one concise, relevant follow-up question "
        "that asks for clarification, a deeper explanation, or an example based strictly on the candidate's answer. "
        "Do not produce multiple questions. Keep it short (max 25 words) and professional."
    )
    user_content = f"Previous question: {question}\n\nCandidate answer: {answer}"
    if isinstance(history, list) and history:
        # include brief history if provided
        hist_text = "\n\n".join(history[-3:])  # only last few entries
        user_content += f"\n\nRecent history:\n{hist_text}"

    follow_up_text = None

    # Try OpenAI if configured
    if openai:
        try:
            # Use the Chat Completions API if available
            # Note: choose model according to your account; "gpt-4o-mini" is used here as an example.
            response = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=60,
                temperature=0.2,
                n=1,
            )
            # Extract text safely based on API response shape
            follow_up_text = None
            if response and "choices" in response and len(response["choices"]) > 0:
                c = response["choices"][0]
                # Some SDKs return message/content
                if isinstance(c.get("message"), dict) and c["message"].get("content"):
                    follow_up_text = c["message"]["content"].strip()
                elif c.get("text"):
                    follow_up_text = c.get("text").strip()
            if follow_up_text:
                # Clean newline characters
                follow_up_text = follow_up_text.replace("\n", " ").strip()
        except Exception as e:
            log.exception("OpenAI follow-up generation failed, falling back. Error: %s", e)
            follow_up_text = None

    # Fallback heuristic generator if OpenAI not available or failed
    if not follow_up_text:
        try:
            # Simple rule-based follow-up generator:
            # - If answer contains 'because' or 'since', ask for example
            # - If answer contains technical terms, ask for explanation
            # - Otherwise, ask for clarification or example
            a = answer.lower()
            if any(word in a for word in ["because", "since", "therefore", "so that"]):
                follow_up_text = "Can you give a concrete example to illustrate that?"
            elif any(word in a for word in ["for example", "e.g.", "such as"]):
                follow_up_text = "Can you explain the steps you took in that example?"
            elif any(term in a for term in ["algorithm", "data", "model", "architecture", "thread", "process", "api", "hash"]):
                follow_up_text = "Can you explain the technical details or steps involved?"
            elif len(a.split()) < 10:
                follow_up_text = "Could you expand on that with more detail or an example?"
            else:
                follow_up_text = "Can you provide more detail or an example to illustrate your point?"
        except Exception as e:
            log.exception("Fallback follow-up generator error: %s", e)
            follow_up_text = "Can you elaborate on that?"

    # Safety: make sure the follow-up is short and not too long
    if follow_up_text and len(follow_up_text) > 200:
        follow_up_text = follow_up_text[:197].rsplit(" ", 1)[0] + "..."

    # Log the follow-up generation attempt
    log.info("Follow-up generated for session %s: %s", session_id, follow_up_text)

    return jsonify({"ok": True, "follow_up": follow_up_text})


@app.route("/proctor", methods=["POST"])
def proctor():
    # accepts form-data snapshot_b64 (data URL) and session_id
    session_id = request.form.get("session_id", "unknown")
    img_b64 = request.form.get("snapshot_b64")
    if not img_b64:
        return jsonify({"error": "no image"}), 400
    import re, base64
    m = re.search(r"data:image/.+;base64,(.+)", img_b64)
    if not m:
        return jsonify({"error": "bad image data"}), 400
    b64_raw = m.group(1)
    try:
        b = base64.b64decode(b64_raw)
        filename = f"{session_id}_{int(time.time())}.jpg"
        path = UPLOAD_DIR / filename
        with open(path, "wb") as f:
            f.write(b)
    except Exception as e:
        log.exception("Failed to save snapshot")
        return jsonify({"error": f"save_failed: {e}"}), 500

    try:
        analysis = detect_face_from_base64(b64_raw)
    except Exception as e:
        log.exception("Face detection error")
        analysis = {"error": str(e)}
    return jsonify({"saved": str(filename), "analysis": analysis})

@app.route("/dashboard")
def dashboard():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id,name,email,subject,started_at FROM sessions ORDER BY started_at DESC")
        sessions = cur.fetchall()
        cur.execute("SELECT session_id, question, answer, ts FROM answers ORDER BY ts DESC LIMIT 200")
        answers = cur.fetchall()
    except Exception:
        log.exception("DB error loading dashboard")
        sessions, answers = [], []
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return render_template("dashboard.html", sessions=sessions, answers=answers)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    log.info("Starting Flask app on http://0.0.0.0:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
