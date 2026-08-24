"""
Unit tests for claim-evidence evaluation and composite aggregate scoring.
"""

import pytest
from backend.services.scoring import (
    evaluate_claim_against_evidence,
    compute_aggregate_verdict
)
from backend.services.linguistic import compute_sentiment, compute_clickbait, compute_bias, compute_readability, compute_writing_style, compute_virality_proxy
from backend.schemas.analysis import ClaimItem, EvidenceItem, LinguisticSignals


def test_claim_evaluation_supported():
    ev = EvidenceItem(
        source_name="Reuters",
        title="Solar Cell Breakthrough",
        url="https://reuters.com/tech",
        snippet="Verified and confirmed by international research teams.",
        authority_score=0.95,
        relevance_score=0.8
    )
    claim = ClaimItem(
        claim_id="claim_1",
        text="Solar energy efficiency improved significantly.",
        evidence=[ev]
    )
    evaluated = evaluate_claim_against_evidence(claim)
    assert evaluated.verdict == "SUPPORTED"
    assert evaluated.confidence > 50


def test_claim_evaluation_contradicted():
    ev = EvidenceItem(
        source_name="FactCheck Network",
        title="Debunked Hoax",
        url="https://factcheck.org/article",
        snippet="Fact-Check Rating: False. This viral conspiracy theory is completely debunked and fabricated.",
        authority_score=0.95,
        relevance_score=0.8
    )
    claim = ClaimItem(
        claim_id="claim_1",
        text="The government engineered a secret miracle cure.",
        evidence=[ev]
    )
    evaluated = evaluate_claim_against_evidence(claim)
    assert evaluated.verdict == "CONTRADICTED"
    assert evaluated.confidence > 60


def test_aggregate_verdict_deterministic_output():
    c1 = ClaimItem(
        claim_id="claim_1",
        text="Factual claim",
        verdict="SUPPORTED",
        confidence=80.0
    )
    ling = LinguisticSignals(
        sentiment=compute_sentiment("Scientific study confirmed positive results."),
        bias=compute_bias("Standard editorial review."),
        clickbait=compute_clickbait("Standard headline."),
        virality_risk=compute_virality_proxy(10, 0, 5),
        readability=compute_readability("This is a clean readable sentence."),
        writing_style=compute_writing_style("Standard text.")
    )

    v1, l1, cred1, fake1, conf1, msg1 = compute_aggregate_verdict([c1], ling)
    v2, l2, cred2, fake2, conf2, msg2 = compute_aggregate_verdict([c1], ling)

    assert v1 == v2 == "SUPPORTED"
    assert cred1 == cred2
    assert fake1 == fake2
    assert conf1 == conf2
    assert cred1 >= 60.0


# ─── FALSE POSITIVE REGRESSION TESTS ──────────────────────────────────────────

def _make_ling(text: str) -> LinguisticSignals:
    """Helper: build LinguisticSignals from raw text."""
    from backend.services.linguistic import (
        compute_sentiment, compute_clickbait, compute_bias,
        compute_readability, compute_writing_style, compute_virality_proxy,
        extract_suspicious_keywords,
    )
    sent  = compute_sentiment(text)
    cb    = compute_clickbait(text)
    bias  = compute_bias(text)
    read  = compute_readability(text)
    style = compute_writing_style(text)
    vir   = compute_virality_proxy(cb.score, sent.fear_pct, sent.negative_pct)
    kw    = extract_suspicious_keywords(text)
    return LinguisticSignals(
        sentiment=sent, bias=bias, clickbait=cb,
        virality_risk=vir, readability=read, writing_style=style,
        triggered_keywords=kw,
    )


def test_no_false_positive_on_breaking_news():
    """BREAKING NEWS headlines should NOT be classified as FAKE."""
    text = "BREAKING: NASA announces new Artemis moon landing mission for 2026 following congressional approval."
    ling = _make_ling(text)
    _, legacy, cred, fake, _, _ = compute_aggregate_verdict([], ling)
    assert legacy == "REAL", f"Breaking news falsely classified as {legacy}"
    assert cred >= 60.0, f"Credibility too low for legit news: {cred}"


def test_no_false_positive_on_truth_word():
    """The word 'truth' in a journalistic context should NOT trigger deception flags."""
    text = "The government confirmed the truth about the new policy changes affecting workers."
    ling = _make_ling(text)
    assert "truth" not in ling.triggered_keywords, "'truth' should not be a deception keyword"
    _, legacy, cred, _, _, _ = compute_aggregate_verdict([], ling)
    assert legacy == "REAL", f"Legit sentence with 'truth' classified as {legacy}"


def test_no_false_positive_on_scientific_news():
    """Scientific peer-reviewed news should not be flagged as fake."""
    text = "Researchers at Oxford published peer-reviewed findings on malaria vaccine efficacy showing 78% protection."
    ling = _make_ling(text)
    _, legacy, cred, fake, _, _ = compute_aggregate_verdict([], ling)
    assert legacy == "REAL", f"Scientific news classified as {legacy}"
    assert cred >= 65.0


def test_disinfo_detected_tier1():
    """Clear misinformation patterns (illuminati, new world order, etc.) should score as suspicious/fake."""
    text = "The illuminati new world order globalist plot is destroying our country. Wake up sheeple!"
    ling = _make_ling(text)
    assert len(ling.triggered_keywords) >= 2, "Should detect multiple deception keywords"
    _, legacy, cred, fake, _, _ = compute_aggregate_verdict([], ling)
    assert legacy in ("SUSPICIOUS", "FAKE"), f"Clear disinfo not flagged: got {legacy}"


def test_disinfo_detected_clickbait_extreme():
    """Extreme clickbait with fake-cure language should be flagged."""
    text = "SHOCKING: Secret miracle cure!!! What doctors are hiding! Banned forever! They don't want you to know!"
    ling = _make_ling(text)
    _, legacy, cred, fake, _, _ = compute_aggregate_verdict([], ling)
    assert legacy in ("SUSPICIOUS", "FAKE"), f"Extreme clickbait not flagged: got {legacy}"
    assert fake > 40


def test_no_false_positive_on_negative_news():
    """Negative news (disasters, crime, etc.) should not be flagged just for negative sentiment."""
    text = "A deadly earthquake struck the coastal region, killing dozens of people. Emergency services are responding to the disaster."
    ling = _make_ling(text)
    kw = ling.triggered_keywords
    assert len(kw) == 0, f"Negative news incorrectly triggered: {kw}"
    _, legacy, cred, _, _, _ = compute_aggregate_verdict([], ling)
    assert legacy == "REAL", f"Legitimate disaster news classified as {legacy}"

