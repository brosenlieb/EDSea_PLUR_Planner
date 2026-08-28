import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import LocationDistance

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

load_dotenv()
# Connect to database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_location_distances():
    session = SessionLocal()
    json_path = PROJECT_ROOT / "data" / "raw" / "location_distances.json"
    
    if not json_path.exists():
        print(f"Error: Could not find JSON file at {json_path}")
        return

    try:
        print("Reading distance data from JSON...")
        with open(json_path, "r") as f:
            distances_data = json.load(f)

        # Clear existing entries to prevent duplicate rows on re-runs
        print("Clearing existing location distances...")
        session.query(LocationDistance).delete()

        entries_added = 0
        for entry in distances_data:
            # Handle either key naming style gracefully
            loc_a = entry.get("location_a")
            loc_b = entry.get("location_b")
            dist = entry["distance_minutes"]

            if not loc_a or not loc_b:
                print(f"Warning: Skipping malformed record: {entry}")
                continue

            # Add A -> B
            session.add(LocationDistance(location_a=loc_a, location_b=loc_b, distance_minutes=dist))
            # Add B -> A (Symmetric travel time)
            session.add(LocationDistance(location_a=loc_b, location_b=loc_a, distance_minutes=dist))
            entries_added += 2

        session.commit()
        print(f"Successfully seeded {entries_added} directional location records into 'location_distances'!")

    except Exception as e:
        print(f"Error seeding distances: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_location_distances()