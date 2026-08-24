# 🔍 TruthLens AI — Evidence-Grounded Credibility & Misinformation Intelligence

> **A production-ready, evidence-first NLP forensic intelligence platform that extracts declarative claims, queries authoritative knowledge sources, evaluates linguistic risk vectors, and computes deterministic, explainable credibility ratings.**

[![Live Web Application](https://img.shields.io/badge/Live_Demo-GitHub_Pages-blue?style=for-the-badge&logo=github)](https://dilipkumarprudhvi-a11y.github.io/truthlens/)
[![Backend API](https://img.shields.io/badge/Backend_API-FastAPI_3.0-009688?style=for-the-badge&logo=fastapi)](https://truthlens-1-ue36.onrender.com/health)
[![Test Suite](https://img.shields.io/badge/Test_Suite-27_Passed-success?style=for-the-badge&logo=pytest)](backend/tests/)
[![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 Scientific Principles & Core Methodology

TruthLens adheres to strict scientific and engineering non-negotiables:
1. **Zero Randomness**: All scoring, linguistic evaluations, and verdicts are 100% deterministic and testable.
2. **Zero Simulated Verification**: The platform **never** fabricates citations or claims external organizations verified an assertion unless an active provider actually returned evidence. Unsubstantiated statements are honestly marked **`UNVERIFIED`**.
3. **Decoupled Rhetorical Risk vs Factual Truth**: Linguistic signals (clickbait score, fear emotion, readability) analyze *how* text is framed; external evidence corroboration evaluates *what* facts are asserted.
4. **Calibrated Uncertainty**: Categorizes content into four scientific verdicts:
   - **`SUPPORTED`** — Corroborated by independent, authoritative records.
   - **`CONTRADICTED`** — Disputed or refuted by documented evidence.
   - **`MIXED`** — Combines substantiated data with disputed assertions.
   - **`UNVERIFIED`** — Insufficient independent evidence retrieved in indexed stores.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TruthLens User Interface                 │
│       (Canonical Source: backend/static/ — HTML5/CSS3/JS)   │
└──────────────────────────────┬──────────────────────────────┘
                               │  Async REST (Pydantic v2)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Gateway & Security                 │
│      (Rate Limiting, X-Request-ID, SSRF Guard, CORS)        │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ Factual Claims Extractor     │ │ Deterministic Linguistic   │
│ (Declarative Sentence NLI)   │ │ Analyzer (Emotion/Bias)    │
└──────────────┬───────────────┘ └────────────┬───────────────┘
               │                              │
               ▼                              │
┌──────────────────────────────┐              │
│ Evidence Retrieval Providers │              │
│ (Wikipedia, DDG, FactCheck)  │              │
└──────────────┬───────────────┘              │
               │                              │
               ▼                              │
┌──────────────────────────────┐              │
│ Claim-Evidence Evaluator     │              │
│ (Support/Refutation Matcher) │              │
└──────────────┬───────────────┘              │
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│             Deterministic Scoring & Aggregation             │
│        (Weighted Evidence, Quality, Uncertainty Penalties)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               SQLAlchemy ORM Persistence Layer              │
│                 (SQLite Local / PostgreSQL)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Core Analytical Modules

| Module | Service File | Diagnostic Output |
|---|---|---|
| **Claim Extraction** | `services/claims.py` | Parses atomic declarative statements, strips noise words, and builds targeted search queries. |
| **Evidence Providers** | `services/evidence.py` | Queries Wikipedia OpenSearch, DuckDuckGo Knowledge API, and Google Fact Check Tools API with domain authority ranking. |
| **Claim Evaluator** | `services/scoring.py` | Performs refutation/affirmation matching and classifies claims as `SUPPORTED`, `CONTRADICTED`, `MIXED`, or `UNVERIFIED`. |
| **Linguistic Risk** | `services/linguistic.py` | Computes sentiment polarity, fear index, clickbait intensity, partisan bias ratio, Flesch readability, and formality. |
| **SSRF-Safe Ingestion** | `services/url_extractor.py` | Resolves target IPs and blocks private/loopback/cloud metadata ranges before extracting web article text. |
| **OCR Ingestion** | `services/ocr.py` | Validates image MIME types (PNG, JPEG, WEBP) and extracts text via Tesseract OCR engine. |

---

## 📊 Benchmark Evaluation Metrics

Tested on a standardized labeled benchmark dataset (`backend/tests/test_evaluation.py`):

| Evaluation Metric | Score | Benchmark Status |
|---|---|---|
| **Overall Accuracy** | **100.0%** | Exceeds Target (≥80%) |
| **Deception Precision** | **100.0%** | Exceeds Target (≥80%) |
| **Deception Recall** | **100.0%** | Exceeds Target (≥80%) |
| **F1 Score** | **1.000** | Exceeds Target (≥0.80) |

---

## 📁 Repository Structure

```
truthlens/
├── backend/
│   ├── main.py                 ← FastAPI application entrypoint & static mount
│   ├── requirements.txt       ← Modular backend dependencies
│   ├── api/
│   │   ├── routes.py          ← Standardized REST API endpoints
│   │   └── dependencies.py    ← DB session, rate limiter, service injection
│   ├── db/
│   │   ├── models.py          ← SQLAlchemy ORM models (Scan, Claim, Evidence)
│   │   └── session.py         ← Engine & session management
│   ├── schemas/
│   │   └── analysis.py        ← Pydantic v2 request/response schemas
│   ├── services/
│   │   ├── analyzer.py        ← Master orchestration pipeline
│   │   ├── claims.py          ← Declarative claim extraction
│   │   ├── evidence.py        ← Evidence provider interfaces
│   │   ├── linguistic.py      ← Deterministic linguistic risk analyzers
│   │   ├── scoring.py         ← Evidence comparison & scoring aggregator
│   │   ├── url_extractor.py   ← SSRF-safe URL scraper
│   │   └── ocr.py             ← Image & OCR service interface
│   ├── static/                ← CANONICAL FRONTEND SOURCE OF TRUTH
│   │   ├── index.html         ← Forensic UI dashboard
│   │   ├── style.css          ← Glassmorphism dark styling & keyframe animations
│   │   ├── app.js             ← Evidence matrix client & failover
│   │   ├── config.js          ← API configuration
│   │   ├── how-it-works.html  ← Scientific methodology guide
│   │   ├── faq.html           ← Frequently asked questions
│   │   ├── privacy.html       ← Privacy & retention policy
│   │   ├── terms.html         ← Terms of service
│   │   ├── sitemap.xml        ← SEO sitemap
│   │   └── robots.txt         ← Search engine crawler rules
│   └── tests/
│       ├── test_linguistic.py ← Determinism & linguistic tests
│       ├── test_claims.py     ← Claim extraction & filter tests
│       ├── test_evidence.py   ← Authority ranking & provider tests
│       ├── test_scoring.py    ← Verdict aggregator tests
│       ├── test_security.py   ← SSRF & input security tests
│       ├── test_api.py        ← Integration endpoint tests
│       └── test_evaluation.py ← Labeled benchmark evaluation
├── frontend/                  ← Static mirror for CDN hosting
├── docs/
│   └── architecture.md        ← Detailed system architecture specification
├── .env.example               ← Configuration template
├── index.html                 ← GitHub Pages root entrypoint
├── style.css                  ← Root stylesheet
├── app.js                     ← Root client script
└── config.js                  ← Root configuration script
```

---

## ⚡ Quick Start & Development Setup

### 1. Prerequisites
- **Python 3.9+** installed on your system.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/dilipkumarprudhvi-a11y/truthlens.git
cd truthlens

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 3. Run Automated Tests
```bash
python -m pytest backend/tests -v
```

### 4. Start Local Development Server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser.

---

## 📡 REST API Reference

### `POST /api/analyze`
Analyzes input text, extracts claims, retrieves evidence, and returns an explainable verdict.

**Request:**
```json
{
  "text": "Scientists at the renewable energy laboratory published peer-reviewed findings confirming a 30% efficiency increase in solar cells."
}
```

**Response (Sample):**
```json
{
  "scan_id": "scan_42e4a30b",
  "text_length": 18,
  "primary_verdict": "SUPPORTED",
  "legacy_classification": "REAL",
  "credibility_score": 92.5,
  "fake_probability": 7.5,
  "confidence": 80.0,
  "message": "Core assertions are corroborated by authoritative knowledge and wire records.",
  "claims": [
    {
      "claim_id": "claim_1",
      "text": "Scientists at the renewable energy laboratory published peer-reviewed findings confirming a 30% efficiency increase in solar cells.",
      "verdict": "SUPPORTED",
      "confidence": 85.0,
      "explanation": "Corroborated by reports from Wikipedia Encyclopedia.",
      "evidence": [
        {
          "source_name": "Wikipedia Encyclopedia",
          "title": "Perovskite solar cell",
          "url": "https://en.wikipedia.org/wiki/Perovskite_solar_cell",
          "snippet": "Research demonstrates notable efficiency gains in tandem perovskite solar architectures.",
          "authority_score": 0.85,
          "relevance_score": 0.82
        }
      ]
    }
  ],
  "linguistic_signals": {
    "sentiment": { "tone": "Positive / Optimistic", "positive_pct": 75, "negative_pct": 0, "fear_pct": 0 },
    "bias": { "leaning": "Center / Balanced", "balance_ratio": 0.5 },
    "clickbait": { "score": 0, "level": "Minimal / Standard Headline" },
    "readability": { "score": 68.2, "grade": "Standard (Grade 8-9)" }
  }
}
```

---

## 🔒 Security & Privacy

- **SSRF Prevention**: Strict DNS IP resolution blocks calls to private subnets, loopbacks, and cloud metadata.
- **Privacy By Design**: Raw user articles are processed in-memory and not permanently retained in the database.
- **Input Validation**: Enforces 25,000 character maximums, 5MB file upload caps, and 5-second timeouts.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
