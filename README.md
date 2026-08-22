# 🔍 TruthLens AI — Real-Time Misinformation & Credibility Intelligence

> **An advanced, multi-vector NLP forensic platform engineered to detect deception, political bias, sensationalist clickbait, emotional manipulation, and factual assertions in digital media.**

[![Live Web Application](https://img.shields.io/badge/Live_Demo-GitHub_Pages-blue?style=for-the-badge&logo=github)](https://dilipkumarprudhvi-a11y.github.io/truthlens/)
[![API Status](https://img.shields.io/badge/Backend_API-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://truthlens-1-ue36.onrender.com/health)
[![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 Project Overview

**TruthLens AI** is an open-access intelligence dashboard designed to combat the proliferation of synthetic misinformation, sensationalized clickbait, and algorithmic echo chambers across digital media. 

By deconstructing input text across **12 distinct forensic and linguistic vectors**, TruthLens provides journalists, researchers, educators, and everyday readers with an objective, multi-dimensional credibility score, actionable evidence tags, sentiment breakdowns, ideological stance mapping, and extracted claim summaries in sub-second inference time.

---

## 💡 Why We Built This Project

In the modern digital age, information moves faster than human verification capacity:
1. **The Infodemic Crisis**: Misleading headlines, coordinated disinformation campaigns, and fabricated stories spread up to 6 times faster on social platforms than verified reporting.
2. **Emotional & Fear Manipulation**: Deceptive articles often weaponize alarmist vocabulary and extreme negative sentiment to bypass critical human judgment.
3. **Subtle Ideological Bias**: Partisan polarization frequently disguises subjective opinion as objective fact.
4. **Attention-Economy Clickbait**: Exaggerated claims and hyperbole distort public understanding of critical scientific, political, and medical developments.

**Our Mission**: To build a transparent, multi-layered verification system that doesn't just deliver a binary "True/False" verdict, but comprehensively explains **why** a piece of content is trustworthy, questionable, or deceptive.

---

## 🛠️ How We Built It

TruthLens is architected as an asynchronous, decoupled full-stack intelligence system combining robust Python NLP pipelines with a reactive, dark-theme forensic frontend.

```
┌─────────────────────────────────────────────────────────────┐
│                    TruthLens User Interface                 │
│   (Glassmorphism Console, Radial HUD, Dynamic Stepper)      │
└──────────────────────────────┬──────────────────────────────┘
                               │  JSON API Requests
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Engine                    │
│   (Asynchronous REST Architecture, Routing, SQLite DB)       │
└───────┬──────────────────────┬──────────────────────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌─────────────────┐    ┌─────────────────┐
│ spaCy NER    │      │ Heuristic NLP   │    │ Statistical &   │
│ Pipeline     │      │ Lexicons        │    │ Readability     │
│ (Entities)   │      │ (Bias/Sentiment)│    │ Formulas        │
└──────────────┘      └─────────────────┘    └─────────────────┘
```

### 1. Backend & NLP Architecture (Python / FastAPI)
- **FastAPI Engine**: High-throughput async REST endpoints for sub-second analytical processing.
- **spaCy NLP Pipeline**: Entity extraction engine parsing named entities (`PERSON`, `ORG`, `GPE`, `LOC`) to identify real-world subjects mentioned in claims.
- **Lexical Emotion Matrix**: Multi-vector dictionary scoring system computing Positive, Negative, and Fear/Panic probabilities.
- **Ideological Stance Analyzer**: Spectrum scoring quantifying left/right partisan trigger vocabulary and stance indicators.
- **Syntactic Heuristics**: Punctuation clustering, ALL-CAPS ratios, sensationalism indices, and passive-voice detection.
- **SQLite Persistence**: Embedded relational logging maintaining audit history and real-time aggregate statistics.

### 2. Frontend Engineering (Modern Reactive UI)
- **Glassmorphism Aesthetic**: Obsidian palette (`#090d16`), subtle ambient floating glow meshes, and card hierarchy designed for high readability.
- **Dynamic Radial SVG Gauges**: Real-time ease-out count-up animation displaying credibility percentage and risk boundaries.
- **Multi-Step Processing Stepper**: Staged progress visualizer simulating live tokenization, sentiment vectoring, and bias mapping.
- **Responsive HUD**: Modular grid cards that adapt smoothly from multi-monitor desktop displays to mobile screens.
- **Failover Client**: Multi-endpoint client with automatic failover, timeout protection, and seamless local/cloud switching.

---

## 🔬 Core Functionality & Analytical Vectors

| # | Analysis Vector | Description & Diagnostic Output |
|---|---|---|
| 1 | **Credibility & Deception Index** | Composite 0–100% confidence rating categorizing content into `REAL`, `SUSPICIOUS`, or `FAKE`. |
| 2 | **Sentiment & Emotional Vectors** | Quantifies linguistic mood into Positive %, Negative %, and Fear/Alarmist % scores. |
| 3 | **Political Bias Spectrum** | Identifies partisan slant (`Left`, `Center`, `Right`) and highlights ideological buzzwords. |
| 4 | **Clickbait & Sensationalism** | Calculates clickbait severity (0–100) using exclamation density, ALL-CAPS frequency, and viral hooks. |
| 5 | **Virality & Spread Potential** | Estimates social amplification velocity by weighting deception risk, emotional volatility, and sensationalism. |
| 6 | **Readability & Complexity** | Implements the Flesch Reading Ease algorithm to calculate reading level and grade complexity. |
| 7 | **Writing Style & Syntax HUD** | Evaluates formality index, passive voice instances, direct quotations, numeric data, and URL density. |
| 8 | **Named Entity Recognition (NER)** | Color-coded entity extraction tags (`PERSON`, `ORGANIZATION`, `GEOPOLITICAL`, `LOCATION`). |
| 9 | **Factual Claims Extractor** | Parses and isolates key factual assertion statements from surrounding narrative text. |
| 10 | **Flagged Suspicious Keywords** | Highlights tokens associated with conspiracy theories, miracle claims, and deceptive patterns. |
| 11 | **Cross-Verification Network** | Simulates multi-source cross-referencing against major wire services (Reuters, AP, FactCheck). |
| 12 | **Diagnostic JSON & Export** | One-click clipboard summary sharing and complete forensic JSON audit report downloads. |

---

## 📈 Outcomes & Impact

- ⚡ **Sub-Second Latency**: Full 12-vector analysis completes in under 200ms for standard news articles.
- 🎯 **Multi-Layer Explainability**: Replaces black-box predictions with transparent, human-readable linguistic evidence.
- 🌐 **100% Open Access**: No authentication or paywall required, empowering public digital literacy.
- 📱 **Cross-Platform Compatibility**: Fully responsive across desktop browsers, tablets, and smartphones.

---

## 📁 Repository Structure

```
truthlens/
├── backend/
│   ├── main.py              ← Core FastAPI application & NLP pipelines
│   ├── requirements.txt     ← Python backend dependencies
│   ├── Dockerfile           ← Production container configuration
│   └── static/              ← Production frontend static assets
│       ├── index.html       ← Main dashboard interface
│       ├── style.css        ← Theme, layout & keyframe animations
│       ├── app.js           ← Frontend application logic & failover
│       └── config.js        ← API endpoint configuration
├── frontend/                ← Static mirror for standalone hosting
├── index.html               ← Root entry point for GitHub Pages
├── style.css                ← Root stylesheet
├── app.js                   ← Root application script
├── config.js                ← Root configuration script
├── vercel.json              ← Vercel deployment configuration
├── docker-compose.yml       ← Docker multi-service definition
├── start.bat                ← Windows quick-launch script
├── start.sh                 ← Unix/macOS quick-launch script
└── README.md                ← Project documentation
```

---

## ⚡ Quick Start (Local Setup)

### Prerequisites
- **Python 3.9+** installed on your system.

### 1. Clone the Repository
```bash
git clone https://github.com/dilipkumarprudhvi-a11y/truthlens.git
cd truthlens
```

### 2. Install Dependencies & Run Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### 3. Open the Application
Navigate to **`http://localhost:8000`** in your browser to launch the dashboard.

---

## 📡 REST API Reference

### `POST /analyze`
Analyzes input text across all 12 forensic models.

**Request Body:**
```json
{
  "text": "Breaking news: Scientists discover clean energy breakthrough in renewable solar tech."
}
```

**Response (Sample):**
```json
{
  "text_length": 11,
  "credibility_score": 92,
  "fake_probability": 8,
  "confidence": 92,
  "classification": "REAL",
  "message": "Content appears credible following standard journalistic structures.",
  "sentiment": {
    "tone": "Positive",
    "positive_pct": 75,
    "negative_pct": 10,
    "fear_pct": 5
  },
  "bias": {
    "leaning": "Center / Neutral",
    "left_triggers": [],
    "right_triggers": []
  },
  "clickbait": {
    "score": 12,
    "level": "Low",
    "triggers": []
  },
  "readability": {
    "score": 68.5,
    "grade": "Standard",
    "sentence_count": 1
  }
}
```

### Additional Endpoints
- **`GET /health`** — System health check & active NLP status.
- **`GET /history`** — Returns the last 20 logged analysis records.
- **`DELETE /history`** — Clears the persistent audit log.
- **`GET /stats`** — Aggregate distribution of analyzed articles (`REAL`, `SUSPICIOUS`, `FAKE`).

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
