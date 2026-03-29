FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir flask flask-cors huggingface_hub wavmark unidic-lite
RUN pip install --no-cache-dir git+https://github.com/myshell-ai/OpenVoice.git
RUN pip install --no-cache-dir git+https://github.com/myshell-ai/MeloTTS.git

COPY . .

EXPOSE 5000

CMD ["python", "openvoice_server.py"]
