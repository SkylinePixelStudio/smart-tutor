from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'voice_output')
VOICE_SAMPLE = 'D:\\softwares\\ACADworkspace\\voice_sample_trimmed.wav'
os.makedirs(OUTPUT_DIR, exist_ok=True)

device = "cpu"
ckpt_converter = os.path.join(BASE_DIR, 'checkpoints_v2', 'converter')

print("Loading converter...")
tone_color_converter = ToneColorConverter(
    os.path.join(ckpt_converter, 'config.json'),
    device=device
)
tone_color_converter.load_ckpt(
    os.path.join(ckpt_converter, 'checkpoint.pth')
)

print("Extracting your voice...")
target_se, _ = se_extractor.get_se(
    VOICE_SAMPLE,
    tone_color_converter,
    vad=True
)
print("Voice extracted!")

print("Loading TTS...")
tts_model = TTS(language='EN', device=device)
speaker_ids = tts_model.hps.data.spk2id
speaker_id = speaker_ids['EN_INDIA']
print("TTS ready!")

source_se = torch.load(
    os.path.join(BASE_DIR, 'checkpoints_v2', 'base_speakers', 'ses', 'en-india.pth'),
    map_location=device
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'OpenVoice running'})

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    data = request.get_json()
    text = data.get('text', 'Hello')
    clean_text = text.replace('**', '').replace('#', '').replace('*', '').replace('`', '').strip()
    if len(clean_text) > 300:
        clean_text = clean_text[:300]

    print("Generating: " + clean_text[:60] + "...")

    try:
        audio_id = str(uuid.uuid4())[:8]
        base_file = os.path.join(OUTPUT_DIR, 'base_' + audio_id + '.wav')
        output_file = os.path.join(OUTPUT_DIR, 'speech_' + audio_id + '.wav')

        tts_model.tts_to_file(
            clean_text,
            speaker_id,
            base_file,
            speed=1.0
        )

        tone_color_converter.convert(
            audio_src_path=base_file,
            src_se=source_se,
            tgt_se=target_se,
            output_path=output_file,
            message="@MyShell"
        )

        audio_url = 'http://localhost:5000/audio/speech_' + audio_id + '.wav'
        print("Audio ready: " + audio_url)
        return jsonify({'success': True, 'audio_url': audio_url})

    except Exception as e:
        print("Error: " + str(e))
        return jsonify({'success': False, 'reply': 'Error: ' + str(e)})

@app.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    print("================================")
    print("  OpenVoice API on port 5000   ")
    print("================================")
    app.run(host='0.0.0.0', port=5000, debug=False)