import asyncio
import sys
from pathlib import Path

# Fix the import path automatically
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.app.db.models import Artist
from backend.app.core.lemonade import generate_embedding
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def embed_artists():
    session = SessionLocal()
    try:
        # Fetch artists that don't have an embedding yet.  Easiest way to regenerate currently
        # is to drop the embedding column and readd.  
        artists = session.query(Artist).filter(Artist.embedding.is_(None)).all()

        if not artists:
            print("All artists already have embeddings!")
            return

        print(f"Found {len(artists)} artists needing embeddings. Generating...")
        
        for artist in artists:
            # Create a rich text string for the AI to understand the artist
            embed_text = f"Artist: {artist.name}. Genre: {artist.genre}. Description: {artist.description}"
            
            print(f"Embedding: {artist.name}...")
            # Call our local Lemonade AI
            vector = await generate_embedding(embed_text)
            
            # Save it back to the SQLAlchemy model
            artist.embedding = vector
            
        # Commit the transaction to save all vectors to Postgres
        session.commit()
        print("Successfully saved all embeddings to the database!")
        
    except Exception as e:
        print(f"Error during embedding generation: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Because we are using an async function, we run it via asyncio
    asyncio.run(embed_artists())