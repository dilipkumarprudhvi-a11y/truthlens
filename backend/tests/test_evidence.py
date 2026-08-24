"""
Unit tests for evidence retrieval providers, authority ranking, and relevance scoring.
"""

import asyncio
import pytest
from backend.services.evidence import (
    calculate_domain_authority,
    calculate_relevance,
    WikipediaEvidenceProvider,
    CompositeEvidenceAggregator,
    EvidenceProvider,
)
from backend.schemas.analysis import EvidenceItem


def test_domain_authority_ranking():
    assert calculate_domain_authority("https://www.reuters.com/world/article") == 0.95
    assert calculate_domain_authority("https://en.wikipedia.org/wiki/Solar_cell") == 0.85
    assert calculate_domain_authority("https://random-blog-post-123.xyz/news") == 0.50


def test_relevance_calculation():
    claim = "Solar energy efficiency increased by 30 percent in lab tests."
    title = "Perovskite Solar Cell Efficiency Breakthrough"
    snippet = "Researchers record a 30 percent increase in solar cell energy output."
    
    score = calculate_relevance(claim, title, snippet)
    assert score >= 0.40


def test_composite_evidence_empty_fallback():
    class DummyEmptyProvider(EvidenceProvider):
        async def search(self, query: str, max_results: int = 3):
            return []

    aggregator = CompositeEvidenceAggregator(providers=[DummyEmptyProvider()])
    evidence = asyncio.run(aggregator.retrieve_evidence_for_claim("Test claim", "Test query"))
    assert isinstance(evidence, list)
    assert len(evidence) == 0  # Strictly never fabricates fake evidence
