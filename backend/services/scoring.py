"""
Deterministic Scoring and Evidence Comparison Engine
Calculates claim-level verdicts and transparent composite credibility ratings.

DESIGN PRINCIPLES:
- Strictly deterministic: No random numbers, ever.
- Linguistic risk is a signal, not a verdict. High clickbait ≠ false claim.
- UNVERIFIED means "insufficient evidence found", not necessarily fake.
- The FAKE/SUSPICIOUS legacy labels map conservatively to avoid false positives.
"""

import re
from typing import List, Tuple
from ..schemas.analysis import ClaimItem, EvidenceItem, LinguisticSignals

# Evidence comparison markers
# These must be found in evidence SNIPPETS (not the article being analyzed)
REFUTATION_MARKERS = {
    "false", "debunked", "hoax", "fabricated", "untrue", "misleading", "incorrect",
    "disproved", "no evidence", "refuted", "inaccurate", "pseudoscience"
}

AFFIRMATION_MARKERS = {
    "confirmed", "peer-reviewed", "demonstrated", "announced", "published",
    "documented", "official study", "clinical trial", "concluded that", "evidence shows",
    "research shows", "study finds", "scientists found"
}


def evaluate_claim_against_evidence(claim: ClaimItem) -> ClaimItem:
    """
    Compares a single claim against its retrieved evidence items and assigns a verdict.
    
    Verdict logic:
    - SUPPORTED: evidence contains affirmation markers with high relevance and no major refutation
    - CONTRADICTED: evidence contains explicit refutation markers (debunked, hoax, false)
    - MIXED: both affirmation and refutation signals present
    - UNVERIFIED: no strong signal either way (most common for obscure/recent claims)
    """
    if not claim.evidence:
        claim.verdict = "UNVERIFIED"
        claim.confidence = 40.0
        claim.explanation = (
            "No independent corroborating or refuting evidence was found in indexed "
            "public knowledge repositories. This does not imply the claim is false."
        )
        return claim

    refute_score = 0.0
    support_score = 0.0

    for ev in claim.evidence:
        snippet_lower = ev.snippet.lower()
        authority = ev.authority_score
        relevance = ev.relevance_score

        # Direct fact-check ratings take priority (highest weight)
        if "fact-check rating: false" in snippet_lower or "fact-check rating: misleading" in snippet_lower:
            refute_score += 2.5 * authority
            continue
        elif "fact-check rating: true" in snippet_lower or "fact-check rating: correct" in snippet_lower:
            support_score += 2.5 * authority
            continue

        # Marker-based scoring
        has_refute = any(rm in snippet_lower for rm in REFUTATION_MARKERS)
        has_affirm = any(am in snippet_lower for am in AFFIRMATION_MARKERS)

        # Only count if the evidence is actually relevant to the claim
        if has_refute and relevance >= 0.4:
            refute_score += 1.2 * authority * relevance
        elif has_affirm and relevance >= 0.4:
            support_score += 1.0 * authority * relevance
        elif relevance >= 0.55:
            # Background context — small positive signal
            support_score += 0.4 * authority * relevance

    # Verdict assignment with conservative thresholds
    if refute_score > support_score and refute_score >= 0.7:
        claim.verdict = "CONTRADICTED"
        claim.confidence = round(min(92.0, 55.0 + (refute_score * 20.0)), 1)
        claim.explanation = (
            f"Evidence retrieved from {claim.evidence[0].source_name} contains "
            f"refutation signals for this assertion."
        )
    elif support_score > refute_score and support_score >= 0.6:
        claim.verdict = "SUPPORTED"
        claim.confidence = round(min(88.0, 55.0 + (support_score * 18.0)), 1)
        claim.explanation = (
            f"Evidence from {claim.evidence[0].source_name} contains corroborating "
            f"context for this assertion."
        )
    elif refute_score >= 0.35 and support_score >= 0.35:
        claim.verdict = "MIXED"
        claim.confidence = 62.0
        claim.explanation = "Conflicting signals found across evidence sources — context is disputed or complex."
    else:
        claim.verdict = "UNVERIFIED"
        claim.confidence = 45.0
        claim.explanation = (
            "Retrieved background context does not directly confirm or refute the specific "
            "factual assertion. More specialized sources may be required."
        )

    return claim


from .linguistic import DECEPTION_TIER1, DECEPTION_TIER2


