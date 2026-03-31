from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import uuid
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'voice_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Fish Audio Config ---
FISH_API_KEY  = os.environ.get("FISH_API_KEY", "")
FISH_VOICE_ID = os.environ.get("FISH_VOICE_ID", "")
FISH_API_URL  = "https://api.fish.audio/v1/tts"

# --- Groq Config ---
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL  = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL    = "llama-3.3-70b-versatile"

print("================================")
print("  Smart Tutor API - Fish Audio + Groq  ")
print("================================")

if not FISH_API_KEY:
    print("WARNING: FISH_API_KEY not set!")
if not FISH_VOICE_ID:
    print("WARNING: FISH_VOICE_ID not set!")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not set!")


def groq_chat(messages, max_tokens=800, temperature=0.7):
    """Helper: call Groq and return the reply string, or raise on error."""
    response = requests.post(
        GROQ_API_URL,
        headers={
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'model': GROQ_MODEL,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


def generate_speech(text: str, audio_id: str):
    """Call Fish Audio TTS API and save output as WAV."""
    if not FISH_API_KEY:
        return None, "FISH_API_KEY is not set"
    if not FISH_VOICE_ID:
        return None, "FISH_VOICE_ID is not set"

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model": "s1",
        "reference_id": FISH_VOICE_ID,
        "format": "wav",
        "latency": "normal",
    }
    try:
        response = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        output_path = os.path.join(OUTPUT_DIR, f"speech_{audio_id}.wav")
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path, None
    except requests.exceptions.HTTPError as e:
        msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(f"Fish Audio HTTP error: {msg}")
        return None, msg
    except Exception as e:
        print(f"Fish Audio exception: {e}")
        return None, str(e)


# ═══════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'Smart Tutor',
        'model': GROQ_MODEL,
        'message': 'Smart Tutor running with Fish Audio + Groq',
        'voice_configured': bool(FISH_VOICE_ID),
        'api_configured': bool(FISH_API_KEY),
        'groq_configured': bool(GROQ_API_KEY),
    })


# ═══════════════════════════════════════
# TOPICS  ← THIS WAS MISSING — caused the 404
# ═══════════════════════════════════════
@app.route('/topics', methods=['GET'])
def topics():
    """Return the list of available topics.
    The frontend has built-in defaults so returning [] is fine —
    it just tells the frontend to use its own default topic cards."""
    topic_list = [
        {"id": "photosynthesis",      "title": "Photosynthesis",           "subject": "Biology",      "emoji": "🌿", "grade": "Grade 8-10",  "color": "#10b981"},
        {"id": "newtons-laws",        "title": "Newton's Laws of Motion",  "subject": "Physics",      "emoji": "⚡", "grade": "Grade 9-11",  "color": "#6366f1"},
        {"id": "quadratic-equations", "title": "Quadratic Equations",      "subject": "Mathematics",  "emoji": "📐", "grade": "Grade 9-10",  "color": "#06b6d4"},
        {"id": "python-basics",       "title": "Python Programming",       "subject": "Coding",       "emoji": "💻", "grade": "Grade 10-12", "color": "#8b5cf6"},
        {"id": "water-cycle",         "title": "The Water Cycle",          "subject": "Geography",    "emoji": "💧", "grade": "Grade 6-8",   "color": "#3b82f6"},
        {"id": "periodic-table",      "title": "The Periodic Table",       "subject": "Chemistry",    "emoji": "🧪", "grade": "Grade 8-10",  "color": "#ec4899"},
        {"id": "human-body",          "title": "Human Body Systems",       "subject": "Biology",      "emoji": "🫀", "grade": "Grade 7-9",   "color": "#ef4444"},
        {"id": "world-war-2",         "title": "World War II",             "subject": "History",      "emoji": "🌍", "grade": "Grade 9-12",  "color": "#f59e0b"},
        {"id": "electricity",         "title": "Electricity & Circuits",   "subject": "Physics",      "emoji": "🔋", "grade": "Grade 8-10",  "color": "#22d3ee"},
        {"id": "fractions",           "title": "Fractions & Decimals",     "subject": "Mathematics",  "emoji": "➗", "grade": "Grade 5-7",   "color": "#a78bfa"},
        {"id": "climate-change",      "title": "Climate Change",           "subject": "Environmental","emoji": "🌱", "grade": "Grade 8-12",  "color": "#34d399"},
        {"id": "shakespeare",         "title": "Shakespeare — Macbeth",    "subject": "Literature",   "emoji": "📖", "grade": "Grade 10-12", "color": "#f97316"},
    ]
    return jsonify({'success': True, 'topics': topic_list})


