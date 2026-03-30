require('dotenv').config();
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const path = require('path');
const app = express();

app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  preflightContinue: false,
  optionsSuccessStatus: 204
}));
app.options('*', cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/health', function(req, res) {
    res.json({ status: 'ok', voice_configured: true });
});

app.post('/chat', function(req, res) {
    var message = req.body.message || "Hello";
    var subject = req.body.subject || "General";
    console.log("Message: " + message);
    var systemPrompt = "You are ACAD, a smart classroom AI tutor for " + subject + ". Answer clearly and concisely for students.";
    axios.post(
        'https://api.groq.com/openai/v1/chat/completions',
        {
            model: 'llama-3.3-70b-versatile',
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: message }
            ],
            max_tokens: 800,
            temperature: 0.7
        },
        {
            headers: {
                'Authorization': 'Bearer ' + process.env.GROQ_API_KEY,
                'Content-Type': 'application/json'
            }
        }
    )
    .then(function(response) {
        var reply = response.data.choices[0].message.content;
        console.log("Reply: " + reply.substring(0, 60));
        res.json({ success: true, reply: reply });
    })
    .catch(function(err) {
        var errMsg = err.response?.data?.error?.message || err.message || "Unknown error";
        console.error("Error: " + errMsg);
        res.json({ success: false, reply: "Error: " + errMsg });
    });
});

app.post('/generate', function(req, res) {
    var text = req.body.text || '';
    console.log("Fish Audio TTS: " + text.substring(0, 60));
    axios.post(
        'https://api.fish.audio/v1/tts',
        {
            text: text,
            reference_id: '8fcc581b791f496eb11d8f4daef4995c',
            format: 'mp3',
            latency: 'normal'
        },
        {
            headers: {
                'Authorization': 'Bearer ' + process.env.FISH_API_KEY,
                'Content-Type': 'application/json'
            },
            responseType: 'arraybuffer'
        }
    )
    .then(function(response) {
        res.set('Content-Type', 'audio/mpeg');
        res.send(Buffer.from(response.data));
    })
    .catch(function(err) {
        var errMsg = err.response?.data?.error?.message || err.message || 'Unknown error';
        console.error("Fish Audio Error: " + errMsg);
        res.status(500).json({ error: errMsg });
    });
});

// ↓ This stays at the bottom always
const PORT = process.env.PORT || 3000;
app.listen(PORT, function() {
    console.log("ACAD server running on port " + PORT);
});
