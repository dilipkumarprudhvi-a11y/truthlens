# TruthLens AI — System Architecture & Verification Methodology

## 1. System Overview

TruthLens AI is an evidence-first, multi-vector credibility and misinformation analysis platform. It analyzes user-submitted text, URLs, and image screenshots to extract declarative factual claims, assess linguistic risk signals, retrieve real-time corroborating/refuting evidence from authoritative knowledge sources, and compute a deterministic, explainable credibility verdict.

---

## 2. Core Architecture Pipeline

```mermaid
flowchart TD
    subgraph Client["Frontend Layer (Canonical: backend/static/)"]
        UI[Glassmorphism Forensic Dashboard]
        Inputs[Text / URL / Image Dropzone]
        HUD[Verdict Banner & Claim Evidence Cards]
    end

    subgraph API["FastAPI Gateway Layer (backend/api/)"]
        Security[Security Headers, CORS & Rate Limiter]
        Validation[Pydantic Request Schemas & Size Limits]
        SSRF[SSRF Protection for URL Ingestion]
        Routes[API Endpoints: /analyze, /url/extract, /ocr/extract]
    end

    subgraph NLP["Analysis & Linguistic Engine (backend/services/)"]
        Claims[Claim Extraction & Sentence Boundary Classifier]
        Linguistic[Deterministic Linguistic Vector Engine]
        L_Sent[Sentiment & Fear Vector]
        L_Click[Clickbait & Sensationalism]
        L_Bias[Political Polarization]
        L_Read[Readability Flesch Index]
        L_Style[Writing Style & Formality]
    end

    subgraph Evidence["Evidence & Verification Engine (backend/services/)"]
        ProviderInterface[EvidenceProvider Interface]
        DDG[DuckDuckGo Search Provider]
        Wiki[Wikipedia Knowledge Provider]
        GFC[Google Fact Check API Provider]
        Matcher[Claim-Evidence Semantic Comparison & NLI Classifier]
    end

    subgraph Scoring["Scoring & Verdict Engine (backend/services/scoring.py)"]
        Scorer[Deterministic Aggregation Formula]
        Verdict[SUPPORTED / CONTRADICTED / MIXED / UNVERIFIED]
    end

    subgraph DB["Persistence Layer (backend/db/)"]
        SQLAlchemy[SQLAlchemy ORM Session]
        SQLite_PG[(SQLite Local / PostgreSQL Prod)]
    end

    Inputs --> Security --> Validation --> Routes
    Routes --> SSRF
    Routes --> Claims & Linguistic
    Linguistic --> L_Sent & L_Click & L_Bias & L_Read & L_Style
    Claims --> ProviderInterface
    ProviderInterface --> DDG & Wiki & GFC
    DDG & Wiki & GFC --> Matcher
    Matcher --> Scorer
    Linguistic --> Scorer
    Scorer --> SQLAlchemy --> SQLite_PG
    Scorer --> HUD
```

---

## 3. Separation of Concerns: Linguistic Risk vs Factual Truth

A fundamental tenet of TruthLens is the strict scientific distinction between **Linguistic Risk Signals** and **Factual Verification**:
- **Linguistic Signals** (Clickbait score, emotional tone, readability, writing style) analyze *how* something is written (rhetorical style). High clickbait or negative tone is an alert signal, but does **not** prove a claim is false.
- **Factual Verification** (Claim extraction, external evidence retrieval, source comparison) analyzes *what* is asserted against verified records and reporting.

---

## 4. Target Verdict Model

| Verdict | Meaning | Evidence Criteria |
|---|---|---|
| **`SUPPORTED`** | Core claims corroborated by authoritative sources. | Independent reputable sources verify the assertion without substantial dispute. |
| **`CONTRADICTED`** | Core claims directly refuted by reputable sources or documented fact checks. | Verified evidence contradicts key premises. |
| **`MIXED`** | Content contains both accurate facts and misleading/unsubstantiated claims. | Evidence shows partial truth or conflicting accounts. |
| **`UNVERIFIED`** | Insufficient corroborating evidence found in indexed knowledge repositories. | No authoritative external source has verified or refuted the claim. |

---

## 5. Security Architecture

1. **SSRF Guard (`url_extractor.py`)**: Validates URLs, resolves domain IPs, and blocks requests targeting private networks, loopback addresses (`127.0.0.1`, `localhost`), metadata endpoints (`169.254.169.254`), and non-HTTP protocols.
2. **Payload Protection**: Strict 25,000 character length limits, 5MB file upload caps, and 5-second external timeouts.
3. **Data Privacy**: Raw user articles are parsed in-memory and not permanently retained in the database; only structured scan IDs, anonymized snippets, and aggregated metrics are persisted.
4. **CORS & Security Headers**: Strict origin checks, `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY`.
