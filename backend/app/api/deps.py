import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency to yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()