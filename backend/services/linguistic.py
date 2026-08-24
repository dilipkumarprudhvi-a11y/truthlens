"""
Deterministic Linguistic Risk Signal Engine
Evaluates rhetorical style, emotional vectors, readability, and syntax patterns.
Note: Linguistic signals evaluate writing style and are NOT proof of factual truth.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from ..schemas.analysis import (
    SentimentSignal,
    BiasSignal,
    ClickbaitSignal,
    ViralitySignal,
    ReadabilitySignal,
    WritingStyleSignal,
    NamedEntity,
    LinguisticSignals,
)

# Optional spaCy integration
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    NLP_AVAILABLE = True
except Exception:
    nlp = None
    NLP_AVAILABLE = False


# ─── LEXICONS ─────────────────────────────────────────────
POSITIVE_WORDS = {
    "breakthrough", "success", "innovative", "progress", "advance", "effective", "efficient",
    "verified", "confirmed", "collaborate", "benefit", "growth", "achievement", "promising",
    "positive", "triumph", "solution", "reliable", "sustainable", "peer-reviewed", "proven",
    "cure", "improved", "safely", "excellent", "accurate", "clean", "vital", "remarkable"
}

NEGATIVE_WORDS = {
    "crisis", "disaster", "collapse", "corrupt", "failure", "threat", "danger", "fraud",
    "destructive", "deadly", "fatal", "scandal", "deception", "horrific", "tragedy",
    "catastrophic", "toxic", "damaging", "hostile", "ruined", "bankrupt", "sabotage",
    "warning", "severe", "abusive", "unethical", "plague", "treason", "illegal", "crime"
}

FEAR_ALARM_WORDS = {
    "panic", "apocalypse", "deadly", "terrifying", "catastrophe", "imminent", "nightmare",
    "shocking", "doomsday", "destroy", "annihilate", "bio-weapon", "toxic", "fatal",
    "emergency", "existential", "threat", "chaos", "outbreak", "weaponized", "kill",
    "flee", "horrifying", "unprecedented danger", "banned", "censored", "they don't want"
}

CLICKBAIT_TRIGGERS = [
    "you won't believe", "shocking truth", "what happened next", "miracle cure",
    "secret trick", "they don't want you to know", "blow your mind", "jaw dropping",
    "doctors stunned", "click here", "will leave you speechless", "revealed at last",
    "exposed forever", "the real truth about", "warning to all", "must see this",
    "anonymous sources confirm", "banned video", "mind blowing"
]

LEFT_BIAS_WORDS = {
    "progressive", "corporate greed", "wealth tax", "systemic", "marginalized", "universal healthcare",
    "oligarchy", "climate emergency", "living wage", "far-right", "regressive", "disenfranchised",
    "grassroots", "unionize", "social justice", "anti-capitalist", "redistribution"
}

RIGHT_BIAS_WORDS = {
    "patriot", "deep state", "socialist agenda", "woke", "tyranny", "globalist", "border crisis",
    "indoctrination", "freedom of speech", "mainstream media", "liberty", "free market",
    "bureaucrats", "unconstitutional", "marxist", "traditional values", "law and order"
}

POLARIZATION_AMPLIFIERS = {
    "traitor", "treason", "evil", "puppet", "tyrant", "fascist", "communist", "destroying the country",
    "conspiracy", "enemy of the people", "cover-up", "shameless", "radical", "corrupt cabal"
}

SUSPICIOUS_KEYWORD_PATTERNS = [
    "shocking", "you won't believe", "secret", "hoax", "conspiracy",
    "exposed", "truth", "miracle", "click here", "scandal", "buy now",
    "illuminati", "deep state", "magic cure", "breaking", "urgent warning",
    "banned", "censored", "they don't want", "hidden truth", "unmasked"
]


# ─── DETERMINISTIC NLP CALCULATORS ────────────────────────
def compute_sentiment(text: str) -> SentimentSignal:
    """Deterministic lexicon-based sentiment analysis."""
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    if not words:
        return SentimentSignal(
            tone="Neutral / Objective",
            positive_pct=0,
            negative_pct=0,
            fear_pct=0,
            polarity_score=0.0
        )

    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    fear_count = sum(1 for w in words if w in FEAR_ALARM_WORDS)
    total_sentiment_words = pos_count + neg_count + fear_count

    if total_sentiment_words == 0:
        return SentimentSignal(
            tone="Neutral / Objective",
            positive_pct=10,
            negative_pct=10,
            fear_pct=0,
            polarity_score=0.0
        )

    pos_pct = round((pos_count / len(words)) * 100)
    neg_pct = round((neg_count / len(words)) * 100)
    fear_pct = round((fear_count / len(words)) * 100)

    # Polarity between -1.0 and +1.0
    polarity = (pos_count - neg_count) / max(1, (pos_count + neg_count))
    polarity_score = round(max(-1.0, min(1.0, polarity)), 2)

    if fear_pct > 8 or (fear_count >= 2 and neg_count > pos_count):
        tone = "Alarmist / Fear-Inducing"
    elif polarity_score >= 0.25:
        tone = "Positive / Optimistic"
    elif polarity_score <= -0.25:
        tone = "Critical / Negative"
    else:
        tone = "Neutral / Objective"

    return SentimentSignal(
        tone=tone,
        positive_pct=min(100, pos_pct * 4),
        negative_pct=min(100, neg_pct * 4),
        fear_pct=min(100, fear_pct * 5),
        polarity_score=polarity_score
    )


def compute_clickbait(text: str) -> ClickbaitSignal:
    """Deterministic clickbait calculation from punctuation, caps, and sensational hooks."""
    words = text.split()
    total_words = max(1, len(words))
    
    # 1. All-caps words (ignoring short acronyms <= 2 letters)
    caps_words = [w for w in words if w.isupper() and len(w) > 2 and w.isalpha()]
    caps_ratio = len(caps_words) / total_words

    # 2. Punctuation intensity
    exclamation_count = text.count("!")
    question_count = text.count("?")

    # 3. Trigger phrase matches
    text_lower = text.lower()
    found_triggers = [trig for trig in CLICKBAIT_TRIGGERS if trig in text_lower]

    # Weighted scoring formula (0-100)
    score = 0
    score += min(35, len(found_triggers) * 15)
    score += min(30, int(caps_ratio * 150))
    score += min(20, exclamation_count * 6)
    score += min(15, (question_count - 1) * 5 if question_count > 1 else 0)

    score = max(0, min(100, score))

    if score >= 70:
        level = "Extreme Clickbait Alert"
    elif score >= 45:
        level = "Moderate Clickbait Risk"
    elif score >= 20:
        level = "Low Sensationalism"
    else:
        level = "Minimal / Standard Headline"

    return ClickbaitSignal(
        score=score,
        level=level,
        caps_word_count=len(caps_words),
        exclamation_count=exclamation_count,
        question_count=question_count,
        triggers=found_triggers
    )


def compute_bias(text: str) -> BiasSignal:
    """Deterministic political bias and partisan tone analyzer."""
    text_lower = text.lower()
    left_found = [w for w in LEFT_BIAS_WORDS if w in text_lower]
    right_found = [w for w in RIGHT_BIAS_WORDS if w in text_lower]
    amp_found = [w for w in POLARIZATION_AMPLIFIERS if w in text_lower]

    left_score = len(left_found)
    right_score = len(right_found)

    # Balance ratio: 0.0 (Left) to 1.0 (Right), 0.5 is Center
    balance_ratio = round((right_score + 1) / (left_score + right_score + 2), 2)

    diff = right_score - left_score
    if diff >= 3:
        leaning = "Right Leaning"
    elif diff <= -3:
        leaning = "Left Leaning"
    elif diff >= 1:
        leaning = "Slight Right Leaning"
    elif diff <= -1:
        leaning = "Slight Left Leaning"
    else:
        leaning = "Center / Balanced"

    if len(amp_found) >= 2:
        leaning += " (High Polarization)"

    return BiasSignal(
        leaning=leaning,
        left_triggers=left_found,
        right_triggers=right_found,
        amplifiers=amp_found,
        balance_ratio=balance_ratio
    )


def count_syllables(word: str) -> int:
    """Count syllables in a word using standard vowel clustering."""
    word = word.lower().strip(".:;?!,'\"")
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    # Count vowel groups
    count = len(re.findall(r'[aeiouy]+', word))
    if word.endswith('e') and not word.endswith('le') and count > 1:
        count -= 1
    return max(1, count)


def compute_readability(text: str) -> ReadabilitySignal:
    """Flesch Reading Ease and Flesch-Kincaid Grade Level calculation."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = re.findall(r'\b[a-zA-Z]+\b', text)

    num_sentences = max(1, len(sentences))
    num_words = max(1, len(words))
    total_syllables = sum(count_syllables(w) for w in words)

    asl = num_words / num_sentences  # Average Sentence Length
    asw = total_syllables / num_words  # Average Syllables per Word

    # Flesch Reading Ease formula
    fre = 206.835 - (1.015 * asl) - (84.6 * asw)
    fre_score = round(max(0.0, min(100.0, fre)), 1)

    if fre_score >= 80:
        grade = "Very Easy (Grade 5-6)"
    elif fre_score >= 65:
        grade = "Standard (Grade 8-9)"
    elif fre_score >= 50:
        grade = "Fairly Difficult (High School)"
    elif fre_score >= 30:
        grade = "Difficult (College Level)"
    else:
        grade = "Very Difficult (Academic / Technical)"

    return ReadabilitySignal(
        score=fre_score,
        grade=grade,
        sentence_count=num_sentences,
        avg_sentence_length=round(asl, 1)
    )


