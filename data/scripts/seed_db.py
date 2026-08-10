import os
import json
import random
import traceback
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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

def parse_to_utc(date_str: str, time_str: str) -> datetime:
    """
    Parses a date and time string using 24-hour format, 
    localizes it to SOURCE_TIMEZONE, and converts it to UTC.
    
    Args:
        date_str: Date in "YYYY-MM-DD" format.
        time_str: Time in "HH:MM" (24-hour) format.
        
    Returns:
        A timezone-aware datetime object in UTC.
    """
    # Clean the time string (remove spaces, extra zeros, and normalize)
    normalized_time = time_str.strip().replace(" ", "").upper()
    # Converts to a 24-hr datetime object
    clean_time = datetime.strptime(normalized_time, "%I:%M%p")
    # Shift clean_time back to a string with only five characters: HH:MM
    clean_time = datetime.strftime(clean_time, "%I:%M")[:5]

    combined_str = f"{date_str} {clean_time}"
    
    try:
        # Use %H:%M for 24-hour clock
        naive_dt = datetime.strptime(combined_str, "%Y-%m-%d %H:%M")
    except ValueError as e:
        # Fallback/Error handling for unexpected formats
        raise ValueError(f"Time '{clean_time}' is not in valid 24-hour HH:MM format: {e}")

    # 1. Attach the local festival timezone (e.g., America/New_York)
    # 2. Convert that local time to UTC
    local_dt = naive_dt.replace(tzinfo=ZoneInfo(SOURCE_TIMEZONE))
    return local_dt.astimezone(timezone.utc)

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
        unique_stages = set()
        unique_artist_names = set()
        
        for e in all_events:
            raw_stage = e.get("stage")
            raw_location = e.get("location")
            
            e["clean_stage"] = sanitize_value(raw_stage, fallback="Festival Wide")
            e["clean_location"] = sanitize_value(raw_location, fallback="General Area")
            
            stage_key = (e["clean_stage"], e["clean_location"])
            e["stage_key"] = stage_key
            unique_stages.add(stage_key)
            
            raw_event = e.get("event")
            e["clean_artist"] = sanitize_value(raw_event, fallback="General Announcement")
            unique_artist_names.add(e["clean_artist"])

        print(f"Seeding {len(unique_stages)} stages...")
        stages_dict = {}
        for stage_name, location_name in unique_stages:
            stage = Stage(name=stage_name, location_name=location_name)
            session.add(stage)
            session.flush()
            stages_dict[(stage_name, location_name)] = stage

        print(f"Seeding {len(unique_artist_names)} artists/events...")
        artists_dict = {}
        for name in unique_artist_names:
            dummy_embedding = [random.uniform(-1.0, 1.0) for _ in range(384)]
            
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
                # Convert start time to UTC
                start_dt = parse_to_utc(e['festival_date'], e['start_time'])
                
                # Handle End Time
                end_time_raw = e.get('end_time')
                if end_time_raw and str(end_time_raw).strip().lower() not in ["null", "none", "", "n/a"]:
                    end_dt = parse_to_utc(e['festival_date'], str(end_time_raw))
                    
                    # Midnight rollover check: If end is before start, it's the next day
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                else:
                    # Default to 15 minutes after start time
                    end_dt = start_dt + timedelta(minutes=15)
                
                performance = Performance(
                    artist_id=artists_dict[e['clean_artist']].id,
                    stage_id=stages_dict[e['stage_key']].id,
                    start_time=start_dt,
                    end_time=end_dt
                )
                session.add(performance)
                
            except (ValueError, KeyError) as ve:
                print(f"Skipping event '{e.get('clean_artist', 'Unknown')}' due to error: {ve}. See {current_event}")
                continue
            
        try:
            session.commit()
            print("Database successfully seeded with UTC times.")
        except Exception as e:
            session.rollback()
            print(f"Error occurred during: {current_event}\n{traceback.format_exc()}")
            raise 
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()