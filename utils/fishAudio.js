async function speakWithFishAudio(text) {
  const response = await fetch("https://api.fish.audio/v1/tts", {
    method: "POST",
    headers: {
      "Authorization": `Bearer YOUR_FISH_API_KEY`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text: text,
      reference_id: "8fcc581b791f496eb11d8f4daef4995c",
      format: "mp3",
      latency: "normal"
    })
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Fish Audio failed: ${response.status} - ${err}`);
  }

  const audioBlob = await response.blob();
  const audioUrl = URL.createObjectURL(audioBlob);

  const audio = new Audio(audioUrl);
  audio.play();
}

export default speakWithFishAudio;
```

6. **Scroll down** → add a commit message like:
```
   Add Fish Audio TTS utility