def compute_writing_style(text: str, doc: Any = None) -> WritingStyleSignal:
    """Deterministic structural and syntactic writing style assessment."""
    words = text.split()
    total_words = max(1, len(words))
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    avg_word_len = round(sum(len(w.strip(".,!?\"'")) for w in words) / total_words, 2)
    
    # Passive voice estimation
    passive_matches = re.findall(r'\b(?:is|are|was|were|been|being)\s+([a-z]+ed|[a-z]+en)\b', text.lower())
    quote_matches = re.findall(r'["\'](.*?)["\']', text)
    number_matches = re.findall(r'\b\d+(?:[\.,]\d+)?%?\b', text)
    url_matches = re.findall(r'https?://\S+', text)

    # Formality estimation index
    formality_points = 0
    if avg_word_len > 5.0: formality_points += 1
    if len(passive_matches) >= 1: formality_points += 1
    if len(quote_matches) >= 1: formality_points += 1
    if len(number_matches) >= 2: formality_points += 1
    if text.count("!") == 0: formality_points += 1

    if formality_points >= 4:
        formality = "Formal / Academic"
    elif formality_points >= 2:
        formality = "Standard Editorial"
    else:
        formality = "Informal / Conversational"

    return WritingStyleSignal(
        formality=formality,
        avg_word_length=avg_word_len,
        passive_voice_count=len(passive_matches),
        quote_count=len(quote_matches),
        number_count=len(number_matches),
        url_count=len(url_matches),
        sentence_count=len(sentences)
    )


