"""
FastAPI Dependencies: Database Sessions, Rate Limiting, and Service Injection
"""

import time
from typing import Dict, List
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.analyzer import TruthLensAnalyzer

# In-memory sliding window rate limiter
RATE_LIMIT_PER_MINUTE = 40
client_request_history: Dict[str, List[float]] = {}


def check_rate_limit(request: Request):
    """
    Sliding window rate limit checker per client IP.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    # Respect X-Forwarded-For if behind a reverse proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    now = time.time()
    window_start = now - 60.0

    # Filter out requests older than 60s
    timestamps = client_request_history.get(client_ip, [])
    timestamps = [t for t in timestamps if t > window_start]

    if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 40 requests per minute allowed. Please try again shortly."
        )

    timestamps.append(now)
    client_request_history[client_ip] = timestamps


def get_analyzer() -> TruthLensAnalyzer:
    """Dependency provider for the master TruthLens analyzer."""
    return TruthLensAnalyzer()
