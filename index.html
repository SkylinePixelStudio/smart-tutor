/**
 * ACAD Smart Classroom — Backend Server
 * Deploy on Render.com as a Node.js web service.
 *
 * Environment variables to set in Render dashboard:
 *   GROQ_API_KEY   — your Groq API key  (never put this in code)
 *   PORT           — set automatically by Render (don't override)
 *   FRONTEND_URL   — e.g. https://smart-tutor.acadapp.in  (for CORS)
 *
 * Endpoints:
 *   GET  /             — health check
 *   GET  /topics       — topic list
 *   POST /chat         — free-form Q&A
 *   POST /generate-slides — AI lecture slide generation
 *   POST /teach        — slide narration
 *   POST /doubt        — doubt Q&A
 */

const express  = require('express');
const cors     = require('cors');
const fetch    = (...args) => import('node-fetch').then(({ default: f }) => f(...args));

const app  = express();
const PORT = process.env.PORT || 3000;

// ── GROQ CONFIG ─────────────────────────────────────────────────────────────
const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_MODEL   = 'llama-3.1-8b-instant';   // fastest free model

function groqKey() {
  const key = process.env.GROQ_API_KEY;
  if (!key) throw new Error('GROQ_API_KEY environment variable is not set on the server.');
  return key;
}

// ── MIDDLEWARE ───────────────────────────────────────────────────────────────
const allowedOrigins = [
  'https://smart-tutor.acadapp.in',
  'http://localhost:5500',
  'http://127.0.0.1:5500',
  'http://localhost:3000',
  // add more origins if needed
];

app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (Postman, curl, same-origin)
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin) || process.env.NODE_ENV !== 'production') {
      callback(null, true);
    } else {
      callback(new Error('CORS: origin not allowed — ' + origin));
    }
  },
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type'],
}));

app.use(express.json({ limit: '1mb' }));

// ── GROQ HELPER ──────────────────────────────────────────────────────────────
async function callGroq(systemPrompt, userMessage, maxTokens = 1024) {
  const resp = await fetch(GROQ_API_URL, {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': 'Bearer ' + groqKey(),
    },
    body: JSON.stringify({
      model:      GROQ_MODEL,
      max_tokens: maxTokens,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user',   content: userMessage  },
      ],
    }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(
      (err.error && err.error.message) || `Groq API error ${resp.status}`
    );
  }

  const data = await resp.json();
  return data.choices?.[0]?.message?.content?.trim() ?? '';
}

// ── ROUTES ───────────────────────────────────────────────────────────────────

// Health check
app.get('/', (_req, res) => {
  res.json({ status: 'ok', service: 'ACAD Backend', model: GROQ_MODEL });
});

// ── GET /topics ──────────────────────────────────────────────────────────────
app.get('/topics', (_req, res) => {
  res.json({
    success: true,
    topics: [
      { id: 'photosynthesis',      title: 'Photosynthesis',           subject: 'Biology',      emoji: '🌿', grade: 'Grade 8-10',  color: '#10b981' },
      { id: 'newtons-laws',        title: "Newton's Laws of Motion",  subject: 'Physics',      emoji: '⚡', grade: 'Grade 9-11',  color: '#6366f1' },
      { id: 'quadratic-equations', title: 'Quadratic Equations',      subject: 'Mathematics',  emoji: '📐', grade: 'Grade 9-10',  color: '#06b6d4' },
      { id: 'python-basics',       title: 'Python Programming',       subject: 'Coding',       emoji: '💻', grade: 'Grade 10-12', color: '#8b5cf6' },
      { id: 'water-cycle',         title: 'The Water Cycle',          subject: 'Geography',    emoji: '💧', grade: 'Grade 6-8',   color: '#3b82f6' },
      { id: 'periodic-table',      title: 'The Periodic Table',       subject: 'Chemistry',    emoji: '🧪', grade: 'Grade 8-10',  color: '#ec4899' },
      { id: 'human-body',          title: 'Human Body Systems',       subject: 'Biology',      emoji: '🫀', grade: 'Grade 7-9',   color: '#ef4444' },
      { id: 'world-war-2',         title: 'World War II',             subject: 'History',      emoji: '🌍', grade: 'Grade 9-12',  color: '#f59e0b' },
      { id: 'electricity',         title: 'Electricity & Circuits',   subject: 'Physics',      emoji: '🔋', grade: 'Grade 8-10',  color: '#22d3ee' },
      { id: 'fractions',           title: 'Fractions & Decimals',     subject: 'Mathematics',  emoji: '➗', grade: 'Grade 5-7',   color: '#a78bfa' },
      { id: 'climate-change',      title: 'Climate Change',           subject: 'Environmental',emoji: '🌱', grade: 'Grade 8-12',  color: '#34d399' },
      { id: 'shakespeare',         title: 'Shakespeare — Macbeth',    subject: 'Literature',   emoji: '📖', grade: 'Grade 10-12', color: '#f97316' },
    ],
  });
});

