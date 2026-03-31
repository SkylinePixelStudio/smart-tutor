from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import requests
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

FISH_API_KEY  = os.environ.get("FISH_API_KEY", "") or os.environ.get("FISH_AUDIO_KEY", "")
FISH_VOICE_ID = os.environ.get("FISH_VOICE_ID", "8fcc581b791f496eb11d8f4daef4995c")

print("=== Smart Tutor API starting ===")
print(f"Groq configured: {bool(GROQ_API_KEY)}")
print(f"Fish configured: {bool(FISH_API_KEY)}")


def groq_chat(messages, max_tokens=800, temperature=0.7):
    r = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def cors_ok():
    r = jsonify({"status": "ok"})
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    r.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return r, 204


# ── HEALTH ────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Smart Tutor",
        "model": GROQ_MODEL,
        "groq_configured": bool(GROQ_API_KEY),
        "voice_configured": bool(FISH_API_KEY),
    })


# ── TOPICS ────────────────────────────────────────────
@app.route("/topics", methods=["GET"])
def topics():
    return jsonify({"success": True, "topics": [
        {"id": "photosynthesis",      "title": "Photosynthesis",          "subject": "Biology",      "emoji": "🌿", "grade": "Grade 8-10",  "color": "#10b981"},
        {"id": "newtons-laws",        "title": "Newton's Laws of Motion", "subject": "Physics",      "emoji": "⚡", "grade": "Grade 9-11",  "color": "#6366f1"},
        {"id": "quadratic-equations", "title": "Quadratic Equations",     "subject": "Mathematics",  "emoji": "📐", "grade": "Grade 9-10",  "color": "#06b6d4"},
        {"id": "python-basics",       "title": "Python Programming",      "subject": "Coding",       "emoji": "💻", "grade": "Grade 10-12", "color": "#8b5cf6"},
        {"id": "water-cycle",         "title": "The Water Cycle",         "subject": "Geography",    "emoji": "💧", "grade": "Grade 6-8",   "color": "#3b82f6"},
        {"id": "periodic-table",      "title": "The Periodic Table",      "subject": "Chemistry",    "emoji": "🧪", "grade": "Grade 8-10",  "color": "#ec4899"},
        {"id": "human-body",          "title": "Human Body Systems",      "subject": "Biology",      "emoji": "🫀", "grade": "Grade 7-9",   "color": "#ef4444"},
        {"id": "world-war-2",         "title": "World War II",            "subject": "History",      "emoji": "🌍", "grade": "Grade 9-12",  "color": "#f59e0b"},
        {"id": "electricity",         "title": "Electricity & Circuits",  "subject": "Physics",      "emoji": "🔋", "grade": "Grade 8-10",  "color": "#22d3ee"},
        {"id": "fractions",           "title": "Fractions & Decimals",    "subject": "Mathematics",  "emoji": "➗", "grade": "Grade 5-7",   "color": "#a78bfa"},
        {"id": "climate-change",      "title": "Climate Change",          "subject": "Environmental","emoji": "🌱", "grade": "Grade 8-12",  "color": "#34d399"},
        {"id": "shakespeare",         "title": "Shakespeare — Macbeth",   "subject": "Literature",   "emoji": "📖", "grade": "Grade 10-12", "color": "#f97316"},
    ]})


# ── GENERATE SLIDES ───────────────────────────────────
@app.route("/generate-slides", methods=["POST", "OPTIONS"])
def generate_slides():
    if request.method == "OPTIONS":
        return cors_ok()
    if not GROQ_API_KEY:
        return jsonify({"success": False, "error": "GROQ_API_KEY not set"})

    data    = request.get_json() or {}
    topic   = data.get("topic", "General Knowledge")
    subject = data.get("subject", "General")

    try:
        raw = groq_chat([
            {"role": "system", "content": (
                "You are ACAD, an expert AI tutor. Generate exactly 5 lecture slides as a JSON array. "
                "Each slide must have: title (string), emoji (single emoji), points (array of 4 strings). "
                "Output ONLY the raw JSON array — no markdown, no code fences, no explanation."
            )},
            {"role": "user", "content": f"Create 5 lecture slides for: '{topic}' (subject: {subject}). Output ONLY the JSON array."},
        ], max_tokens=1200, temperature=0.6)

        cleaned = raw.strip().strip("```").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        slides = json.loads(cleaned)
        if not isinstance(slides, list) or len(slides) == 0:
            raise ValueError("Not a list")
        return jsonify({"success": True, "data": {"slides": slides, "topic": topic}})

    except Exception as e:
        print(f"Slide gen error: {e} — using fallback")
        fallback = [
            {"title": f"Introduction to {topic}", "emoji": "📚", "points": ["Overview of this topic", "Why it matters today", "Key concepts we will cover", "What you will learn"]},
            {"title": "Core Concepts",             "emoji": "🔑", "points": ["Fundamental principles", "Key definitions and terms", "Important background knowledge", "Basic framework"]},
            {"title": "How It Works",              "emoji": "⚙️", "points": ["Step-by-step breakdown", "Underlying mechanisms", "Real-world examples", "Practical demonstrations"]},
            {"title": "Key Facts & Examples",      "emoji": "💡", "points": ["Important facts to remember", "Common misconceptions cleared", "Interesting case studies", "Real-world applications"]},
            {"title": "Summary & Review",          "emoji": "✅", "points": ["Recap of key points", "Main takeaways", "Practice questions", "Next steps for learning"]},
        ]
        return jsonify({"success": True, "data": {"slides": fallback, "topic": topic}})


