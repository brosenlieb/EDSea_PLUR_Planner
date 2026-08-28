import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up the engine exactly as we did in the seed script
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency to yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()