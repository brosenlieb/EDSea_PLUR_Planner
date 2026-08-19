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
from backend.app.db.models import Base, Stage, Artist, Performance, StageDistance

load_dotenv()
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment or .env file!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- CONFIGURATION ---
# Change this to the timezone where the festival actually takes place
SOURCE_TIMEZONE = "America/New_York" 

SCHEDULE_FILES = [
    {"file": "data/raw/day1.json", "date": "2025-11-01"},
    {"file": "data/raw/day2.json", "date": "2025-11-02"},
    {"file": "data/raw/day3.json", "date": "2025-11-03"},
    {"file": "data/raw/day4.json", "date": "2025-11-04"},
    {"file": "data/raw/day5.json", "date": "2025-11-05"},
]

def sanitize_value(val, fallback):
    """Checks for null, 'all', or empty strings and applies a safe fallback."""
    if not val:
        return fallback
    clean_val = str(val).strip()
    if clean_val.lower() in ["null", "all", "none", "n/a", ""]:
        return fallback
    return clean_val

def parse_local_datetime(date_str: str, time_str: str) -> datetime:
    """
    Parses a date and time string, normalizes it to a 24-hour format,
    and returns a timezone-aware datetime object in the local festival timezone.
    Args:
        date_str: Date in "YYYY-MM-DD" format.
        time_str: Time in "HH:MM" (24-hour) or "H:MM AM/PM" format.
        
    Returns:
        A timezone-aware datetime object in SOURCE_TIMEZONE.
    """
    # Clean input: " 2:30 PM " -> "2:30PM"
    normalized_time = time_str.strip().replace(" ", "").upper()

    # Determine if input is 12-hour (contains AM/PM) or 24-hour
    if "AM" in normalized_time or "PM" in normalized_time:
        # Parse 12-hour format
        temp_dt = datetime.strptime(normalized_time, "%I:%M%p")
        # Convert to a 24-hour string: "2:30 PM" -> "14:30"
        clean_time = temp_dt.strftime("%H:%M")
    else:
        # Assume 24-hour format, ensure "H:MM" becomes "HH:MM"
        clean_time = normalized_time
        if len(clean_time) == 4:
            clean_time = f"0{clean_time}"
    combined_str = f"{date_str} {clean_time}"
    
    try:
        # Parse into a naive datetime object
        naive_dt = datetime.strptime(combined_str, "%Y-%m-%d %H:%M")
    except ValueError as e:
        raise ValueError(f"Time '{combined_str}' is not in a valid format: {e}")

    # Attach the local festival timezone without converting to UTC
    # UTC conversion may be added back later depending on 2027 data
    return naive_dt.replace(tzinfo=ZoneInfo(SOURCE_TIMEZONE))

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
        print("Reading JSON files...")
        all_events = []
        for sf in SCHEDULE_FILES:
            try:
                with open(sf["file"], 'r') as f:
                    data = json.load(f)
                    events = data.get("performances", data) if isinstance(data, dict) else data
                    
                    for event in events:
                        event['festival_date'] = sf['date']
                        all_events.append(event)
            except FileNotFoundError:
                print(f"Warning: {sf['file']} not found. Skipping.")

        if not all_events:
            print("No event data found. Exiting.")
            return

        print("Sanitizing and extracting entities...")
        unique_artist_names = set()
        # Map normalized keys (lowercase) to the Stage objects
        # Key format: (normalized_stage_name, normalized_location_name)
        stages_map = {}
        
        for e in all_events:
            raw_stage = e.get("stage")
            raw_location = e.get("location")
            
            # Clean values for display/storage
            clean_stage = sanitize_value(raw_stage, fallback="Festival Wide").title()
            clean_location = sanitize_value(raw_location, fallback="General Area").title()

            #Specific edits for a few edge cases.  May not apply to 2027 data.
            if clean_location == "Manhattan Dining Deck 7 Aft":
                clean_location = "Manhattan Dining Room Deck 7 Aft"
            if clean_stage == "Kinetic Ocean":
                clean_location = "Pool Deck Deck 16"
            
            # Create a normalized key for uniqueness (Title case)
            stage_key = (clean_stage, clean_location)
            
            # If this stage/location combo hasn't been seen, create it
            if stage_key not in stages_map:
                new_stage = Stage(name=clean_stage, location_name=clean_location)
                session.add(new_stage)
                session.flush()  # Flush to generate ID if needed
                stages_map[stage_key] = new_stage
            
            # Assign the shared object to the event
            e["clean_stage"] = stages_map[stage_key].name
            e["clean_location"] = stages_map[stage_key].location_name
            e["stage_key"] = stage_key # Optional: keep for logic reference
            
            raw_event = e.get("event")
            e["clean_artist"] = sanitize_value(raw_event, fallback="General Announcement")
            unique_artist_names.add(e["clean_artist"])

        print(f"Seeding {len(stages_map)} unique stages...")

        print(f"Seeding {len(unique_artist_names)} artists/events...")
        artists_dict = {}
        for name in unique_artist_names:
            dummy_embedding = [random.uniform(-1.0, 1.0) for _ in range(768)]

            activities = ["SOUND HEALING (COSMIC CORAL)", "OPEN DECK SIGN UPS (CASINO)",
            "CARTOONS + CEREAL BAR (THE PEARL)", "RISE + RADIATE YOGA (KINETIC OCEAN)",
            "RAVERCISE (KINETIC OCEAN)", "OPEN DECK (CASINO)", "UP TO DATE (CIRCUIT WAVES)",
            "CHARACTER BRUNCH EGGSTRAVAGANZA (TASTE&SAVOR)", "LAUGHS AHOY! COMEDY (DEEP DIVE DISCO)",
            "DEEP CORE, DEEPER BEATS YOGA (COSMIC CORAL)", "BACARDÍ RAVE BINGO (CIRCUIT WAVES)"]

            if name in activities:
                artist = Artist(
                    name=name,
                    genre="Activity",
                    description=f"{name}",
                    embedding=dummy_embedding
                )
            elif name == "General Announcement":
                artist = Artist(
                    name=name,
                    genre="Announcement",
                    description=f"{name}",
                    embedding=dummy_embedding
                )
            else:    
                artist = Artist(
                    name=name,
                    genre="Unknown",
                    description=f"Event/Performance: {name}",
                    embedding=dummy_embedding
                )
            session.add(artist)
            session.flush()
            artists_dict[name] = artist
            
        session.commit()

        print("Seeding performances...")
        current_event = None
        
        for e in all_events:
            current_event = e
            
            try:
                # Convert start time to 24-hour time
                start_dt = parse_local_datetime(e['festival_date'], e['start_time'])
                
                # Handle End Time
                end_time_raw = e.get('end_time')
                if end_time_raw and str(end_time_raw).strip().lower() not in ["null", "none", "", "n/a"]:
                    end_dt = parse_local_datetime(e['festival_date'], str(end_time_raw))
                    
                    # Midnight rollover check: If end is before start, it's the next day
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                else:
                    # Default to 15 minutes after start time
                    end_dt = start_dt + timedelta(minutes=15)
                
                performance = Performance(
                    artist_id=artists_dict[e['clean_artist']].id,
                    stage_id=stages_map[e['stage_key']].id,
                    start_time=start_dt,
                    end_time=end_dt
                )
                session.add(performance)
                
            except (ValueError, KeyError) as ve:
                print(f"Skipping event '{e.get('clean_artist', 'Unknown')}' due to error: {ve}. See {current_event}")
                continue
            
        try:
            session.commit()
            print("Database successfully seeded with 24-hour times.")
        except Exception as e:
            session.rollback()
            print(f"Error occurred during: {current_event}\n{traceback.format_exc()}")
            raise 
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()