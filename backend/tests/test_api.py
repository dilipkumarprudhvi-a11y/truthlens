"""
Integration tests for FastAPI endpoints (/analyze, /health, /history, /stats, /url/extract).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_api_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "degraded")
    assert "nlp_available" in data
    assert data["mode"] == "evidence_grounded"


def test_api_analyze_valid_text(client):
    payload = {
        "text": "Scientists at the renewable energy laboratory confirmed a notable increase in solar power conversion efficiency."
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "scan_id" in data
    assert data["primary_verdict"] in ("SUPPORTED", "CONTRADICTED", "MIXED", "UNVERIFIED")
    assert "credibility_score" in data
    assert "linguistic_signals" in data
    assert "sentiment" in data
    assert "claims" in data


def test_api_analyze_input_too_short(client):
    res = client.post("/api/analyze", json={"text": "Short"})
    assert res.status_code in (400, 422)


def test_api_stats_endpoint(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "breakdown" in data
    assert "primary_verdicts" in data


def test_api_history_endpoints(client):
    # Test GET history
    res = client.get("/api/history")
    assert res.status_code == 200
    assert "history" in res.json()


def test_api_url_extract_ssrf_blocked(client):
    res = client.post("/api/url/extract", json={"url": "http://127.0.0.1:8000/internal"})
    assert res.status_code == 400
    assert "Security Error" in res.json()["detail"]
