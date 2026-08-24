"""
Evidence Retrieval Service
Provider interface and real search integrations (DuckDuckGo, Wikipedia, Google Fact Check).
Adheres strictly to the rule: NEVER fabricate evidence or claim sources verified unless queried.
"""

import os
import re
import urllib.parse
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import httpx
from ..schemas.analysis import EvidenceItem

# Domain Authority Registry
REPUTABLE_DOMAINS: Dict[str, float] = {
    "reuters.com": 0.95,
    "apnews.com": 0.95,
    "bbc.com": 0.92,
    "bbc.co.uk": 0.92,
    "nature.com": 0.95,
    "science.org": 0.95,
    "nejm.org": 0.95,
    "who.int": 0.94,
    "cdc.gov": 0.94,
    "nasa.gov": 0.94,
    "nih.gov": 0.94,
    "wikipedia.org": 0.85,
    "factcheck.org": 0.92,
    "snopes.com": 0.90,
    "politifact.com": 0.90,
    "nytimes.com": 0.88,
    "wsj.com": 0.88,
    "theguardian.com": 0.87,
    "washingtonpost.com": 0.87,
    "bloomberg.com": 0.88,
}


def calculate_domain_authority(url: str) -> float:
    """Calculates authority score based on domain reputation registry."""
    try:
        domain = urllib.parse.urlparse(url).netloc.lower()
        domain = re.sub(r'^www\.', '', domain)
        for known_domain, score in REPUTABLE_DOMAINS.items():
            if domain == known_domain or domain.endswith("." + known_domain):
                return score
        if domain.endswith(".edu") or domain.endswith(".gov"):
            return 0.90
        if domain.endswith(".org"):
            return 0.70
        return 0.50
    except Exception:
        return 0.40


def calculate_relevance(claim: str, title: str, snippet: str) -> float:
    """Computes keyword overlap relevance score between claim and evidence snippet."""
    claim_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', claim.lower()))
    if not claim_words:
        return 0.5
    
    evidence_text = f"{title} {snippet}".lower()
    evidence_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', evidence_text))
    
    overlap = len(claim_words.intersection(evidence_words))
    return round(min(1.0, overlap / max(1, len(claim_words) * 0.5)), 2)


class EvidenceProvider(ABC):
    """Abstract interface for factual evidence retrieval providers."""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 3) -> List[EvidenceItem]:
        """Searches for authoritative evidence matching the query."""
        pass


class WikipediaEvidenceProvider(EvidenceProvider):
    """Retrieves factual background and context from Wikipedia OpenSearch API."""
    
    API_URL = "https://en.wikipedia.org/w/api.php"

    async def search(self, query: str, max_results: int = 2) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        if not query.strip():
            return items

        params = {
            "action": "opensearch",
            "search": query,
            "limit": max_results,
            "namespace": 0,
            "format": "json"
        }
        headers = {"User-Agent": "TruthLens/3.0 (misinformation-research-agent; contact@truthlens.ai)"}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(self.API_URL, params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    # OpenSearch format: [query, [titles], [descriptions], [urls]]
                    if len(data) >= 4 and isinstance(data[1], list):
                        titles = data[1]
                        descriptions = data[2]
                        urls = data[3]
                        for t, desc, u in zip(titles, descriptions, urls):
                            if desc and "may refer to:" not in desc:
                                items.append(
                                    EvidenceItem(
                                        source_name="Wikipedia Encyclopedia",
                                        title=t,
                                        url=u,
                                        snippet=desc[:300],
                                        source_type="encyclopedia",
                                        authority_score=0.85,
                                        relevance_score=calculate_relevance(query, t, desc)
                                    )
                                )
        except Exception:
            # Network or timeout failure gracefully yields empty list
            pass

        return items


class DuckDuckGoEvidenceProvider(EvidenceProvider):
    """Queries DuckDuckGo Instant Answer API for live verified public data."""
    
    API_URL = "https://api.duckduckgo.com/"

    async def search(self, query: str, max_results: int = 2) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        if not query.strip():
            return items

        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        headers = {"User-Agent": "TruthLens/3.0"}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(self.API_URL, params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    abstract = data.get("AbstractText", "")
                    heading = data.get("Heading", query)
                    url = data.get("AbstractURL", "")
                    source = data.get("AbstractSource", "DuckDuckGo Knowledge Index")

                    if abstract:
                        items.append(
                            EvidenceItem(
                                source_name=source,
                                title=heading,
                                url=url or "https://duckduckgo.com",
                                snippet=abstract[:300],
                                source_type="search_index",
                                authority_score=calculate_domain_authority(url),
                                relevance_score=calculate_relevance(query, heading, abstract)
                            )
                        )
        except Exception:
            pass

        return items


class GoogleFactCheckEvidenceProvider(EvidenceProvider):
    """Queries Google Fact Check Tools API when configured with an API key."""
    
    API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_FACTCHECK_API_KEY", "")

    async def search(self, query: str, max_results: int = 3) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        if not self.api_key or not query.strip():
            return items

        params = {
            "query": query,
            "pageSize": max_results,
            "key": self.api_key
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(self.API_URL, params=params)
                if res.status_code == 200:
                    data = res.json()
                    claims = data.get("claims", [])
                    for c in claims:
                        reviews = c.get("claimReview", [])
                        for rev in reviews:
                            publisher = rev.get("publisher", {}).get("name", "Fact-Checker")
                            site_url = rev.get("publisher", {}).get("site", "")
                            rating = rev.get("textualRating", "Unrated")
                            title = rev.get("title", c.get("text", query))
                            review_url = rev.get("url", site_url)
                            
                            snippet = f"Claim Evaluated: '{c.get('text', '')}'. Fact-Check Rating: {rating}."

                            items.append(
                                EvidenceItem(
                                    source_name=publisher,
                                    title=title,
                                    url=review_url,
                                    published_at=rev.get("reviewDate"),
                                    snippet=snippet,
                                    source_type="fact_check_database",
                                    authority_score=0.95,
                                    relevance_score=calculate_relevance(query, title, snippet)
                                )
                            )
        except Exception:
            pass

        return items


class CompositeEvidenceAggregator:
    """Aggregates and ranks evidence across all active providers."""
    
    def __init__(self, providers: Optional[List[EvidenceProvider]] = None):
        if providers is not None:
            self.providers = providers
        else:
            self.providers = [
                GoogleFactCheckEvidenceProvider(),
                DuckDuckGoEvidenceProvider(),
                WikipediaEvidenceProvider()
            ]

    async def retrieve_evidence_for_claim(self, claim_text: str, search_query: str) -> List[EvidenceItem]:
        """Queries providers and returns deduplicated, ranked evidence items."""
        all_items: List[EvidenceItem] = []
        seen_urls = set()

        for provider in self.providers:
            try:
                results = await provider.search(search_query, max_results=2)
                for item in results:
                    norm_url = item.url.rstrip('/')
                    if norm_url and norm_url not in seen_urls:
                        seen_urls.add(norm_url)
                        all_items.append(item)
            except Exception:
                continue

        # Sort evidence by authority_score * relevance_score descending
        all_items.sort(key=lambda x: (x.authority_score * 0.6 + x.relevance_score * 0.4), reverse=True)
        return all_items[:4]
