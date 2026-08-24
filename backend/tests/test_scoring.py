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
