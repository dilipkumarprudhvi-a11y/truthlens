from .linguistic import analyze_linguistic_signals, NLP_AVAILABLE
from .claims import extract_claims, build_search_query
from .evidence import (
    EvidenceProvider,
    WikipediaEvidenceProvider,
    DuckDuckGoEvidenceProvider,
    GoogleFactCheckEvidenceProvider,
    CompositeEvidenceAggregator,
)
from .scoring import evaluate_claim_against_evidence, compute_aggregate_verdict
from .analyzer import TruthLensAnalyzer
from .url_extractor import extract_url_content, is_safe_url
from .ocr import extract_text_from_image, validate_image_upload

__all__ = [
    "analyze_linguistic_signals",
    "NLP_AVAILABLE",
    "extract_claims",
    "build_search_query",
    "EvidenceProvider",
    "WikipediaEvidenceProvider",
    "DuckDuckGoEvidenceProvider",
    "GoogleFactCheckEvidenceProvider",
    "CompositeEvidenceAggregator",
    "evaluate_claim_against_evidence",
    "compute_aggregate_verdict",
    "TruthLensAnalyzer",
    "extract_url_content",
    "is_safe_url",
    "extract_text_from_image",
    "validate_image_upload",
]
