"""
TruthLens Master Analysis Orchestration Engine
Executes complete end-to-end evidence-first verification pipeline.
"""

import uuid
import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from ..schemas.analysis import AnalysisResponse, ClaimItem, EvidenceItem
from .linguistic import analyze_linguistic_signals, NLP_AVAILABLE
from .claims import extract_claims, build_search_query
from .evidence import CompositeEvidenceAggregator
from .scoring import evaluate_claim_against_evidence, compute_aggregate_verdict
from ..db.models import Scan, ClaimRecord, EvidenceRecord


class TruthLensAnalyzer:
    """Orchestrates linguistic analysis, evidence retrieval, claim evaluation, and persistence."""
    
    def __init__(self, evidence_aggregator: Optional[CompositeEvidenceAggregator] = None):
        self.evidence_aggregator = evidence_aggregator or CompositeEvidenceAggregator()

    async def analyze(self, text: str, source_url: Optional[str] = None, db: Optional[Session] = None) -> AnalysisResponse:
        scan_id = f"scan_{uuid.uuid4().hex[:12]}"
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # 1. Deterministic Linguistic Evaluation
        linguistic, entities, doc = analyze_linguistic_signals(text)
        
        # 2. Factual Claim Extraction
        raw_claims = extract_claims(text, max_claims=4)
        
        # 3. Retrieve Evidence for each Claim
        evaluated_claims: List[ClaimItem] = []
        for claim in raw_claims:
            query = build_search_query(claim.text)
            evidence_items = await self.evidence_aggregator.retrieve_evidence_for_claim(claim.text, query)
            claim.evidence = evidence_items
            evaluated_claim = evaluate_claim_against_evidence(claim)
            evaluated_claims.append(evaluated_claim)

        # 4. Compute Aggregate Deterministic Verdict
        primary_verdict, legacy_class, cred_score, fake_prob, confidence, message = compute_aggregate_verdict(
            evaluated_claims, linguistic
        )

        # 5. Build Human-Readable Evidence Summary
        if evaluated_claims and evaluated_claims[0].evidence:
            first_ev = evaluated_claims[0].evidence[0]
            context_summary = f"Evidence Source: {first_ev.source_name} ({first_ev.title}). {first_ev.snippet[:200]}..."
        else:
            context_summary = "Cross-referencing complete across indexed public databases. No direct matching verification reports retrieved."

        # 6. Construct Standardized Analysis Response
        response = AnalysisResponse(
            scan_id=scan_id,
            text_length=len(text.split()),
            primary_verdict=primary_verdict,
            legacy_classification=legacy_class,
            credibility_score=cred_score,
            fake_probability=fake_prob,
            confidence=confidence,
            message=message,
            claims=evaluated_claims,
            extracted_claims=[c.text for c in evaluated_claims],
            evidence=entities,  # legacy compatibility mapping
            entities=entities,
            actual_news_context=context_summary,
            triggered_keywords=linguistic.triggered_keywords,
            linguistic_signals=linguistic,
            sentiment=linguistic.sentiment,
            bias=linguistic.bias,
            clickbait=linguistic.clickbait,
            virality_risk=linguistic.virality_risk,
            readability=linguistic.readability,
            writing_style=linguistic.writing_style,
            nlp_available=NLP_AVAILABLE,
            created_at=now_str
        )

        # 7. Database Persistence (Minimal Anonymized Retention)
        if db is not None:
            try:
                snippet = text[:90] + "..." if len(text) > 90 else text
                scan_record = Scan(
                    scan_id=scan_id,
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    text_length=len(text.split()),
                    snippet=snippet,
                    primary_verdict=primary_verdict,
                    legacy_classification=legacy_class,
                    credibility_score=cred_score,
                    fake_probability=fake_prob,
                    confidence=confidence,
                    linguistic_risk=float(linguistic.clickbait.score),
                    evidence_count=sum(len(c.evidence) for c in evaluated_claims),
                    claims_count=len(evaluated_claims)
                )
                db.add(scan_record)
                db.flush()

                for c in evaluated_claims:
                    claim_rec = ClaimRecord(
                        scan_id=scan_record.id,
                        claim_id=c.claim_id,
                        claim_text=c.text,
                        verdict=c.verdict,
                        confidence=c.confidence,
                        explanation=c.explanation
                    )
                    db.add(claim_rec)
                    db.flush()

                    for ev in c.evidence:
                        ev_rec = EvidenceRecord(
                            claim_id=claim_rec.id,
                            source_name=ev.source_name,
                            title=ev.title,
                            url=ev.url,
                            snippet=ev.snippet,
                            source_type=ev.source_type,
                            authority_score=ev.authority_score,
                            relevance_score=ev.relevance_score
                        )
                        db.add(ev_rec)

                db.commit()
            except Exception as e:
                db.rollback()

        return response