def compute_aggregate_verdict(
    claims: List[ClaimItem],
    linguistic: LinguisticSignals
) -> Tuple[str, str, float, float, float, str]:
    """
    Computes the overall verdict, credibility score, deception probability, and message.

    ACCURACY PRINCIPLES:
    1. Clean journalistic text with no deception signals -> REAL (credibility 75-88%, fake prob 12-25%)
    2. Flagged misinformation, hoaxes, medical cures, conspiracy claims -> FAKE (fake prob 75-95%)
    3. Moderate clickbait or sensationalism -> SUSPICIOUS (fake prob 45-65%)
    4. Evidence contradictions -> FAKE (fake prob 80-95%)
    5. Corroborated evidence -> REAL (credibility 80-95%)
    """
    # ─── Evidence-based counts ────────────────────────────────────────────────
    total_claims = len(claims) if claims else 0
    supp_count = sum(1 for c in claims if c.verdict == "SUPPORTED") if claims else 0
    cont_count = sum(1 for c in claims if c.verdict == "CONTRADICTED") if claims else 0
    mix_count  = sum(1 for c in claims if c.verdict == "MIXED") if claims else 0

    # ─── Linguistic risk evaluation ───────────────────────────────────────────
    cb_score = linguistic.clickbait.score
    fear_pct  = linguistic.sentiment.fear_pct
    triggers = linguistic.triggered_keywords or []
    
    tier1_set = set(DECEPTION_TIER1)
    tier1_flags = len([k for k in triggers if k in tier1_set])
    tier2_flags = len(triggers) - tier1_flags

    # Tier 1 flags are decisive misinformation signals (45 pts each, max 75 pts)
    # Tier 2 flags are sensationalism modifiers (12 pts each, max 30 pts)
    ling_penalty = 0.0
    ling_penalty += min(75.0, tier1_flags * 45.0)
    ling_penalty += min(30.0, tier2_flags * 12.0)

    # Clickbait and alarmist fear penalties
    if cb_score >= 60 and fear_pct >= 20:
        ling_penalty += 25.0
    elif cb_score >= 40:
        ling_penalty += 15.0
    elif fear_pct >= 20:
        ling_penalty += 10.0

    if "High Polarization" in linguistic.bias.leaning:
        ling_penalty += 10.0

    ling_penalty = min(80.0, ling_penalty)

    # ─── Base credibility from evidence ──────────────────────────────────────
    if total_claims == 0:
        base_score = 78.0
    elif cont_count > 0 and cont_count >= max(1, total_claims / 2):
        # Majority contradicted by evidence
        base_score = max(10.0, 35.0 - (cont_count / total_claims) * 25.0)
    elif supp_count > 0 and cont_count == 0:
        # Supported by evidence
        base_score = min(92.0, 78.0 + (supp_count / max(1, total_claims)) * 14.0)
    elif mix_count > 0:
        base_score = 50.0
    elif cont_count > 0:
        base_score = 35.0
    else:
        base_score = 78.0

    final_credibility = max(5.0, min(95.0, base_score - ling_penalty))
    fake_probability = round(100.0 - final_credibility, 1)
    final_credibility = round(final_credibility, 1)

    # ─── Primary scientific verdict assignment ────────────────────────────────
    if cont_count > 0 or final_credibility <= 35.0 or tier1_flags >= 2 or (tier1_flags >= 1 and cb_score >= 40):
        # Definite FAKE / CONTRADICTED
        primary_verdict = "CONTRADICTED" if cont_count > 0 else "FLAGGED"
        legacy_class = "FAKE"
        msg = "Content contains refuted claims, severe conspiracy patterns, or known misinformation triggers."
        confidence = min(92.0, max(70.0, 55.0 + (tier1_flags * 12.0) + (cont_count * 15.0)))

    elif tier1_flags >= 1 or (40.0 <= fake_probability < 65.0) or mix_count > 0:
        # SUSPICIOUS / MIXED
        primary_verdict = "MIXED" if mix_count > 0 else "SUSPICIOUS"
        legacy_class = "SUSPICIOUS"
        msg = "Content displays elevated sensationalism, unverified claims, or mixed evidence signals."
        confidence = 62.0

    elif supp_count > 0 and cont_count == 0:
        # Confirmed REAL
        primary_verdict = "SUPPORTED"
        legacy_class = "REAL"
        msg = "Core assertions are corroborated by verified context in public knowledge sources."
        confidence = min(90.0, 68.0 + supp_count * 10.0)

    else:
        # Clean journalistic text without misinformation triggers
        if final_credibility >= 65.0:
            primary_verdict = "SUPPORTED"
            legacy_class = "REAL"
            msg = "Content adheres to standard objective journalistic style with no deception signals detected."
            confidence = round(min(80.0, max(60.0, final_credibility * 0.85)), 1)
        elif final_credibility >= 45.0:
            primary_verdict = "SUSPICIOUS"
            legacy_class = "SUSPICIOUS"
            msg = "Unverified claims with moderate risk markers. Independent verification is recommended."
            confidence = 55.0
        else:
            primary_verdict = "FLAGGED"
            legacy_class = "FAKE"
            msg = "High linguistic risk combined with unverifiable assertions."
            confidence = 68.0

    return primary_verdict, legacy_class, final_credibility, fake_probability, round(confidence, 1), msg
