from flask import Flask, request, jsonify, send_from_directory
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


def generate_speech(text: str, audio_id: str):
    """Call Fish Audio TTS API and save output as WAV.
    Returns (output_path, error_message) — one of them will be None."""

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


# ── HEALTH ────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Smart Tutor running with Fish Audio + Groq',
        'voice_configured': bool(FISH_VOICE_ID),
        'api_configured': bool(FISH_API_KEY),
        'groq_configured': bool(GROQ_API_KEY),
    })


# ── CHAT (Groq) ───────────────────────────────────────────────────
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response, 204

    if not GROQ_API_KEY:
        return jsonify({'success': False, 'reply': 'GROQ_API_KEY not configured on server.'})

    data = request.get_json()
    message = data.get('message', 'Hello')
    subject = data.get('subject', 'General')

    system_prompt = (
        f"You are ACAD, an AI tutor for Academic Coaching and Development. "
        f"Teach clearly with examples. Current subject: {subject}. "
        f"Keep answers concise and student-friendly."
    )

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': GROQ_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': message},
                ],
                'max_tokens': 800,
                'temperature': 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
        print(f"Groq reply: {reply[:60]}...")
        return jsonify({'success': True, 'reply': reply})

    except requests.exceptions.HTTPError as e:
        err = e.response.json().get('error', {}).get('message', str(e))
        print(f"Groq error: {err}")
        return jsonify({'success': False, 'reply': f'Groq error: {err}'})
    except Exception as e:
        print(f"Groq exception: {e}")
        return jsonify({'success': False, 'reply': f'Error: {str(e)}'})


# ── VOICE (Fish Audio) ────────────────────────────────────────────
from flask import Response

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response, 204

    data = request.get_json()
    text = data.get('text', 'Hello')
    clean_text = (
        text.replace('**', '').replace('#', '')
            .replace('*', '').replace('`', '').strip()
    )[:300]

    print(f"Generating speech: {clean_text[:60]}...")

    try:
        fish_resp = requests.post(
            'https://api.fish.audio/v1/tts',
            headers={
                'Authorization': f'Bearer {os.environ.get("FISH_AUDIO_KEY", "")}',
                'Content-Type': 'application/json'
            },
            json={
                'text': clean_text,
                'reference_id': os.environ.get('FISH_VOICE_ID', '8fcc581b791f496eb11d8f4daef4995c'),
                'format': 'mp3',
                'mp3_bitrate': 128
            },
            timeout=30
        )

        if fish_resp.status_code != 200:
            print(f"Fish Audio error: {fish_resp.status_code} {fish_resp.text}")
            return jsonify({
                'success': False,
                'reply': f'Fish Audio TTS failed: HTTP {fish_resp.status_code}: {fish_resp.text}'
            }), 500

        return Response(
            fish_resp.content,
            status=200,
            mimetype='audio/mpeg',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Length': str(len(fish_resp.content))
            }
        )

    except Exception as e:
        print(f"Fish Audio exception: {e}")
        return jsonify({'success': False, 'reply': str(e)}), 500