// ── POST /chat ───────────────────────────────────────────────────────────────
app.post('/chat', async (req, res) => {
  try {
    const { message, subject = 'General' } = req.body;
    if (!message || !message.trim()) {
      return res.status(400).json({ success: false, error: 'message is required' });
    }

    const system = `You are ACAD, a friendly and knowledgeable AI tutor specialising in ${subject}.
Answer student questions clearly and concisely. Use simple language suitable for school students.
Keep responses under 120 words unless a longer explanation is genuinely needed.
Never use markdown code fences in your response — plain text only.`;

    const reply = await callGroq(system, message.trim(), 400);
    res.json({ success: true, reply });
  } catch (err) {
    console.error('[/chat]', err.message);
    res.status(500).json({ success: false, error: err.message });
  }
});

// ── POST /generate-slides ────────────────────────────────────────────────────
app.post('/generate-slides', async (req, res) => {
  try {
    const { topic, subject = 'General' } = req.body;
    if (!topic) return res.status(400).json({ success: false, error: 'topic is required' });

    const system = `You are ACAD, an AI curriculum designer. 
Always respond with valid JSON only — no markdown, no explanation, no code fences.`;

    const user = `Create a 5-slide lecture on "${topic}" (subject: ${subject}) for school students.
Return ONLY a JSON array with exactly 5 objects. Each object must have:
  "title"  — short slide title (string)
  "emoji"  — one relevant emoji (string)
  "points" — array of exactly 4 concise bullet-point strings (each under 12 words)

Example structure:
[{"title":"Introduction","emoji":"📖","points":["Point 1","Point 2","Point 3","Point 4"]}]

Return the array now:`;

    const raw   = await callGroq(system, user, 1200);
    const match = raw.match(/\[[\s\S]*\]/);
    if (!match) throw new Error('Model did not return a JSON array');

    const slides = JSON.parse(match[0]);
    if (!Array.isArray(slides) || slides.length === 0) throw new Error('Empty slides array');

    res.json({ success: true, data: { slides } });
  } catch (err) {
    console.error('[/generate-slides]', err.message);
    res.status(500).json({ success: false, error: err.message });
  }
});

// ── POST /teach ──────────────────────────────────────────────────────────────
app.post('/teach', async (req, res) => {
  try {
    const {
      topic       = 'this topic',
      slide_title = '',
      slide_points = [],
      slide_index  = 0,
      total_slides = 1,
    } = req.body;

    const system = `You are ACAD, an enthusiastic and clear AI tutor.
Write narrations in a warm, engaging tone suitable for students.
No markdown. Plain prose only. Under 80 words.`;

    const user =
      `Narrate slide ${slide_index + 1} of ${total_slides} for the topic "${topic}".
Slide title: "${slide_title}"
Key points: ${slide_points.join(' | ')}
Write a short, engaging 2–3 sentence narration that introduces this slide to students.`;

    const narration = await callGroq(system, user, 200);
    res.json({ success: true, narration });
  } catch (err) {
    console.error('[/teach]', err.message);
    res.status(500).json({ success: false, error: err.message });
  }
});

// ── POST /doubt ──────────────────────────────────────────────────────────────
app.post('/doubt', async (req, res) => {
  try {
    const {
      question    = '',
      topic       = 'General',
      slide_title = '',
      slide_points = [],
      history     = [],
    } = req.body;

    if (!question.trim()) {
      return res.status(400).json({ success: false, error: 'question is required' });
    }

    // Build a short conversation history for context (last 3 pairs max)
    const historyMessages = history.slice(-3).flatMap(h => [
      { role: 'user',      content: h.question },
      { role: 'assistant', content: h.answer   },
    ]);

    const system = `You are ACAD, a patient and encouraging AI tutor.
Answer student doubts clearly in 2–4 sentences. Use simple language.
Context: topic "${topic}", current slide "${slide_title}".
Slide content: ${slide_points.join('; ')}.
No markdown. Plain text only.`;

    // For doubt we build the full messages array ourselves to include history
    const resp = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': 'Bearer ' + groqKey(),
      },
      body: JSON.stringify({
        model:      GROQ_MODEL,
        max_tokens: 350,
        messages: [
          { role: 'system', content: system },
          ...historyMessages,
          { role: 'user',   content: question.trim() },
        ],
      }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error((err.error && err.error.message) || `Groq API error ${resp.status}`);
    }

    const data   = await resp.json();
    const answer = data.choices?.[0]?.message?.content?.trim() ?? '';
    res.json({ success: true, answer });
  } catch (err) {
    console.error('[/doubt]', err.message);
    res.status(500).json({ success: false, error: err.message });
  }
});

// ── 404 catch-all ─────────────────────────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ success: false, error: 'Endpoint not found' });
});

// ── START ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`ACAD backend listening on port ${PORT}`);
  console.log(`Model: ${GROQ_MODEL}`);
  console.log(`GROQ_API_KEY set: ${!!process.env.GROQ_API_KEY}`);
});
