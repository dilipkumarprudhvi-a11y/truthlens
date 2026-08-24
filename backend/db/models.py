"""
TruthLens Database Models
SQLAlchemy ORM models supporting both SQLite (local) and PostgreSQL (production).
"""

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Scan(Base):
    """Represents a single analysis execution."""
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)
    text_length = Column(Integer, default=0)
    snippet = Column(String(120), default="")
    primary_verdict = Column(String(32), default="UNVERIFIED")  # SUPPORTED, CONTRADICTED, MIXED, UNVERIFIED
    legacy_classification = Column(String(32), default="UNKNOWN")  # REAL, SUSPICIOUS, FAKE
    credibility_score = Column(Float, default=50.0)
    fake_probability = Column(Float, default=50.0)
    confidence = Column(Float, default=50.0)
    linguistic_risk = Column(Float, default=0.0)
    evidence_count = Column(Integer, default=0)
    claims_count = Column(Integer, default=0)

    # Relationships
    claims = relationship("ClaimRecord", back_populates="scan", cascade="all, delete-orphan")


class ClaimRecord(Base):
    """Extracted declarative claim associated with a scan."""
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id = Column(String(32), nullable=False)
    claim_text = Column(Text, nullable=False)
    verdict = Column(String(32), default="UNVERIFIED")
    confidence = Column(Float, default=0.0)
    explanation = Column(Text, default="")

    # Relationships
    scan = relationship("Scan", back_populates="claims")
    evidence_items = relationship("EvidenceRecord", back_populates="claim", cascade="all, delete-orphan")


class EvidenceRecord(Base):
    """Retrieved evidence citing or refuting a claim."""
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(128), default="Unknown")
    title = Column(String(256), default="")
    url = Column(String(512), default="")
    snippet = Column(Text, default="")
    source_type = Column(String(64), default="web")
    authority_score = Column(Float, default=0.5)
    relevance_score = Column(Float, default=0.5)

    # Relationships
    claim = relationship("ClaimRecord", back_populates="evidence_items")


class SourceDomain(Base):
    """Reputation registry for evaluated domains."""
    __tablename__ = "sources"

    domain = Column(String(128), primary_key=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), default="general")
    authority_weight = Column(Float, default=0.5)
