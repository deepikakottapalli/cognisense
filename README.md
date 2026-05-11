CogniSense 🧠
AI-Powered Student Burnout Early Detection System

Built at Hackverse 1.0 (2026) — Shortlisted in Top 50 / 120+ teams
🔴 Live Demo: cognisense.onrender.com
(Free tier — allow 30–60 seconds on first load)


The Problem
College students don't recognise burnout until it's already affecting their performance and mental health. By the time it's visible, it's been building for weeks. CogniSense detects it early — before it becomes a crisis.

What It Does
CogniSense is a privacy-first mental wellness platform that tracks student emotional patterns over time and surfaces early burnout signals — for both students and institutions.
Core Features:

🔥 Burnout Risk Index (BRI) — Custom 0–100 scoring algorithm built on VADER sentiment scores and keyword frequency analysis
📓 AI Journal — Daily check-in with real-time NLP sentiment analysis via Web Speech API
📅 7-Day Mood Heatmap — Visual emotional trend tracker
🤖 Ember — Real-time AI support agent
🧘 Cognitive Reframe Engine — Evidence-based reframing prompts for negative thought patterns
💨 Box Breathing Animation — CSS-only guided breathing tool
🏫 Institutional Dashboard — Anonymous BRI trends shared with rehabilitation centers only on explicit student consent
🗂️ Full Data Control — Students can view, manage, and delete every stored record


Privacy Architecture
No personal identity is ever stored. The system operates on anonymous session data. BRI trends are only shared with linked rehabilitation centers when the student explicitly opts in. Every data record is user-deletable at any time.

Tech Stack
LayerTechnologyBackendPython · FlaskNLP EngineVADER Sentiment AnalysisDatabaseSQLiteFrontendHTML · CSS · JavaScriptSpeech InputWeb Speech APIDeploymentRender

How the BRI Algorithm Works
The Burnout Risk Index (0–100) is calculated from:

Sentiment Score — VADER compound score from journal entries
Keyword Frequency — Detection of burnout-signal words (exhaustion, overwhelmed, can't focus, etc.)
Trend Weight — 7-day rolling pattern analysis

Higher scores = higher burnout risk. Scores above 65 trigger support prompts and institutional alerts (with consent).

Run Locally
bashgit clone https://github.com/deepikakottapalli/cognisense.git
cd cognisense
pip install -r requirements.txt
python app.py
App runs at http://localhost:5000

Built By
Team Kairos — Hackverse 1.0, April 2026
Deepika Ravichandra Kottapali — deepikakottapalli05@gmail.com

If you're a student or institution interested in this project, feel free to reach out.
