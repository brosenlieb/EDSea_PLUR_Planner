import os
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import the models we just created
from backend.app.db.models import Base, Stage, Artist, Performance, StageDistance

load_dotenv()
# Connect to the local Postgres container we spun up in docker-compose
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment or .env file!")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    print("Connecting to database...")
    
    # 1. Enable pgvector extension dynamically
    with engine.connect() as conn:
        # prevents having to recreate the Docker container for initialization
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    # 2. Clear existing data and create tables
    print("Creating tables...")
    Base.metadata.drop_all(bind=engine) 
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        # 3. Seed Stages
        print("Seeding stages...")
        stages_data = ["Main Stage", "Forest Stage", "Neon Tent"]
        stages = []
        for name in stages_data:
            stage = Stage(name=name)
            session.add(stage)
            stages.append(stage)
        session.commit()

        # 4. Seed Stage Distances (Travel Matrix)
        print("Seeding travel matrix...")
        # (Stage A index, Stage B index, Walk time in minutes)
        distances = [
            (0, 1, 10), # Main to Forest: 10 mins
            (0, 2, 15), # Main to Neon: 15 mins
            (1, 2, 5),  # Forest to Neon: 5 mins
        ]
        
        for a_idx, b_idx, dist in distances:
            # We add both directions to make routing queries easier later
            session.add(StageDistance(stage_a_id=stages[a_idx].id, stage_b_id=stages[b_idx].id, distance_minutes=dist))
            session.add(StageDistance(stage_a_id=stages[b_idx].id, stage_b_id=stages[a_idx].id, distance_minutes=dist))
        session.commit()

        # 5. Seed Artists with dummy vector embeddings
        print("Seeding artists...")
        artist_names = [
            "Neon Dreams", "Electric Horizon", "Bass Drop Brigade", "The Melody Makers",
            "Synthwave Surfers", "Acoustic Sunset", "Midnight Rhythms", "DJ Phantom",
            "The Underground", "Cosmic Groove"
        ]
        artists = []
        for name in artist_names:
            # Generate a random 384-dimensional float array to simulate an AI embedding
            dummy_embedding = [random.uniform(-1.0, 1.0) for _ in range(384)]
            
            artist = Artist(
                name=name,
                genre="Electronic", 
                description=f"A mind-bending performance by {name}.",
                embedding=dummy_embedding
            )
            session.add(artist)
            artists.append(artist)
        session.commit()

        # 6. Seed Performances (Overlapping schedules to test OR-Tools later)
        print("Seeding performances...")
        festival_start = datetime(2026, 8, 15, 17, 0, tzinfo=timezone.utc)
        
        for i, artist in enumerate(artists):
            # Assign stages cyclically and create some overlapping times
            stage = stages[i % 3]
            start_time = festival_start + timedelta(hours=(i // 3))
            end_time = start_time + timedelta(minutes=45)
            
            performance = Performance(
                artist_id=artist.id,
                stage_id=stage.id,
                start_time=start_time,
                end_time=end_time
            )
            session.add(performance)
        session.commit()
        
        print("Database successfully seeded.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()