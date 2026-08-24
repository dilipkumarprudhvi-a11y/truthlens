"""
Factual Claim Extraction Service
Extracts atomic declarative factual assertions from user text.
Filters out pure questions, subjective opinions, and conversational filler.
"""

import re
from typing import List, Dict, Any, Tuple
from ..schemas.analysis import ClaimItem

# Indicators that a sentence makes a testable factual assertion
FACTUAL_PREDICATE_INDICATORS = {
    "is", "are", "was", "were", "has", "have", "had", "will", "announced", "discovered",
    "published", "proved", "confirmed", "revealed", "stated", "found", "signed", "passed",
    "caused", "killed", "injured", "elected", "increased", "decreased", "developed",
    "launched", "approved", "banned", "tested", "concluded", "demonstrated", "recorded"
}

# Phrases indicating subjective opinion or non-factual statements
OPINION_MARKER_PATTERNS = [
    r"\bi think\b", r"\bi believe\b", r"\bin my (?:personal )?opinion\b",
    r"\bi feel\b", r"\bpersonally\b", r"\bwho knows\b", r"\bwhat if\b",
    r"\bit seems to me\b", r"\bmaybe\b", r"\bperhaps\b", r"\bprobably\b"
]


def clean_sentence(sentence: str) -> str:
    """Strip extra quotes and whitespace."""
    s = sentence.strip().strip('"\'“”')
    s = re.sub(r'\s+', ' ', s)
    return s


def is_factual_claim(sentence: str) -> bool:
    """Evaluates if a sentence structure is a declarative testable assertion."""
    s = sentence.strip()
    if len(s) < 20 or len(s.split()) < 4:
        return False
    
    # Exclude questions and pure imperatives
    if s.endswith("?") or s.startswith(("Click here", "Subscribe", "Follow us", "Share this")):
        return False

    s_lower = s.lower()
    
    # If it contains clear subjective opinion markers
    if any(re.search(pat, s_lower) for pat in OPINION_MARKER_PATTERNS):
        return False

    # Check for presence of factual predicate indicators
    tokens = set(re.findall(r'\b[a-z]+\b', s_lower))
    has_predicate = bool(tokens.intersection(FACTUAL_PREDICATE_INDICATORS))
    
    return has_predicate


def extract_claims(text: str, max_claims: int = 5) -> List[ClaimItem]:
    """
    Extracts declarative claims from input text and formats them with claim IDs.
    """
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    claims: List[ClaimItem] = []
    seen = set()

    for idx, raw_s in enumerate(raw_sentences, start=1):
        cleaned = clean_sentence(raw_s)
        if not cleaned:
            continue

        if is_factual_claim(cleaned) and cleaned not in seen:
            seen.add(cleaned)
            claim_id = f"claim_{len(claims) + 1}"
            claims.append(
                ClaimItem(
                    claim_id=claim_id,
                    text=cleaned,
                    verdict="UNVERIFIED",
                    confidence=0.0,
                    explanation="Awaiting evidence verification.",
                    evidence=[]
                )
            )

        if len(claims) >= max_claims:
            break

    # If no declarative sentence passed strict filter, fallback to main statement
    if not claims and raw_sentences:
        first_clean = clean_sentence(raw_sentences[0])
        if len(first_clean) >= 15:
            claims.append(
                ClaimItem(
                    claim_id="claim_1",
                    text=first_clean,
                    verdict="UNVERIFIED",
                    confidence=0.0,
                    explanation="Primary statement identified for evaluation.",
                    evidence=[]
                )
            )

    return claims


def build_search_query(claim_text: str) -> str:
    """
    Generates a concise keyword search query from a claim statement.
    Strips noise words to optimize search relevance.
    """
    stop_words = {
        "the", "a", "an", "this", "that", "these", "those", "is", "are", "was", "were",
        "has", "have", "had", "will", "would", "shall", "should", "can", "could", "may",
        "might", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about",
        "into", "through", "during", "before", "after", "above", "below", "from", "up",
        "down", "in", "out", "on", "off", "over", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all", "any", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
        "don", "should", "now"
    }
    
    words = re.findall(r'\b[a-zA-Z0-9_-]+\b', claim_text)
    keywords = [w for w in words if w.lower() not in stop_words and len(w) > 2]
    return " ".join(keywords[:8])