# ═══════════════════════════════════════
# GENERATE SLIDES  ← WAS MISSING
# ═══════════════════════════════════════
@app.route('/generate-slides', methods=['POST', 'OPTIONS'])
def generate_slides():
    if request.method == 'OPTIONS':
        return _cors_preflight()

    if not GROQ_API_KEY:
        return jsonify({'success': False, 'error': 'GROQ_API_KEY not configured on server.'})

    data    = request.get_json() or {}
    topic   = data.get('topic', 'General Knowledge')
    subject = data.get('subject', 'General')

    system_prompt = (
        "You are ACAD, an expert AI tutor. Generate exactly 5 lecture slides as a JSON array. "
        "Each slide must have: title (string), emoji (single emoji), points (array of 4 strings). "
        "Output ONLY the raw JSON array — no markdown, no explanation, no code fences. "
        "Example format: "
        '[{"title":"Introduction","emoji":"📚","points":["Point 1","Point 2","Point 3","Point 4"]}]'
    )
    user_prompt = (
        f"Create 5 lecture slides for the topic: '{topic}' (subject: {subject}). "
        "Make the points clear, educational, and suitable for students. "
        "Output ONLY the JSON array."
    )

    try:
        raw = groq_chat(
            [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            max_tokens=1200,
            temperature=0.6,
        )

        # Strip any accidental markdown fences Groq may add
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('```')[1]
            if cleaned.startswith('json'):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        import json
        slides = json.loads(cleaned)

        # Validate basic structure
        if not isinstance(slides, list) or len(slides) == 0:
            raise ValueError("Parsed result is not a non-empty list")

        print(f"Generated {len(slides)} slides for '{topic}'")
        return jsonify({'success': True, 'data': {'slides': slides, 'topic': topic}})

    except Exception as e:
        print(f"Slide generation error: {e}")
        # Return fallback slides so the frontend can still run a lecture
        fallback = [
            {"title": f"Introduction to {topic}",  "emoji": "📚", "points": ["Overview of this topic", "Why it matters", "Key concepts we will cover", "What you will learn today"]},
            {"title": "Core Concepts",              "emoji": "🔑", "points": ["Fundamental principles", "Key definitions", "Important background", "Basic framework"]},
            {"title": "How It Works",               "emoji": "⚙️", "points": ["Step-by-step breakdown", "Underlying mechanisms", "Real-world examples", "Practical demonstrations"]},
            {"title": "Key Facts & Examples",       "emoji": "💡", "points": ["Important facts to remember", "Common misconceptions", "Interesting case studies", "Real applications"]},
            {"title": "Summary & Review",           "emoji": "✅", "points": ["Recap of key points", "Main takeaways", "Practice questions", "Next steps for learning"]},
        ]
        return jsonify({'success': True, 'data': {'slides': fallback, 'topic': topic}})


# ═══════════════════════════════════════
# TEACH (slide narration)  ← WAS MISSING
# ═══════════════════════════════════════
@app.route('/teach', methods=['POST', 'OPTIONS'])
def teach():
    if request.method == 'OPTIONS':
        return _cors_preflight()

    if not GROQ_API_KEY:
        return jsonify({'success': False, 'error': 'GROQ_API_KEY not configured on server.'})

    data         = request.get_json() or {}
    topic        = data.get('topic', 'General')
    slide_title  = data.get('slide_title', '')
    slide_points = data.get('slide_points', [])
    slide_index  = data.get('slide_index', 0)
    total_slides = data.get('total_slides', 5)

    points_text = '\n'.join(f'- {p}' for p in slide_points)
    system_prompt = (
        "You are ACAD, an enthusiastic and clear AI tutor. "
        "When given a slide, narrate it as if speaking directly to a student. "
        "Be engaging, use simple language, and explain with a brief real-world example. "
        "Keep the narration to 3-5 sentences."
    )
    user_prompt = (
        f"Topic: {topic}\n"
        f"Slide {slide_index + 1} of {total_slides}: {slide_title}\n"
        f"Points:\n{points_text}\n\n"
        "Narrate this slide to the student."
    )

    try:
        narration = groq_chat(
            [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            max_tokens=300,
            temperature=0.75,
        )
        print(f"Narrated slide {slide_index + 1}: {narration[:60]}...")
        return jsonify({'success': True, 'narration': narration})

    except Exception as e:
        print(f"Teach error: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ═══════════════════════════════════════
# DOUBT  ← WAS MISSING
# ═══════════════════════════════════════
@app.route('/doubt', methods=['POST', 'OPTIONS'])
def doubt():
    if request.method == 'OPTIONS':
        return _cors_preflight()

    if not GROQ_API_KEY:
        return jsonify({'success': False, 'error': 'GROQ_API_KEY not configured on server.'})

    data         = request.get_json() or {}
    question     = data.get('question', '')
    topic        = data.get('topic', 'General')
    slide_title  = data.get('slide_title', '')
    slide_points = data.get('slide_points', [])
    history      = data.get('history', [])   # list of {question, answer} dicts

    if not question:
        return jsonify({'success': False, 'error': 'No question provided.'})

    # Build conversation history for context
    messages = [
        {
            'role': 'system',
            'content': (
                f"You are ACAD, a patient and encouraging AI tutor. "
                f"A student is studying '{topic}' and has a doubt. "
                f"Current slide: '{slide_title}'. "
                "Answer clearly and simply. Use a short analogy or example. "
                "Keep your answer under 120 words."
            ),
        }
    ]

    # Add prior doubt exchanges so ACAD has context
    for item in history[-3:]:   # last 3 exchanges max
        messages.append({'role': 'user',      'content': item.get('question', '')})
        messages.append({'role': 'assistant', 'content': item.get('answer', '')})

    messages.append({'role': 'user', 'content': question})

    try:
        answer = groq_chat(messages, max_tokens=250, temperature=0.7)
        print(f"Doubt answered: {answer[:60]}...")
        return jsonify({'success': True, 'answer': answer})

    except Exception as e:
        print(f"Doubt error: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ═══════════════════════════════════════
# CHAT (Groq)  — unchanged from original
# ═══════════════════════════════════════
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return _cors_preflight()

    if not GROQ_API_KEY:
        return jsonify({'success': False, 'reply': 'GROQ_API_KEY not configured on server.'})

    data    = request.get_json() or {}
    message = data.get('message', 'Hello')
    subject = data.get('subject', 'General')

    system_prompt = (
        f"You are ACAD, an AI tutor for Academic Coaching and Development. "
        f"Teach clearly with examples. Current subject: {subject}. "
        f"Keep answers concise and student-friendly."
    )

    try:
        reply = groq_chat(
            [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': message},
            ],
            max_tokens=800,
            temperature=0.7,
        )
        print(f"Groq reply: {reply[:60]}...")
        return jsonify({'success': True, 'reply': reply})

    except requests.exceptions.HTTPError as e:
        err = e.response.json().get('error', {}).get('message', str(e))
        print(f"Groq error: {err}")
        return jsonify({'success': False, 'reply': f'Groq error: {err}'})
    except Exception as e:
        print(f"Groq exception: {e}")
        return jsonify({'success': False, 'reply': f'Error: {str(e)}'})


# ═══════════════════════════════════════
# VOICE / GENERATE (Fish Audio) — unchanged
# ═══════════════════════════════════════
@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        return _cors_preflight()

    data = request.get_json() or {}
    text = data.get('text', 'Hello')
    clean_text = (
        text.replace('**', '').replace('#', '')
            .replace('*', '').replace('`', '').strip()
    )[:300]

    print(f"Generating speech: {clean_text[:60]}...")

    fish_key     = os.environ.get("FISH_API_KEY") or os.environ.get("FISH_AUDIO_KEY", "")
    fish_voice   = os.environ.get("FISH_VOICE_ID", "8fcc581b791f496eb11d8f4daef4995c")

    if not fish_key:
        return jsonify({'success': False, 'reply': 'FISH_API_KEY not configured on server.'}), 500

    try:
        fish_resp = requests.post(
            'https://api.fish.audio/v1/tts',
            headers={
                'Authorization': f'Bearer {fish_key}',
                'Content-Type': 'application/json',
            },
            json={
                'text': clean_text,
                'reference_id': fish_voice,
                'format': 'mp3',
                'mp3_bitrate': 128,
            },
            timeout=30,
        )

        if fish_resp.status_code != 200:
            print(f"Fish Audio error: {fish_resp.status_code} {fish_resp.text}")
            return jsonify({
                'success': False,
                'reply': f'Fish Audio TTS failed: HTTP {fish_resp.status_code}: {fish_resp.text}',
            }), 500

        return Response(
            fish_resp.content,
            status=200,
            mimetype='audio/mpeg',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Length': str(len(fish_resp.content)),
            },
        )

    except Exception as e:
        print(f"Fish Audio exception: {e}")
        return jsonify({'success': False, 'reply': str(e)}), 500


# ═══════════════════════════════════════
# HELPER
# ═══════════════════════════════════════
def _cors_preflight():
    """Return a standard CORS preflight response."""
    resp = jsonify({'status': 'ok'})
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return resp, 204


# ═══════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
