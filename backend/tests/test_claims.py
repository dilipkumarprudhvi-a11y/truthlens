"""
Unit tests for factual claim extraction and sentence filtering.
"""

import pytest
from backend.services.claims import (
    extract_claims,
    is_factual_claim,
    build_search_query
)


def test_factual_claim_extraction():
    text = (
        "Good morning everyone! "
        "NASA scientists discovered high concentrations of water ice on the south pole of the Moon. "
        "What do you think about space exploration? "
        "The international team published their peer-reviewed findings in the planetary science journal."
    )

    claims = extract_claims(text)
    assert len(claims) >= 1
    assert any("NASA" in c.text for c in claims)
    # Ensure questions are filtered out
    assert not any(c.text.endswith("?") for c in claims)
    # Ensure greetings are filtered out
    assert not any("Good morning" in c.text for c in claims)


def test_is_factual_claim_filter():
    assert is_factual_claim("The government signed a bilateral trade agreement with European partners.") is True
    assert is_factual_claim("What time does the conference begin today?") is False
    assert is_factual_claim("In my personal opinion, that movie was terrible.") is False
    assert is_factual_claim("Hi!") is False


def test_build_search_query():
    claim = "Global health organizations announced a major reduction in malaria transmission rates."
    query = build_search_query(claim)
    assert "malaria" in query
    assert "announced" in query or "transmission" in query
    assert "the" not in query.split()
