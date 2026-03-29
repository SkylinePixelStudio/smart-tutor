import requests

r = requests.post('http://127.0.0.1:5000/generate', json={'text': 'Hello, this is a test of my cloned voice!'})
data = r.json()
print(data)

if data['success']:
    audio = requests.get(data['audio_url'])
    with open('test_output.wav', 'wb') as f:
        f.write(audio.content)
    print("Saved to test_output.wav!")