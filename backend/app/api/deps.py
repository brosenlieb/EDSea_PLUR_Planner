"""
Module for database dependency injection.

This module provides the configuration and dependency function for
managing database sessions in the FastAPI application.
"""
import os
import sys
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to yield a database session.

    This generator yields a database session to be used by a request.
    The session is automatically closed after the request is processed.

    Yields:
        Session: A SQLAlchemy database session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()