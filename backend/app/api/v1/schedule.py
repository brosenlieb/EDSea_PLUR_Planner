import hashlib
import json
import secrets
from typing import Any, List, Optional, Tuple, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import text
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

from app.api.deps import get_db
from app.core.recommendation import get_recommendations
from app.core.solver import generate_optimal_schedule
from app.db.models import Performance, Activity, LocationDistance, Announcement, SavedSchedule
from app.schemas.api_models import ScheduleRequest, EventSlot, ScheduleResponse
from app.crud.crud_schedule import create_saved_schedule, get_saved_schedule_by_slug, get_saved_schedule_by_preferences_hash

# Note: You will need to add ScheduleResponse to your schemas/api_models.py
# class ScheduleResponse(BaseModel):
#     slug: str
#     events: List[EventSlot]

router = APIRouter()

EASTERN_TZ = ZoneInfo("America/New_York")

def to_eastern(dt: Optional[datetime]) -> Optional[datetime]:
    """Converts a database datetime to Eastern Time wall-clock time.

    Args:
        dt: The datetime object to convert. If None, returns None. Naive
            datetimes are assumed to be in UTC.

    Returns:
        The converted datetime in Eastern Time.
    """
    if dt is None:
        return None

    # If naive, assume UTC from the database
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert UTC to true Eastern Time (handles EDT -> EST transitions automatically)
    return dt.astimezone(EASTERN_TZ)

def get_location_name(entity: Any, default: str) -> str:
    """Extracts the location name from an entity object, returning a default value if not found.

    Args:
        entity: The entity object containing location information.
        default: The default location name to return if the entity's location
                 is missing or empty.

    Returns:
        The location name from the entity, or the default value if unavailable.
    """
    if entity and getattr(entity, "location", None):
        return getattr(entity.location, "location_name", None) or default
    return default

@router.get("/schedule/{slug}", response_model=ScheduleResponse)
def get_schedule_by_slug(slug: str, db: Session = Depends(get_db)):
    """Retrieves a cached schedule by its unique slug."""
    cached_schedule = get_saved_schedule_by_slug(db=db, slug=slug)
    
    if not cached_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return {
        "slug": cached_schedule.slug,
        "events": cached_schedule.schedule_data
    }

@router.post("/schedule/generate")
def generate_schedule(
    payload: ScheduleRequest, 
    db: Session = Depends(get_db)
):
    """Generates an optimized festival schedule, utilizing database caching for identical inputs."""
    
    # Generate deterministic hash of the sorted payload
    payload_dict = payload.model_dump() if hasattr(payload, 'model_dump') else payload.dict()
    payload_str = json.dumps(payload_dict, sort_keys=True)
    preferences_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    # Check the database for an existing schedule cache hit
    cached_schedule = get_saved_schedule_by_preferences_hash(db=db, preferences_hash=preferences_hash)
    if cached_schedule:
        return {"slug": cached_schedule.slug, "events": cached_schedule.schedule_data}

    # Cache Miss: Proceed with fetching data and running the solver
    recommended_artists = get_recommendations(db, payload.favorite_artist_ids, limit=10)
    recommended_ids = [a.id for a in recommended_artists]
    target_artist_ids = set(payload.favorite_artist_ids + recommended_ids)
    
    db_performances = (
        db.query(Performance)
        .options(
            selectinload(Performance.artists),
            joinedload(Performance.location)
        )
        .all()
    )
    
    events_for_solver = []
    
    for p in db_performances:
        p_artist_ids = [a.id for a in p.artists]
        
        if not any(aid in target_artist_ids for aid in p_artist_ids):
            continue
            
        artist_names = [a.name for a in p.artists]
        display_title = p.title if p.title else " B2B ".join(artist_names)
        
        events_for_solver.append({
            "id": f"perf_{p.id}",
            "title": display_title,
            "event_type": "performance",
            "start_time": to_eastern(p.start_time),
            "end_time": to_eastern(p.end_time),
            "location_id": p.location_id,
            "location_name": p.location.location_name if p.location else "Main Stage",
            "stage_name": p.location.stage_name if p.location else None,
            "artist_ids": p_artist_ids,
        })

    activity_prefs = {
        pref.activity_id: pref.priority
        for pref in payload.activity_preferences
    } if hasattr(payload, 'activity_preferences') else {}

    if activity_prefs:
        db_activities = (
            db.query(Activity)
            .options(joinedload(Activity.location))
            .filter(Activity.id.in_(activity_prefs.keys()))
            .all()
        )
        
        for a in db_activities:
            events_for_solver.append({
                "id": f"act_{a.id}",
                "title": a.activity_name,
                "event_type": "activity",
                "start_time": to_eastern(a.start_time),
                "end_time": to_eastern(a.end_time),
                "location_id": a.location_id,
                "location_name": a.location.location_name if a.location else "Festival Grounds",
                "stage_name": a.location.stage_name if a.location else None,
                "priority": activity_prefs.get(a.id)
            })
        
    distances = db.query(LocationDistance).all()
    travel_matrix = {
        (d.location_a, d.location_b): d.distance_minutes
        for d in distances
    }
    
    solved_schedule = generate_optimal_schedule(
        events=events_for_solver,
        travel_matrix=travel_matrix,
        favorite_artist_ids=payload.favorite_artist_ids
    )
    
    db_announcements = db.query(Announcement).options(joinedload(Announcement.location)).all()

    announcement_slots = []
    for ann in db_announcements:
        ann_title = (
            getattr(ann, 'announcement_name', None)
            or getattr(ann, 'title', None)
            or "Announcement"
        )

        announcement_slots.append({
            "id": f"ann_{ann.id}",
            "title": ann_title,
            "event_type": "activity",
            "category": "announcement",
            "start_time": to_eastern(ann.start_time),
            "end_time": to_eastern(ann.end_time),
            "location_id": ann.location_id if ann.location_id else 0,
            "location_name": get_location_name(ann, "Shipwide / Informational"),
            "stage_name": ann.location.stage_name if ann.location else None,
        })

    full_schedule = list(solved_schedule) + announcement_slots

    def get_start_key(item):
        st = item["start_time"] if isinstance(item, dict) else item.start_time
        return st.isoformat() if hasattr(st, 'isoformat') else str(st)

    full_schedule.sort(key=get_start_key)
    full_schedule = attach_walking_times(full_schedule, db)

    # Save the new solved schedule into the database cache
    new_slug = secrets.token_urlsafe(6)[:8]
    schedule_json_data = jsonable_encoder(full_schedule)
    
    new_saved_schedule = create_saved_schedule(
        db=db,
        slug=new_slug,
        preferences_hash=preferences_hash,
        input_payload=payload_dict,
        schedule_data=schedule_json_data
    )
    
    return {"slug": new_slug, "events": full_schedule}

