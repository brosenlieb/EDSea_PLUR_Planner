import os
import sys
import json
import random
import traceback
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Automatically locate project root (2 levels up from data/scripts/seed_db.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import the models
from backend.app.db.models import Base, Activity, Stage, Artist, Performance, Announcement, Event
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

def sanitize_value(val, fallback):
    """Checks for null, 'all', or empty strings and applies a safe fallback."""
    if not val:
        return fallback
    clean_val = str(val).strip()
    if clean_val.lower() in ["null", "all", "none", "n/a", ""]:
        return fallback
    return clean_val

def seed_database():
    print("Connecting to database...")
    
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    print("Creating tables...")
    Base.metadata.drop_all(bind=engine) 
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        print("Reading JSON file...")
        for sf in SCHEDULE_FILES:
            try:
                with open(sf["file"], 'r') as f:
                    data = json.load(f)
                    events = data.get(data) if isinstance(data, dict) else data
                    
                    for event in events:
                        event['event_date'] = sf['date']
                        event['event_day'] = sf['day']
            except FileNotFoundError:
                print(f"Warning: {sf['file']} not found. Skipping.")

            for raw_event in events:
                print("Sanitizing and scheduled items...")
                clean_event = StandardizedEvent.model_validate(raw_event)

                # Gets stage record (stage.id), creates if it doesn't yet exist.
                stage = session.query(Stage).filter_by(name=clean_event.stage_name).first()
                if not stage:
                    stage = Stage(name=clean_event.stage_name, fallback="n/a")
                    session.add(stage)
                    session.flush()

                #Specific edits for a few edge cases.  May not apply to 2027 data.
                if clean_event.location_name == "Manhattan Dining Deck 7 Aft":
                    clean_event.location_name = "Manhattan Dining Room Deck 7 Aft"
                if clean_event.stage_name == "Kinetic Ocean":
                    clean_event.location_name = "Pool Deck Deck 16"

                # Come back and add "Day 1/2/5" to the base_event
                base_event = Event(
                    stage_id=stage.id,
                    location_name=clean_event.location_name,
                    event_type=clean_event.event_type,
                    start_time=clean_event.start_time,
                    end_time=clean_event.end_time
                )
                session.add(base_event)
                session.flush()

                # Add additional info (artist name, activity type, etc based on event_type)
                if clean_event.event_type == "performance":
                    artist = session.query(Artist).filter_by(name=clean_event.event_name).first()
                    if not artist:
                        dummy_embedding = [random.uniform(-1.0, 1.0) for _ in range(768)]
                        artist = Artist(
                            name=clean_event.event_name,
                            genre="Unknown",
                            description=f"Event/Performance: {clean_event.event_name}",
                            embedding=dummy_embedding
                        )                        
                        session.add(artist)
                        session.flush()
                    perf = Performance(event_id=base_event.id, artist_id=artist.id)
                    session.add(perf)
                elif clean_event.event_type == "activity":
                    act = Activity(event_id=base_event.id, title=clean_event.entity_name)
                    session.add(act)
                elif clean_event.event_type == "announcement":
                    ann = Announcement(event_id=base_event.id, title=clean_event.entity_name)
                    session.add(ann)
     
        session.commit()
        print("Database successfully seeded.")
    except Exception as e:
        session.rollback()
        print(f"Error occurred during: {clean_event}\n{traceback.format_exc()}")
        raise 
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()