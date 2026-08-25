"""
Deterministic Linguistic Risk Signal Engine
Evaluates rhetorical style, emotional vectors, readability, and syntax patterns.

IMPORTANT DISCLAIMER:
  Linguistic signals evaluate writing style, emotion, and structure.
  They are NOT proof of factual truth or falsity.
  High clickbait or negative sentiment does not mean a claim is false.
  Low scores do not guarantee accuracy.
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


# ─── LEXICONS ──────────────────────────────────────────────────────────────────

POSITIVE_WORDS = {
    "breakthrough", "success", "innovative", "progress", "advance", "effective", "efficient",
    "collaborate", "benefit", "growth", "achievement", "promising", "positive", "triumph",
    "solution", "reliable", "sustainable", "peer-reviewed", "improved", "excellent",
    "accurate", "clean", "vital", "remarkable", "approved", "funded", "published", "launched"
}

NEGATIVE_WORDS = {
    "crisis", "disaster", "collapse", "corrupt", "failure", "threat", "fraud",
    "destructive", "deadly", "fatal", "horrific", "tragedy", "catastrophic", "toxic",
    "damaging", "hostile", "ruined", "bankrupt", "sabotage", "severe", "abusive",
    "unethical", "plague", "treason", "illegal", "crime", "violence", "war", "attack"
}

FEAR_ALARM_WORDS = {
    "panic", "apocalypse", "terrifying", "catastrophe", "imminent", "nightmare",
    "doomsday", "annihilate", "bio-weapon", "existential", "chaos", "outbreak",
    "weaponized", "unprecedented danger", "they don't want you to know", "flee"
}

# Hard deception signals — phrases and patterns highly correlated with
# misinformation, conspiracy theories, pseudoscience, and fabricated hoaxes.
DECEPTION_TIER1 = [
    # Conspiracy & Propaganda
    "illuminati", "deep state", "new world order", "mind control", "chemtrails",
    "secret cabal", "globalist plot", "globalist elite", "shadow government",
    "reptilian", "lizard people", "crisis actor", "crisis actors", "wake up sheeple",
    "world government order", "globalist tyrant", "haarp weather", "depopulation agenda",
    "faked by nasa", "moon landing was faked", "moon landings were faked", "faked moon landing",
    "flat earth", "antarctica is an ice wall", "hollywood studio hoax", "fabricated hoax",
    "secretly staged", "staged by the government", "qanon", "stolen election without proof",

    # Medical & Health Misinformation
    "miracle cure", "magic cure", "secret remedy", "secret herbal mixture",
    "cure for cancer", "cancer cure discovered", "cures cancer", "cures diabetes",
    "cures all diseases", "cure all diseases", "doctors are hiding", "what doctors won't tell you",
    "big pharma is hiding", "big pharma hiding", "drinking bleach", "chlorine dioxide",
    "vaccines contain microchips", "vaccine microchip", "vaccine microchips", "5g causes",
    "5g towers are broadcasting", "autism caused by vaccines", "detox parasite flush",
    "100% cure guaranteed", "reverse aging overnight", "kill 100% of cancer cells",

    # Fabricated Leaks & False Claims
    "leaked government documents prove", "leaked secret footage", "classified documents leaked",
    "they are desperately trying to censor", "banned from the internet", "what they don't want you to know",
    "they don't want you to know", "what the media won't show you", "anonymous whistleblower leaked",
    "anonymous experts confirm", "insider confirms shocking", "truth they are desperately",
    "buy now before they ban", "one weird trick", "banned forever"
]

# Soft sensationalism signals — hyperbolic or clickbait phrasing
DECEPTION_TIER2 = [
    "you won't believe", "shocking truth", "what happened next",
    "jaw dropping", "doctors stunned", "will leave you speechless",
    "mind blowing", "exposed forever", "blow your mind",
    "horrific truth", "shocking footage", "viral video exposes",
    "unbelievable discovery", "mind blowing secret", "scientists stunned",
    "click here to see", "censored everywhere", "media blackout"
]

CLICKBAIT_TRIGGERS = DECEPTION_TIER1 + DECEPTION_TIER2

# NOTE: "breaking", "truth", "warning", "secret", "scandal", "exposed" are intentionally
# REMOVED from triggered keywords — they appear every day in legitimate journalism.
# Including them causes catastrophic false-positive rates.

LEFT_BIAS_WORDS = {
    "progressive", "corporate greed", "wealth tax", "systemic", "marginalized",
    "universal healthcare", "oligarchy", "climate emergency", "living wage",
    "far-right", "regressive", "disenfranchised", "grassroots", "unionize",
    "social justice", "anti-capitalist", "redistribution"
}

RIGHT_BIAS_WORDS = {
    "deep state", "socialist agenda", "woke", "tyranny", "globalist", "border crisis",
    "indoctrination", "mainstream media bias", "free market", "bureaucrats",
    "unconstitutional", "marxist", "traditional values", "law and order",
    "patriot movement", "second amendment"
}

POLARIZATION_AMPLIFIERS = {
    "traitor", "treason", "evil puppet", "tyrant", "destroying the country",
    "enemy of the people", "corrupt cabal", "radical extremist", "shameless traitor"
}


# ─── SENTIMENT ─────────────────────────────────────────────────────────────────

def compute_sentiment(text: str) -> SentimentSignal:
    """
    Deterministic lexicon-based sentiment analysis.
    Counts positive, negative, and fear-related words relative to total word count.
    """
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

    if fear_pct > 10 or (fear_count >= 3 and neg_count > pos_count):
        tone = "Alarmist / Fear-Inducing"
    elif polarity_score >= 0.25:
        tone = "Positive / Optimistic"
    elif polarity_score <= -0.25:
        tone = "Critical / Negative"
    else:
        tone = "Neutral / Objective"

    # Scale to 0-100 display (cap at reasonable visual ranges)
    return SentimentSignal(
        tone=tone,
        positive_pct=min(100, pos_pct * 5),
        negative_pct=min(100, neg_pct * 5),
        fear_pct=min(100, fear_pct * 8),
        polarity_score=polarity_score
    )


# ─── CLICKBAIT ─────────────────────────────────────────────────────────────────

def compute_clickbait(text: str) -> ClickbaitSignal:
    """
    Deterministic clickbait calculation from punctuation intensity, ALL-CAPS ratio,
    and specific sensational hook phrases.

    NOTE: "BREAKING" in uppercase is a journalism convention and is excluded from the
    caps penalty to avoid false positives on legitimate breaking news.
    """
    # Exclude common legitimate journalism caps words
    LEGITIMATE_CAPS = {"BREAKING", "UPDATE", "DEVELOPING", "WATCH", "LIVE", "EXCLUSIVE", "REPORT"}

    words = text.split()
    total_words = max(1, len(words))

    caps_words = [w for w in words if w.isupper() and len(w) > 2 and w.isalpha()
                  and w not in LEGITIMATE_CAPS]
    caps_ratio = len(caps_words) / total_words

    exclamation_count = text.count("!")
    question_count = text.count("?")

    text_lower = text.lower()
    found_tier1 = [trig for trig in DECEPTION_TIER1 if trig in text_lower]
    found_tier2 = [trig for trig in DECEPTION_TIER2 if trig in text_lower]
    found_triggers = found_tier1 + found_tier2

    # Weighted scoring: Tier 1 phrases score much higher than Tier 2
    score = 0
    score += min(50, len(found_tier1) * 25)
    score += min(20, len(found_tier2) * 10)
    score += min(25, int(caps_ratio * 120))
    score += min(15, exclamation_count * 5)
    # Only count MULTIPLE question marks as clickbait (one question mark is normal)
    score += min(10, (question_count - 1) * 4 if question_count > 2 else 0)

    score = max(0, min(100, score))

    if score >= 70:
        level = "Extreme Sensationalism"
    elif score >= 45:
        level = "Moderate Clickbait Risk"
    elif score >= 20:
        level = "Mild Sensationalism"
    else:
        level = "Standard / Neutral Framing"

    return ClickbaitSignal(
        score=score,
        level=level,
        caps_word_count=len(caps_words),
        exclamation_count=exclamation_count,
        question_count=question_count,
        triggers=found_triggers
    )


# ─── POLITICAL BIAS ────────────────────────────────────────────────────────────

def compute_bias(text: str) -> BiasSignal:
    """
    Deterministic political bias and partisan tone analyzer.
    Uses keyword presence. Does NOT evaluate factual accuracy.
    """
    text_lower = text.lower()
    left_found = [w for w in LEFT_BIAS_WORDS if w in text_lower]
    right_found = [w for w in RIGHT_BIAS_WORDS if w in text_lower]
    amp_found = [w for w in POLARIZATION_AMPLIFIERS if w in text_lower]

    left_score = len(left_found)
    right_score = len(right_found)

    # Balance ratio: 0.0 (Left) → 0.5 (Center) → 1.0 (Right)
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


# ─── READABILITY ───────────────────────────────────────────────────────────────

def count_syllables(word: str) -> int:
    """Count syllables in a word using standard vowel clustering."""
    word = word.lower().strip(".:;?!,'\"")
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    count = len(re.findall(r'[aeiouy]+', word))
    if word.endswith('e') and not word.endswith('le') and count > 1:
        count -= 1
    return max(1, count)


def compute_readability(text: str) -> ReadabilitySignal:
    """
    Flesch Reading Ease (0-100, higher = easier) and grade label.
    Formula: FRE = 206.835 - 1.015 * ASL - 84.6 * ASW
    """
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = re.findall(r'\b[a-zA-Z]+\b', text)

    num_sentences = max(1, len(sentences))
    num_words = max(1, len(words))
    total_syllables = sum(count_syllables(w) for w in words)

    asl = num_words / num_sentences
    asw = total_syllables / num_words

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


# ─── WRITING STYLE ─────────────────────────────────────────────────────────────

def compute_writing_style(text: str, doc: Any = None) -> WritingStyleSignal:
    """Deterministic structural and syntactic writing style assessment."""
    words = text.split()
    total_words = max(1, len(words))
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    avg_word_len = round(sum(len(w.strip(".,!?\"'")) for w in words) / total_words, 2)
    passive_matches = re.findall(r'\b(?:is|are|was|were|been|being)\s+([a-z]+ed|[a-z]+en)\b', text.lower())
    quote_matches = re.findall(r'[""\'](.*?)[""\'"]', text)
    number_matches = re.findall(r'\b\d+(?:[\.,]\d+)?%?\b', text)
    url_matches = re.findall(r'https?://\S+', text)

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


# ─── NAMED ENTITIES ────────────────────────────────────────────────────────────

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
        skip = {"The", "A", "An", "This", "That", "It", "In", "On", "At", "Breaking",
                "Warning", "According", "However", "Meanwhile", "Published", "Scientists"}
        for name in capitalized:
            if name not in skip and name not in seen and len(name) > 2:
                seen.add(name)
                entities.append(NamedEntity(
                    text=name,
                    label="ORG" if any(x in name for x in ["Inc", "Corp", "Ltd", "Agency", "Department"]) else "PERSON"
                ))
                if len(entities) >= 8:
                    break

    return entities[:12]


# ─── VIRALITY PROXY ────────────────────────────────────────────────────────────

def compute_virality_proxy(clickbait_score: int, fear_pct: int, negative_pct: int) -> ViralitySignal:
    """
    Composite virality potential estimation based on emotional volatility and clickbait.
    This is a linguistic proxy — it does NOT measure actual social media spread.
    """
    score = int(round((clickbait_score * 0.5) + (fear_pct * 0.3) + (negative_pct * 0.2)))
    score = max(0, min(100, score))

    factors = []
    if clickbait_score > 40:
        factors.append(f"Sensational hook detected (clickbait score: {clickbait_score}/100)")
    if fear_pct > 20:
        factors.append(f"High fear/alarm language density: {fear_pct}%")
    if negative_pct > 25:
        factors.append(f"Predominantly negative framing: {negative_pct}%")
    if not factors:
        factors.append("Balanced tone and standard framing indicate lower viral velocity.")

    if score >= 65:
        risk = "High Viral Spread Potential"
    elif score >= 35:
        risk = "Moderate Virality Potential"
    else:
        risk = "Low Velocity / Standard Spread"

    return ViralitySignal(score=score, risk=risk, velocity_factors=factors)


# ─── SUSPICIOUS KEYWORD DETECTION ──────────────────────────────────────────────

def extract_suspicious_keywords(text: str) -> List[str]:
    """
    Returns ONLY hard deception/misinformation trigger phrases found in text.
    
    Intentionally conservative list: words like 'breaking', 'truth', 'secret',
    'warning', 'scandal', and 'exposed' are EXCLUDED because they appear daily
    in legitimate journalism and their presence does not predict misinformation.
    """
    text_lower = text.lower()
    return [kw for kw in DECEPTION_TIER1 + DECEPTION_TIER2 if kw in text_lower]


# ─── MASTER ANALYSIS RUNNER ────────────────────────────────────────────────────

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
