"""
TruthLens API Routes
Standardized REST endpoints for forensic analysis, URL ingestion, OCR, history, and stats.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    UrlExtractRequest,
    UrlExtractResponse,
    OcrExtractResponse,
    HistoryResponse,
    HistoryItem,
    StatsResponse,
)
from ..db.session import get_db
from ..db.models import Scan, ClaimRecord, EvidenceRecord
from ..services.analyzer import TruthLensAnalyzer
from ..services.url_extractor import extract_url_content
from ..services.ocr import extract_text_from_image
from ..services.linguistic import NLP_AVAILABLE
from .dependencies import check_rate_limit, get_analyzer

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_rate_limit)],
    summary="Analyze text for credibility, factual claims, and linguistic risk signals"
)
async def analyze_content(
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
    analyzer: TruthLensAnalyzer = Depends(get_analyzer)
):
    """
    Executes complete evidence-grounded verification pipeline:
    - Extracts factual declarative claims
    - Gathers corroborating/refuting evidence from live sources
    - Computes deterministic linguistic and style vectors
    - Produces explainable primary verdict (SUPPORTED, CONTRADICTED, MIXED, UNVERIFIED)
    """
    text = payload.text.strip()
    if len(text) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text too short. Minimum 10 characters required for forensic analysis."
        )

    if len(text) > 25000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Input text exceeds maximum allowed length of 25,000 characters."
        )

    response = await analyzer.analyze(text=text, source_url=payload.source_url, db=db)
    return response


@router.post(
    "/url/extract",
    response_model=UrlExtractResponse,
    dependencies=[Depends(check_rate_limit)],
    summary="Securely fetch and extract article body from a public web URL"
)
async def extract_url(payload: UrlExtractRequest):
    """
    Server-side URL extractor protected against SSRF, internal address leakage, and timeouts.
    """
    url = payload.url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target URL parameter cannot be empty."
        )

    res = await extract_url_content(url)
    if not res.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.error or "Failed to extract web content from target URL."
        )
    return res


@router.post(
    "/ocr/extract",
    response_model=OcrExtractResponse,
    dependencies=[Depends(check_rate_limit)],
    summary="Extract text from an image or screenshot using OCR"
)
async def extract_image_text(file: UploadFile = File(...)):
    """
    Validates uploaded image and extracts text using Tesseract OCR.
    """
    content_type = file.content_type or "image/png"
    file_bytes = await file.read()

    res = await extract_text_from_image(file_bytes, content_type)
    return res


@router.get("/history", response_model=HistoryResponse, summary="Get recent analysis logs")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    """Fetches anonymized recent scan records."""
    limit = min(50, max(1, limit))
    rows = db.query(Scan).order_by(Scan.id.desc()).limit(limit).all()

    items = [
        HistoryItem(
            id=r.id,
            scan_id=r.scan_id,
            timestamp=r.created_at.isoformat(),
            snippet=r.snippet,
            classification=r.legacy_classification,
            primary_verdict=r.primary_verdict,
            credibility_score=r.credibility_score,
            fake_probability=r.fake_probability
        )
        for r in rows
    ]
    return HistoryResponse(history=items, total=len(items))


@router.delete("/history", summary="Clear all history logs")
def clear_history(db: Session = Depends(get_db)):
    """Clears all stored scan and claim history."""
    try:
        db.query(EvidenceRecord).delete()
        db.query(ClaimRecord).delete()
        db.query(Scan).delete()
        db.commit()
        return {"status": "success", "message": "History records cleared successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse, summary="Aggregate distribution statistics")
def get_stats(db: Session = Depends(get_db)):
    """Returns aggregate distribution of real, suspicious, fake, and supported verdicts."""
    total = db.query(Scan).count()
    if total == 0:
        return StatsResponse(
            total=0,
            breakdown={"REAL": 0, "SUSPICIOUS": 0, "FAKE": 0},
            primary_verdicts={"SUPPORTED": 0, "CONTRADICTED": 0, "MIXED": 0, "UNVERIFIED": 0},
            avg_credibility=50.0,
            avg_fake_probability=50.0
        )

    # Breakdown by legacy class
    legacy_groups = db.query(Scan.legacy_classification, func.count(Scan.id)).group_by(Scan.legacy_classification).all()
    breakdown = {k: v for k, v in legacy_groups if k}

    # Breakdown by primary scientific verdict
    verdict_groups = db.query(Scan.primary_verdict, func.count(Scan.id)).group_by(Scan.primary_verdict).all()
    primary_verdicts = {k: v for k, v in verdict_groups if k}

    avg_cred = db.query(func.avg(Scan.credibility_score)).scalar() or 50.0
    avg_fake = db.query(func.avg(Scan.fake_probability)).scalar() or 50.0

    return StatsResponse(
        total=total,
        breakdown=breakdown,
        primary_verdicts=primary_verdicts,
        avg_credibility=round(float(avg_cred), 1),
        avg_fake_probability=round(float(avg_fake), 1)
    )


@router.get("/health", summary="Service health and NLP readiness")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint distinguishing API status, database connectivity, and NLP availability."""
    db_ok = True
    try:
        db.execute(func.now()).scalar()
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "api_version": "3.0.0",
        "nlp_available": NLP_AVAILABLE,
        "database_connected": db_ok,
        "mode": "evidence_grounded"
    }
