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


def compute_aggregate_verdict(
    claims: List[ClaimItem],
    linguistic: LinguisticSignals
) -> Tuple[str, str, float, float, float, str]:
    """
    Computes the overall verdict, credibility score, deception probability, and message.

    KEY DESIGN DECISIONS:
    1. Linguistic risk is a modifier, not the primary signal.
       - Clean journalistic text with UNVERIFIED claims is NOT fake.
       - Only EXTREME linguistic manipulation (clickbait≥70 AND fear≥25%) significantly penalizes.
    2. UNVERIFIED + low linguistic risk = REAL (we simply didn't find enough evidence)
    3. FAKE label requires strong evidence (actual contradictions OR extreme deception signals)
    4. The 'fake_probability' is not a calibrated probability — it's a relative risk estimate.
    """
    # ─── Evidence-based counts ────────────────────────────────────────────────
    total_claims = len(claims) if claims else 0
    supp_count = sum(1 for c in claims if c.verdict == "SUPPORTED") if claims else 0
    cont_count = sum(1 for c in claims if c.verdict == "CONTRADICTED") if claims else 0
    mix_count  = sum(1 for c in claims if c.verdict == "MIXED") if claims else 0

    # ─── Linguistic risk penalty (conservative) ───────────────────────────────
    # Only HIGH-CONFIDENCE deception signals contribute meaningfully.
    # Common journalistic language must NOT be penalized.
    cb_score = linguistic.clickbait.score
    fear_pct  = linguistic.sentiment.fear_pct
    tier1_flags = len([k for k in linguistic.triggered_keywords if k in [
        "illuminati", "deep state conspiracy", "magic cure", "mind control", "chemtrails",
        "new world order", "they don't want you to know", "secret cabal", "globalist plot",
        "miracle cure discovered", "doctors are hiding", "banned forever", "one weird trick",
        "what doctors won't tell you", "wake up sheeple", "reptilian",
        "miracle cure", "deep state", "secret conspiracy", "secret remedy",
        "globalist", "world government order", "globalist tyrant",
        "buy now before", "buy now and", "anonymous experts confirm",
    ]])
    tier2_flags = len(linguistic.triggered_keywords) - tier1_flags

    # Tier 1 flags are strong signals (max 60 pts), Tier 2 are weak (max 15 pts)
    ling_penalty = 0.0
    ling_penalty += min(60.0, tier1_flags * 20.0)
    ling_penalty += min(15.0, tier2_flags * 5.0)

    # Extreme clickbait (≥70) AND fear (≥25%) together signal manipulative framing
    if cb_score >= 70 and fear_pct >= 25:
        ling_penalty += 20.0
    elif cb_score >= 45 and fear_pct >= 15:
        ling_penalty += 8.0

    if "High Polarization" in linguistic.bias.leaning:
        ling_penalty += 8.0

    ling_penalty = min(70.0, ling_penalty)

    # ─── Base credibility from evidence ──────────────────────────────────────
    if total_claims == 0:
        # No extractable claims: judge purely on linguistic signals
        base_score = 78.0
    elif cont_count > 0 and cont_count >= total_claims / 2:
        # Majority of claims contradicted
        base_score = max(15.0, 45.0 - (cont_count / total_claims) * 30.0)
    elif supp_count > 0 and cont_count == 0:
        # All evaluated claims supported
        base_score = min(90.0, 75.0 + (supp_count / max(1, total_claims)) * 15.0)
    elif mix_count > 0:
        base_score = 55.0
    elif cont_count > 0:
        base_score = 45.0
    else:
        # All UNVERIFIED: not enough evidence, but not fake either
        base_score = 78.0

    final_credibility = max(5.0, min(95.0, base_score - ling_penalty))
    fake_probability = round(100.0 - final_credibility, 1)
    final_credibility = round(final_credibility, 1)

    # ─── Primary scientific verdict ───────────────────────────────────────────
    if cont_count > 0 and cont_count >= max(1, total_claims / 2):
        primary_verdict = "CONTRADICTED"
        legacy_class = "FAKE"
        msg = "One or more claims are contradicted by evidence retrieved from public knowledge sources."
        confidence = min(90.0, 60.0 + cont_count * 12.0)

    elif supp_count > 0 and cont_count == 0 and final_credibility >= 68:
        primary_verdict = "SUPPORTED"
        legacy_class = "REAL"
        msg = "Core assertions are corroborated by context in public knowledge sources."
        confidence = min(88.0, 62.0 + supp_count * 12.0)

    elif mix_count > 0 or (supp_count > 0 and cont_count > 0):
        primary_verdict = "MIXED"
        legacy_class = "SUSPICIOUS"
        msg = "Content contains a mix of substantiated statements and disputed or unverified claims."
        confidence = 62.0

    elif ling_penalty >= 55.0:
        # Extreme deception patterns without any counter-evidence: flag as suspicious
        primary_verdict = "UNVERIFIED"
        legacy_class = "SUSPICIOUS"
        msg = "Extreme manipulative language patterns detected. Claims could not be verified by evidence."
        confidence = 55.0

    else:
        # UNVERIFIED: this is the honest answer when evidence is simply not found
        # Map to REAL unless linguistic risk is elevated
        primary_verdict = "UNVERIFIED"
        if final_credibility >= 62:
            legacy_class = "REAL"
            msg = (
                "No matching verification records found in indexed public sources. "
                "The content uses standard journalistic structure with no strong deception signals. "
                "UNVERIFIED means insufficient evidence, not necessarily false."
            )
        elif final_credibility >= 40:
            legacy_class = "SUSPICIOUS"
            msg = (
                "Unverified claims with moderate linguistic risk signals. "
                "Independent source verification is recommended."
            )
        else:
            legacy_class = "FAKE"
            msg = "High linguistic risk combined with unverifiable claims."
        # Confidence reflects how strongly the linguistic analysis supports the classification.
        # No external evidence was found, so confidence is based on linguistic signal strength.
        if ling_penalty <= 5.0:
            # Clean journalistic text — high confidence it's credible
            confidence = round(min(75.0, final_credibility * 0.85), 1)
        elif ling_penalty <= 20.0:
            # Some mild signals — moderate confidence
            confidence = round(min(65.0, final_credibility * 0.75), 1)
        else:
            # Elevated linguistic risk — lower confidence in any direction
            confidence = round(max(35.0, final_credibility * 0.6), 1)

    return primary_verdict, legacy_class, final_credibility, fake_probability, round(confidence, 1), msg
