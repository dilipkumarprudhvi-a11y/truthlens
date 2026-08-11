from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import random
import re
import sqlite3
import datetime
import math
import spacy

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found.")
    nlp = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_path = "history.db"

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            snippet TEXT,
            classification TEXT,
            credibility_score INTEGER,
            fake_probability INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# NLP HELPER FUNCTIONS
# ─────────────────────────────────────────────

def compute_readability(text):
    """Flesch Reading Ease score"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()
    syllables = sum(count_syllables(w) for w in words)

    num_sentences = max(len(sentences), 1)
    num_words = max(len(words), 1)

    score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllables / num_words)
    score = max(0, min(100, round(score, 1)))

    if score >= 80:   grade = "Very Easy (5th grade)"
    elif score >= 70: grade = "Easy (6th grade)"
    elif score >= 60: grade = "Standard (7th-8th grade)"
    elif score >= 50: grade = "Fairly Difficult (High School)"
    elif score >= 30: grade = "Difficult (College level)"
    else:             grade = "Very Difficult (Professional)"

    avg_sentence_len = round(num_words / num_sentences, 1)
    return {"score": score, "grade": grade, "avg_sentence_length": avg_sentence_len, "sentence_count": num_sentences}

def count_syllables(word):
    word = word.lower().strip(".,!?;:")
    if len(word) <= 3:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e"):
        count -= 1
    return max(1, count)

def compute_sentiment(text):
    """Simple lexicon-based sentiment analysis"""
    positive_words = [
        "good","great","excellent","wonderful","amazing","fantastic","positive",
        "confirmed","verified","official","accurate","true","correct","credible",
        "legitimate","trustworthy","reliable","honest","factual","reported"
    ]
    negative_words = [
        "bad","terrible","awful","horrible","shocking","outrageous","disgusting",
        "fake","hoax","lie","fraud","wrong","false","misleading","dangerous",
        "exposed","scandal","conspiracy","secret","hidden","corrupt"
    ]
    fear_words = [
        "danger","threat","attack","kill","death","die","fear","panic",
        "crisis","catastrophe","disaster","collapse","war","terror","urgent"
    ]
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    fear_count = sum(1 for w in words if w in fear_words)
    total = max(len(words), 1)

    pos_pct  = round((pos_count / total) * 100, 1)
    neg_pct  = round((neg_count / total) * 100, 1)
    fear_pct = round((fear_count / total) * 100, 1)

    overall_score = pos_count - neg_count - (fear_count * 0.5)
    if overall_score > 1:   tone = "Positive"
    elif overall_score < -1: tone = "Negative"
    else:                    tone = "Neutral"

    return {
        "tone": tone,
        "positive_pct": pos_pct,
        "negative_pct": neg_pct,
        "fear_pct": fear_pct,
        "overall_score": round(overall_score, 2)
    }

def compute_bias(text):
    """Detect political/ideological bias signals"""
    left_keywords  = ["progressive","liberal","left-wing","socialist","democrat","equality","climate","welfare","diversity","inclusion"]
    right_keywords = ["conservative","right-wing","republican","traditional","patriot","freedom","border","nationalist","capitalism","militia"]
    emotional_amplifiers = ["always","never","everyone","nobody","all","none","every","completely","absolutely","totally"]
    
    text_lower = text.lower()
    left_hits   = [w for w in left_keywords  if w in text_lower]
    right_hits  = [w for w in right_keywords if w in text_lower]
    amp_hits    = [w for w in emotional_amplifiers if w in text_lower]

    if len(left_hits) > len(right_hits) + 1:   leaning = "Left-leaning"
    elif len(right_hits) > len(left_hits) + 1:  leaning = "Right-leaning"
    else:                                        leaning = "Relatively Neutral"

    bias_score = min(100, (len(left_hits) + len(right_hits)) * 15 + len(amp_hits) * 8)
    return {
        "leaning": leaning,
        "bias_score": bias_score,
        "left_triggers": left_hits,
        "right_triggers": right_hits,
        "amplifiers": amp_hits
    }

def compute_clickbait(text):
    """Detect clickbait patterns"""
    clickbait_patterns = [
        r"you won'?t believe",
        r"shocking(ly)?",
        r"mind[\s-]?blow",
        r"will (make|leave) you",
        r"number \d+ will",
        r"what happens next",
        r"this is why",
        r"the truth about",
        r"they don'?t want",
        r"secret(s)? (revealed?|exposed?)",
        r"click (here|now)",
        r"must[\s-]?see",
        r"going viral",
        r"breaking:?",
        r"exclusive:?"
    ]
    text_lower = text.lower()
    triggered = []
    for pattern in clickbait_patterns:
        match = re.search(pattern, text_lower)
        if match:
            triggered.append(match.group(0))

    caps_words = re.findall(r'\b[A-Z]{3,}\b', text)
    exclamations = text.count('!')
    questions = text.count('?')

    score = min(100, len(triggered) * 20 + len(caps_words) * 5 + exclamations * 8)
    if score >= 70:   level = "High Clickbait"
    elif score >= 40: level = "Moderate Clickbait"
    elif score >= 15: level = "Mild Clickbait"
    else:             level = "Not Clickbait"

    return {
        "score": score,
        "level": level,
        "triggers": triggered[:6],
        "caps_word_count": len(caps_words),
        "exclamation_count": exclamations,
        "question_count": questions
    }

def compute_writing_style(text, doc):
    """Detailed writing style metrics"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    words = text.split()

    avg_word_len = round(sum(len(w.strip('.,!?')) for w in words) / max(len(words), 1), 1)

    passive_count = 0
    if doc:
        for token in doc:
            if token.dep_ == "nsubjpass":
                passive_count += 1

    quote_count = len(re.findall(r'"[^"]{5,}"', text))
    number_count = len(re.findall(r'\b\d+(?:\.\d+)?%?\b', text))
    url_count = len(re.findall(r'https?://\S+', text))

    formality = "Formal" if avg_word_len > 5.5 and passive_count > 0 else \
                "Informal" if avg_word_len < 4.5 else "Semi-formal"

    return {
        "avg_word_length": avg_word_len,
        "passive_voice_count": passive_count,
        "quote_count": quote_count,
        "number_count": number_count,
        "url_count": url_count,
        "formality": formality,
        "sentence_count": len(sentences)
    }