# ── TEACH (slide narration) ───────────────────────────
@app.route("/teach", methods=["POST", "OPTIONS"])
def teach():
    if request.method == "OPTIONS":
        return cors_ok()
    if not GROQ_API_KEY:
        return jsonify({"success": False, "error": "GROQ_API_KEY not set"})

    data         = request.get_json() or {}
    topic        = data.get("topic", "General")
    slide_title  = data.get("slide_title", "")
    slide_points = data.get("slide_points", [])
    slide_index  = data.get("slide_index", 0)
    total_slides = data.get("total_slides", 5)
    points_text  = "\n".join(f"- {p}" for p in slide_points)

    try:
        narration = groq_chat([
            {"role": "system", "content": (
                "You are ACAD, an enthusiastic AI tutor. Narrate the slide to the student in 3-5 sentences. "
                "Be clear, friendly, and add one real-world example."
            )},
            {"role": "user", "content": (
                f"Topic: {topic}\nSlide {slide_index+1} of {total_slides}: {slide_title}\n"
                f"Points:\n{points_text}\nNarrate this slide."
            )},
        ], max_tokens=300, temperature=0.75)
        return jsonify({"success": True, "narration": narration})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ── DOUBT ─────────────────────────────────────────────
@app.route("/doubt", methods=["POST", "OPTIONS"])
def doubt():
    if request.method == "OPTIONS":
        return cors_ok()
    if not GROQ_API_KEY:
        return jsonify({"success": False, "error": "GROQ_API_KEY not set"})

    data        = request.get_json() or {}
    question    = data.get("question", "")
    topic       = data.get("topic", "General")
    slide_title = data.get("slide_title", "")
    history     = data.get("history", [])

    if not question:
        return jsonify({"success": False, "error": "No question provided"})

    messages = [{"role": "system", "content": (
        f"You are ACAD, a patient AI tutor. The student is studying '{topic}', "
        f"currently on slide: '{slide_title}'. Answer in under 100 words with a simple example."
    )}]
    for item in history[-3:]:
        messages.append({"role": "user",      "content": item.get("question", "")})
        messages.append({"role": "assistant", "content": item.get("answer", "")})
    messages.append({"role": "user", "content": question})

    try:
        answer = groq_chat(messages, max_tokens=250, temperature=0.7)
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ── CHAT ──────────────────────────────────────────────
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return cors_ok()
    if not GROQ_API_KEY:
        return jsonify({"success": False, "reply": "GROQ_API_KEY not set"})

    data    = request.get_json() or {}
    message = data.get("message", "Hello")
    subject = data.get("subject", "General")

    try:
        reply = groq_chat([
            {"role": "system", "content": (
                f"You are ACAD, an AI tutor. Subject: {subject}. "
                "Be clear, concise and student-friendly."
            )},
            {"role": "user", "content": message},
        ], max_tokens=800, temperature=0.7)
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        return jsonify({"success": False, "reply": f"Error: {str(e)}"})


# ── VOICE (Fish Audio) ────────────────────────────────
@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return cors_ok()

    data       = request.get_json() or {}
    text       = data.get("text", "Hello")
    clean_text = text.replace("**","").replace("#","").replace("*","").replace("`","").strip()[:300]

    if not FISH_API_KEY:
        return jsonify({"success": False, "reply": "FISH_API_KEY not set"}), 500

    try:
        fish_resp = requests.post(
            "https://api.fish.audio/v1/tts",
            headers={"Authorization": f"Bearer {FISH_API_KEY}", "Content-Type": "application/json"},
            json={"text": clean_text, "reference_id": FISH_VOICE_ID, "format": "mp3", "mp3_bitrate": 128},
            timeout=30,
        )
        if fish_resp.status_code != 200:
            return jsonify({"success": False, "reply": f"Fish Audio error {fish_resp.status_code}"}), 500
        return Response(fish_resp.content, status=200, mimetype="audio/mpeg",
                        headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return jsonify({"success": False, "reply": str(e)}), 500
