"""
Database Session and Engine Management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Database URL from environment or default SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./history.db")

# Fix Render PostgreSQL URL scheme if needed (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect args for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


# Auto-create tables on module import
try:
    init_db()
except Exception:
    pass


def get_db():
    """Dependency generator for database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
