"""
Deterministic Scoring and Evidence Comparison Engine
Calculates claim-level verdicts and transparent composite credibility ratings.
Strictly deterministic: No random numbers.
"""

import re
from typing import List, Tuple, Dict, Any
from ..schemas.analysis import (
    ClaimItem,
    EvidenceItem,
    LinguisticSignals,
)

REFUTATION_MARKERS = {
    "false", "debunked", "hoax", "fabricated", "untrue", "misleading", "incorrect",
    "disproved", "no evidence", "refuted", "inaccurate", "pseudoscience", "conspiracy"
}

AFFIRMATION_MARKERS = {
    "confirmed", "verified", "peer-reviewed", "demonstrated", "announced", "published",
    "documented", "proven", "official", "evidence shows", "concluded that"
}


def evaluate_claim_against_evidence(claim: ClaimItem) -> ClaimItem:
    """
    Compares a single claim against its retrieved evidence items and assigns a verdict.
    """
    if not claim.evidence:
        claim.verdict = "UNVERIFIED"
        claim.confidence = 40.0
        claim.explanation = "No external corroborating or refuting evidence was found in indexed knowledge repositories."
        return claim

    claim_text_lower = claim.text.lower()
    refute_score = 0.0
    support_score = 0.0
    total_authority = 0.0

    for ev in claim.evidence:
        snippet_lower = ev.snippet.lower()
        authority = ev.authority_score
        relevance = ev.relevance_score
        total_authority += authority

        # Check for direct fact-check rating in snippet
        if "fact-check rating: false" in snippet_lower or "fact-check rating: misleading" in snippet_lower:
            refute_score += 2.0 * authority
            continue
        elif "fact-check rating: true" in snippet_lower or "fact-check rating: correct" in snippet_lower:
            support_score += 2.0 * authority
            continue

        # Check refutation vs affirmation markers in snippet
        has_refute = any(rm in snippet_lower for rm in REFUTATION_MARKERS)
        has_affirm = any(am in snippet_lower for am in AFFIRMATION_MARKERS)

        if has_refute and relevance >= 0.3:
            refute_score += 1.0 * authority * relevance
        elif has_affirm and relevance >= 0.3:
            support_score += 1.0 * authority * relevance
        elif relevance >= 0.5:
            support_score += 0.5 * authority * relevance

    if refute_score > support_score and refute_score >= 0.6:
        claim.verdict = "CONTRADICTED"
        claim.confidence = round(min(95.0, 50.0 + (refute_score * 25.0)), 1)
        claim.explanation = f"Independent evidence from {claim.evidence[0].source_name} disputes this assertion."
    elif support_score > refute_score and support_score >= 0.6:
        claim.verdict = "SUPPORTED"
        claim.confidence = round(min(95.0, 50.0 + (support_score * 25.0)), 1)
        claim.explanation = f"Corroborated by reports from {claim.evidence[0].source_name}."
    elif refute_score > 0.3 and support_score > 0.3:
        claim.verdict = "MIXED"
        claim.confidence = 65.0
        claim.explanation = "Conflicting evidence or disputed context found across reporting sources."
    else:
        claim.verdict = "UNVERIFIED"
        claim.confidence = 45.0
        claim.explanation = "Retrieved background context does not directly substantiate or refute the specific claim."

    return claim


def compute_aggregate_verdict(
    claims: List[ClaimItem],
    linguistic: LinguisticSignals
) -> Tuple[str, str, float, float, float, str]:
    """
    Computes overall primary verdict, legacy classification, credibility score,
    fake probability, confidence index, and human-readable narrative.
    """
    # 1. Base linguistic risk penalty (0 to 60 points deducted)
    ling_penalty = 0.0
    ling_penalty += (linguistic.clickbait.score * 0.30)
    ling_penalty += (linguistic.sentiment.fear_pct * 0.25)
    ling_penalty += (len(linguistic.triggered_keywords) * 8.0)
    if "Polarization" in linguistic.bias.leaning:
        ling_penalty += 10.0
    ling_penalty = min(70.0, ling_penalty)

    total_claims = len(claims) if claims else 0
    supp_count = sum(1 for c in claims if c.verdict == "SUPPORTED") if claims else 0
    cont_count = sum(1 for c in claims if c.verdict == "CONTRADICTED") if claims else 0
    mix_count = sum(1 for c in claims if c.verdict == "MIXED") if claims else 0
    unv_count = sum(1 for c in claims if c.verdict == "UNVERIFIED") if claims else 0

    # 2. Base Evidence Score
    if total_claims == 0:
        base_score = 80.0
    elif supp_count > 0 and cont_count == 0:
        base_score = 85.0 + ((supp_count / total_claims) * 10.0)
    elif cont_count > 0:
        base_score = 30.0 - ((cont_count / total_claims) * 25.0)
    elif mix_count > 0:
        base_score = 50.0
    else:
        # Unverified claims: Clean journalistic text starts at 80, deceptive styling drops it
        base_score = 80.0

    final_credibility = max(5.0, min(95.0, base_score - ling_penalty))
    fake_probability = round(100.0 - final_credibility, 1)
    final_credibility = round(final_credibility, 1)

    # 3. Determine Primary Scientific Verdict & Legacy Classification
    if cont_count >= max(1, total_claims / 2) or (cont_count > 0 and final_credibility < 40) or (ling_penalty >= 45.0):
        primary_verdict = "CONTRADICTED" if cont_count > 0 else "UNVERIFIED"
        legacy_class = "FAKE"
        msg = "Content exhibits high deception patterns or is contradicted by verified evidence."
        confidence = min(95.0, 65.0 + (cont_count * 15.0) + (ling_penalty * 0.2))
    elif supp_count >= max(1, total_claims / 2) and cont_count == 0 and final_credibility >= 65:
        primary_verdict = "SUPPORTED"
        legacy_class = "REAL"
        msg = "Core assertions are corroborated by authoritative knowledge and wire records."
        confidence = min(95.0, 65.0 + (supp_count * 15.0))
    elif mix_count > 0 or (supp_count > 0 and cont_count > 0):
        primary_verdict = "MIXED"
        legacy_class = "SUSPICIOUS"
        msg = "Mixed reporting: content contains both substantiated statements and disputed claims."
        confidence = 65.0
    else:
        primary_verdict = "UNVERIFIED"
        legacy_class = "REAL" if final_credibility >= 55.0 else "SUSPICIOUS" if final_credibility >= 35.0 else "FAKE"
        msg = "Standard reporting structure. Independent evidence verification is limited in indexed repositories."
        confidence = 50.0

    return primary_verdict, legacy_class, final_credibility, fake_probability, round(confidence, 1), msg
