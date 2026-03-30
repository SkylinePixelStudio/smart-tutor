const express = require('express');
const axios = require('axios');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());

origin: '*',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  preflightContinue: false,
  optionsSuccessStatus: 204
}));
app.options('*', cors()); // Handle preflight for ALL routes

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/health', function(req, res) {
    res.json({ status: 'ok' });
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
                {
                    role: 'system',
                    content: systemPrompt
                },
                {
                    role: 'user',
                    content: message
                }
            ],
            max_tokens: 800,
            temperature: 0.7
        },
        {
            headers: {
                'Authorization': 'Bearer ' + GROQ_API_KEY,
                'Content-Type': 'application/json'
            }
        }
    )
    .then(function(response) {
        var reply = response.data.choices[0].message.content;
        console.log("Reply: " + reply.substring(0, 60));
        res.json({
            success: true,
            reply: reply
        });
    })
    .catch(function(err) {
        var errMsg = "Unknown error";
        if (err.response && err.response.data && err.response.data.error) {
            errMsg = err.response.data.error.message;
        } else if (err.message) {
            errMsg = err.message;
        }
        console.error("Error: " + errMsg);
        res.json({
            success: false,
            reply: "Error: " + errMsg
        });
    });
});

app.listen(3000, function() {
    console.log("ACAD server running at http://localhost:3000");
    console.log("Health: http://localhost:3000/health");
    console.log("HTML:   http://localhost:3000/smart-tutor-avatar-v1.html");
});
