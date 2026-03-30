from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import requests

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'voice_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Fish Audio Config (set these in Render Environment Variables) ────────────
FISH_API_KEY  = os.environ.get("FISH_API_KEY", "")
FISH_VOICE_ID = os.environ.get("FISH_VOICE_ID", "")
FISH_API_URL  = "https://api.fish.audio/v1/tts"
# ─────────────────────────────────────────────────────────────────────────────

print("================================")
print("  Smart Tutor API - Fish Audio  ")
print("================================")

if not FISH_API_KEY:
    print("⚠️  WARNING: FISH_API_KEY not set!")
if not FISH_VOICE_ID:
    print("⚠️  WARNING: FISH_VOICE_ID not set!")


def generate_speech(text: str, audio_id: str):
    """Call Fish Audio TTS API and save output. Returns file path or None."""
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
        "model": "s1",                          # ← required by Fish Audio
    }
    payload = {
        "text": text,
        "reference_id": FISH_VOICE_ID,          # ← your cloned voice
        "format": "mp3",
        "latency": "normal",
    }
    try:
        response = requests.post(
            FISH_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        output_path = os.path.join(OUTPUT_DIR, f"speech_{audio_id}.mp3")
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Audio saved: speech_{audio_id}.mp3")
        return output_path

    except requests.exceptions.HTTPError as e:
        print(f"❌ Fish Audio error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Smart Tutor running with Fish Audio',
        'voice_configured': bool(FISH_VOICE_ID),
        'api_configured': bool(FISH_API_KEY),
    })


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    data = request.get_json()
    text = data.get('text', 'Hello')

    # Clean markdown symbols
    clean_text = (
        text.replace('**', '')
            .replace('#', '')
            .replace('*', '')
            .replace('`', '')
            .strip()
    )

    if len(clean_text) > 300:
        clean_text = clean_text[:300]

    print(f"Generating: {clean_text[:60]}...")

    audio_id = str(uuid.uuid4())[:8]
    output_path = generate_speech(clean_text, audio_id)

    if output_path is None:
        return jsonify({
            'success': False,
            'reply': 'Fish Audio TTS failed. Check API key and Voice ID in Render environment variables.'
        })

    host = request.host_url.rstrip('/')
    audio_url = f"{host}/audio/speech_{audio_id}.mp3"
    print(f"Audio URL: {audio_url}")

    return jsonify({'success': True, 'audio_url': audio_url})


@app.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
