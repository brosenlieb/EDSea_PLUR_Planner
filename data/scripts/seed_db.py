import os
import sys
import json
import random
import traceback
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Removed 'Event' import; updated to match models.py
from backend.app.db.models import Base, Activity, Location, Artist, Performance, Announcement
from ingestion_models import StandardizedEvent

load_dotenv()
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment or .env file!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SCHEDULE_FILES = [
    {"file": "data/raw/day1.json", "date": "2025-11-01", "day": 1},
    {"file": "data/raw/day2.json", "date": "2025-11-02", "day": 2},
    {"file": "data/raw/day3.json", "date": "2025-11-03", "day": 3},
    {"file": "data/raw/day4.json", "date": "2025-11-04", "day": 4},
    {"file": "data/raw/day5.json", "date": "2025-11-05", "day": 5},
]

def seed_database():
    print("Connecting to database...")
    
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        for sf in SCHEDULE_FILES:
            file_path = Path(sf["file"])
            if not file_path.exists():
                print(f"Warning: {sf['file']} not found. Skipping.")
                continue

            print(f"Processing {sf['file']}...")
            with open(file_path, 'r') as f:
                data = json.load(f)
                events = data.get("events", data) if isinstance(data, dict) else data

            for raw_event in events:
                print(f"Current event: {raw_event}")
                raw_event['event_date'] = sf['date']
                clean_event = StandardizedEvent.model_validate(raw_event)

                # Handle events that start before midnight and end after midnight
                if clean_event.end_time < clean_event.start_time:
                    clean_event.end_time += timedelta(days=1)

                # Edge case overrides
                if clean_event.location_name == "Manhattan Dining Deck 7 Aft":
                    clean_event.location_name = "Manhattan Dining Room Deck 7 Aft"
                if clean_event.stage_name == "Kinetic Ocean":
                    clean_event.location_name = "Pool Deck Deck 16"

                # Get or create Location record respecting the (name, location_name) constraint
                location = session.query(Location).filter_by(
                    location_name=clean_event.location_name,
                    stage_name=clean_event.stage_name
                ).first()
                
                if not location:
                    location = Location(
                        location_name=clean_event.location_name,
                        stage_name=clean_event.stage_name
                    )
                    session.add(location)
                    session.flush()

                # Insert directly into individual tables
                if clean_event.event_type == "performance":
                    artist = session.query(Artist).filter_by(name=clean_event.event_name).first()
                    if not artist:
                        dummy_embedding = [random.uniform(-1.0, 1.0) for _ in range(768)]
                        artist = Artist(
                            name=clean_event.event_name,
                            genre="Unknown",
                            description=f"Performance by {clean_event.event_name}",
                            embedding=dummy_embedding
                        )                        
                        session.add(artist)
                        session.flush()

                    perf = Performance(
                        artist_id=artist.id,
                        location_id=location.id,
                        start_time=clean_event.start_time,
                        end_time=clean_event.end_time
                    )
                    session.add(perf)

                elif clean_event.event_type == "activity":
                    act = Activity(
                        activity_name=clean_event.event_name,
                        location_id=location.id,
                        start_time=clean_event.start_time,
                        end_time=clean_event.end_time
                    )
                    session.add(act)

                elif clean_event.event_type == "announcement":
                    ann = Announcement(
                        announcement_name=clean_event.event_name,
                        location_id=location.id,
                        start_time=clean_event.start_time,
                        end_time=clean_event.end_time
                    )
                    session.add(ann)
     
        session.commit()
        print("Database successfully seeded.")
    except Exception as e:
        session.rollback()
        print(f"Error occurred during execution:\n{traceback.format_exc()}")
        raise 
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()