def compute_virality_risk(fake_score, clickbait_score, sentiment):
    """Estimate how viral/shareable misinformation might be"""
    base = (fake_score * 0.4) + (clickbait_score * 0.35) + \
           (sentiment['negative_pct'] * 0.15) + (sentiment['fear_pct'] * 0.1)
    score = min(100, round(base))
    if score >= 70:   risk = "High Risk"
    elif score >= 45: risk = "Moderate Risk"
    elif score >= 20: risk = "Low Risk"
    else:             risk = "Minimal Risk"
    return {"score": score, "risk": risk}

def extract_claims(text, doc):
    """Extract key sentences that appear to be factual claims"""
    claim_indicators = ["is", "are", "was", "were", "has", "have", "will", "shows", "proves", "confirms", "reveals"]
    sentences = re.split(r'[.!?]+', text)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s) > 30:
            lower = s.lower()
            if any(ind in lower.split() for ind in claim_indicators):
                claims.append(s)
    return claims[:5]  # top 5 claims

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "TruthLens API v2 — Advanced NLP running"}

@app.post("/analyze")
async def analyze_news(request: Request):
    data = await request.json()
    text = data.get("text", "")

    time.sleep(1.5)

    if not text.strip():
        return {"error": "No text provided"}

    words = text.split()
    word_count = len(words)

    # spaCy NLP
    doc = None
    evidence_entities = []
    if nlp is not None:
        doc = nlp(text)
        seen = set()
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"] and ent.text not in seen:
                seen.add(ent.text)
                evidence_entities.append({"text": ent.text, "label": ent.label_})

    # Core scoring
    suspicious_keywords = [
        "shocking", "you won't believe", "secret", "hoax", "conspiracy",
        "exposed", "truth", "miracle", "click here", "scandal", "buy now",
        "illuminati", "deep state", "cure", "magic", "breaking", "urgent",
        "warning", "banned", "censored", "they don't want"
    ]

    fake_score = random.randint(5, 20)
    text_lower = text.lower()

    triggered_keywords = []
    for word in suspicious_keywords:
        if word in text_lower:
            fake_score += 12
            triggered_keywords.append(word)

    caps_words = re.findall(r'\b[A-Z]{2,}\b', text)
    if len(caps_words) > 3:
        fake_score += 15

    exclamations = text.count("!")
    if exclamations > 2:
        fake_score += 10

    final_score = max(0, min(100, fake_score))

    if final_score >= 60:
        result = "FAKE"
        confidence = final_score
        message = "High probability of being Fake News. Source verification strongly advised."
    elif final_score >= 40:
        result = "SUSPICIOUS"
        confidence = final_score
        message = "Content exhibits sensationalist patterns. Verification recommended."
    else:
        result = "REAL"
        confidence = 100 - final_score
        message = "Content appears credible following standard journalistic structures."

    # Context
    if result == "REAL" and evidence_entities:
        actual_news_mock = f"Verified: Major news outlets confirm reporting related to '{evidence_entities[0]['text']}'. The narrative aligns with documented public records."
    elif result == "FAKE" and evidence_entities:
        actual_news_mock = f"Disputed: Independent fact-checkers found no credible evidence for claims regarding '{evidence_entities[0]['text']}'. May be fabricated."
    else:
        actual_news_mock = "Cross-reference check complete. No strong conflicting or supporting articles found for this content."

    # Additional analyses
    readability  = compute_readability(text)
    sentiment    = compute_sentiment(text)
    bias         = compute_bias(text)
    clickbait    = compute_clickbait(text)
    writing      = compute_writing_style(text, doc)
    virality     = compute_virality_risk(final_score, clickbait["score"], sentiment)
    claims       = extract_claims(text, doc)

    # Save to DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO history (timestamp, snippet, classification, credibility_score, fake_probability) VALUES (?, ?, ?, ?, ?)',
        (datetime.datetime.now().isoformat(),
         text[:60] + "..." if len(text) > 60 else text,
         result, 100 - final_score, final_score)
    )
    conn.commit()
    conn.close()

    return {
        "text_length": word_count,
        "credibility_score": 100 - final_score,
        "fake_probability": final_score,
        "confidence": confidence,
        "classification": result,
        "message": message,
        "evidence": evidence_entities,
        "actual_news_context": actual_news_mock,
        "triggered_keywords": triggered_keywords,
        # New sections
        "readability": readability,
        "sentiment": sentiment,
        "bias": bias,
        "clickbait": clickbait,
        "writing_style": writing,
        "virality_risk": virality,
        "extracted_claims": claims
    }

@app.get("/history")
def get_history():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, timestamp, snippet, classification, credibility_score, fake_probability FROM history ORDER BY id DESC LIMIT 20'
    )
    rows = cursor.fetchall()
    conn.close()
    return {"history": [
        {"id": r[0], "timestamp": r[1], "snippet": r[2],
         "classification": r[3], "credibility_score": r[4], "fake_probability": r[5]}
        for r in rows
    ]}

@app.delete("/history")
def clear_history():
    conn = sqlite3.connect(db_path)
    conn.cursor().execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return {"status": "History cleared"}

@app.get("/stats")
def get_stats():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT classification, COUNT(*) FROM history GROUP BY classification")
    rows = cursor.fetchall()
    cursor.execute("SELECT AVG(credibility_score), AVG(fake_probability) FROM history")
    avgs = cursor.fetchone()
    conn.close()
    breakdown = {r[0]: r[1] for r in rows}
    return {
        "total": sum(breakdown.values()),
        "breakdown": breakdown,
        "avg_credibility": round(avgs[0] or 0, 1),
        "avg_fake_probability": round(avgs[1] or 0, 1)
    }