def get_distance_lookup(db: Session) -> Dict[Tuple[str, str], int]:
    """Loads all location-to-location walking times into memory."""
    rows = db.execute(
        text("""
            SELECT location_a, location_b, distance_minutes
            FROM location_distances
        """)
    ).fetchall()

    lookup: Dict[Tuple[str, str], int] = {}
    for from_name, to_name, minutes in rows:
        lookup[(from_name, to_name)] = minutes
        # Fallback in case location_distances only stores one direction per pair
        if (to_name, from_name) not in lookup:
            lookup[(to_name, from_name)] = minutes

    return lookup

def attach_walking_times(schedule_slots: List[dict], db: Session) -> List[dict]:
    """
    Populates `next_location_walking_minutes` on each performance and activity
    by looking ahead to the next non-announcement event on the same festival day.
    """
    if not schedule_slots:
        return schedule_slots

    # Ensure chronological order before scanning ahead
    sorted_slots = sorted(schedule_slots, key=lambda s: s["start_time"])
    distance_lookup = get_distance_lookup(db)

    non_actionable_locations = {None, "", "All", "All Locations", "Shipwide / Informational"}

    for i, current in enumerate(sorted_slots):
        current["next_location_walking_minutes"] = None

        # Only performances and activities get a "Next Up" prompt (skip announcements)
        if current.get("category") == "announcement":
            continue

        current_festival_day = current["start_time"].date()

        # Scan forward to find the next actionable performance or activity
        next_actionable = None
        for j in range(i + 1, len(sorted_slots)):
            candidate = sorted_slots[j]
            if candidate.get("category") == "announcement":
                continue
            if candidate.get("location_name") in non_actionable_locations:
                continue
            next_actionable = candidate
            break

        if not next_actionable:
            continue

        # Skip if the next event is on a different festival day (current is final event of the day)
        next_festival_day = next_actionable["start_time"].date()
        if next_festival_day != current_festival_day:
            continue

        from_loc_name = current.get("location_name")
        to_loc_name = next_actionable.get("location_name")

        if from_loc_name and to_loc_name:
            if from_loc_name == to_loc_name:
                current["next_location_walking_minutes"] = 0
            else:
                current["next_location_walking_minutes"] = distance_lookup.get(
                    (from_loc_name, to_loc_name)
                )

    return sorted_slots