def extract_entities(text: str, doc: Any = None) -> List[NamedEntity]:
    """Named Entity Recognition using spaCy or deterministic regex fallback."""
    entities: List[NamedEntity] = []
    seen = set()

    if doc is not None:
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "NORP", "FAC"] and ent.text not in seen:
                seen.add(ent.text)
                label_map = {"NORP": "GPE", "FAC": "LOC"}
                entities.append(NamedEntity(text=ent.text, label=label_map.get(ent.label_, ent.label_)))
    else:
        # Regex capitalized sequence fallback
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for name in capitalized:
            if name.lower() not in {"the", "a", "an", "this", "that", "it", "in", "on", "at", "breaking", "warning"} and name not in seen:
                seen.add(name)
                entities.append(NamedEntity(text=name, label="ORG" if "Inc" in name or "Org" in name else "PERSON"))
                if len(entities) >= 6:
                    break

    return entities[:12]


def compute_virality_proxy(clickbait_score: int, fear_pct: int, negative_pct: int) -> ViralitySignal:
    """Composite virality potential estimation based on emotional volatility & clickbait."""
    score = int(round((clickbait_score * 0.5) + (fear_pct * 0.3) + (negative_pct * 0.2)))
    score = max(0, min(100, score))

    factors = []
    if clickbait_score > 40:
        factors.append(f"Sensational hook weighting contributes {clickbait_score}/100")
    if fear_pct > 15:
        factors.append(f"High alarmist emotion index: {fear_pct}%")
    if negative_pct > 20:
        factors.append(f"Polarizing negative framing: {negative_pct}%")
    if not factors:
        factors.append("Low sensationalism and balanced emotional tone reduce viral spread velocity.")

    if score >= 65:
        risk = "High Viral Spread Potential"
    elif score >= 35:
        risk = "Moderate Virality Potential"
    else:
        risk = "Low Velocity / Standard Spread"

    return ViralitySignal(
        score=score,
        risk=risk,
        velocity_factors=factors
    )


def extract_suspicious_keywords(text: str) -> List[str]:
    """Finds flagged deception/conspiracy trigger words."""
    text_lower = text.lower()
    return [kw for kw in SUSPICIOUS_KEYWORD_PATTERNS if kw in text_lower]


def analyze_linguistic_signals(text: str) -> Tuple[LinguisticSignals, List[NamedEntity], Any]:
    """Runs complete deterministic linguistic evaluation pipeline."""
    doc = None
    if nlp is not None:
        try:
            doc = nlp(text)
        except Exception:
            doc = None

    sentiment = compute_sentiment(text)
    clickbait = compute_clickbait(text)
    bias = compute_bias(text)
    readability = compute_readability(text)
    writing_style = compute_writing_style(text, doc)
    entities = extract_entities(text, doc)
    virality = compute_virality_proxy(clickbait.score, sentiment.fear_pct, sentiment.negative_pct)
    triggered_kw = extract_suspicious_keywords(text)

    signals = LinguisticSignals(
        sentiment=sentiment,
        bias=bias,
        clickbait=clickbait,
        virality_risk=virality,
        readability=readability,
        writing_style=writing_style,
        triggered_keywords=triggered_kw
    )

    return signals, entities, doc
