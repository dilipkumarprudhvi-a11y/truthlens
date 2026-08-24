"""
TruthLens Pydantic v2 Request and Response Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=25000, description="Article or text content to analyze")
    source_url: Optional[str] = Field(None, description="Optional original URL for source context")


class UrlExtractRequest(BaseModel):
    url: str = Field(..., description="Target web article URL to securely extract")


class UrlExtractResponse(BaseModel):
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    text: str
    length: int
    success: bool
    error: Optional[str] = None


class OcrExtractResponse(BaseModel):
    text: str
    confidence: float
    status: str
    note: str


class EvidenceItem(BaseModel):
    source_name: str
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: str
    source_type: str = "web"
    authority_score: float = 0.5
    relevance_score: float = 0.5


class ClaimItem(BaseModel):
    claim_id: str
    text: str
    verdict: str = "UNVERIFIED"  # SUPPORTED, CONTRADICTED, MIXED, UNVERIFIED
    confidence: float = 0.0
    explanation: str = ""
    evidence: List[EvidenceItem] = []


class SentimentSignal(BaseModel):
    tone: str
    positive_pct: int
    negative_pct: int
    fear_pct: int
    polarity_score: float


class BiasSignal(BaseModel):
    leaning: str
    left_triggers: List[str] = []
    right_triggers: List[str] = []
    amplifiers: List[str] = []
    balance_ratio: float = 0.5


class ClickbaitSignal(BaseModel):
    score: int
    level: str
    caps_word_count: int
    exclamation_count: int
    question_count: int
    triggers: List[str] = []


class ViralitySignal(BaseModel):
    score: int
    risk: str
    velocity_factors: List[str] = []


class ReadabilitySignal(BaseModel):
    score: float
    grade: str
    sentence_count: int
    avg_sentence_length: float


class WritingStyleSignal(BaseModel):
    formality: str
    avg_word_length: float
    passive_voice_count: int
    quote_count: int
    number_count: int
    url_count: int
    sentence_count: int


class NamedEntity(BaseModel):
    text: str
    label: str


class LinguisticSignals(BaseModel):
    disclaimer: str = "Linguistic signals evaluate rhetorical style, emotion, and structure. They are not proof of factual truth."
    sentiment: SentimentSignal
    bias: BiasSignal
    clickbait: ClickbaitSignal
    virality_risk: ViralitySignal
    readability: ReadabilitySignal
    writing_style: WritingStyleSignal
    triggered_keywords: List[str] = []


class AnalysisResponse(BaseModel):
    scan_id: str
    text_length: int
    primary_verdict: str  # SUPPORTED, CONTRADICTED, MIXED, UNVERIFIED
    legacy_classification: str  # REAL, SUSPICIOUS, FAKE
    credibility_score: float
    fake_probability: float
    confidence: float
    message: str
    claims: List[ClaimItem] = []
    extracted_claims: List[str] = []
    evidence: List[NamedEntity] = []  # Legacy compatibility field for entities
    entities: List[NamedEntity] = []
    actual_news_context: str = ""
    triggered_keywords: List[str] = []
    linguistic_signals: LinguisticSignals
    
    # Direct mappings for legacy UI components
    sentiment: SentimentSignal
    bias: BiasSignal
    clickbait: ClickbaitSignal
    virality_risk: ViralitySignal
    readability: ReadabilitySignal
    writing_style: WritingStyleSignal
    
    nlp_available: bool = True
    created_at: str


class HistoryItem(BaseModel):
    id: int
    scan_id: str
    timestamp: str
    snippet: str
    classification: str
    primary_verdict: str
    credibility_score: float
    fake_probability: float


class HistoryResponse(BaseModel):
    history: List[HistoryItem]
    total: int


class StatsResponse(BaseModel):
    total: int
    breakdown: Dict[str, int]
    primary_verdicts: Dict[str, int]
    avg_credibility: float
    avg_fake_probability: float
