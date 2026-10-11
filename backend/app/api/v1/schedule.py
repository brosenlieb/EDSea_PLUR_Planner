from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload, joinedload
from backend.app.schemas.api_models import ScheduleRequest, EventSlot
from backend.app.api.deps import get_db
from backend.app.core.recommendation import get_recommendations
from backend.app.core.solver import generate_optimal_schedule
from backend.app.db.models import Performance, Activity, LocationDistance, Announcement
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from typing import Any

router = APIRouter()

EASTERN_TZ = ZoneInfo("America/New_York")

def to_eastern(dt: datetime | None) -> datetime | None:
    """Converts a database datetime to Eastern Time wall-clock time.

    Args:
        dt: The datetime object to convert. If None, returns None. Naive
            datetimes are assumed to be in UTC.

    Returns:
        The converted datetime in Eastern Time. If the resulting time is
        between 12:00 AM and 5:59 AM ET, it is shifted forward by one day
        for chronological solver sorting.
    """
    if dt is None:
        return None
        
    # If naive, assume UTC from the database
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    # Convert UTC hours to true Eastern Time hours (e.g., 20:30 UTC -> 16:30 EDT)
    dt_eastern = dt.astimezone(EASTERN_TZ)
    
    # If the event is between 12:00 AM and 5:59 AM ET, shift it
    # for chronological solver sorting if required by your pipeline
    if dt_eastern.hour < 6:
        dt_eastern += timedelta(days=1)

    return dt_eastern

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

@router.post("/schedule/generate", response_model=list[EventSlot])
def generate_schedule(payload: ScheduleRequest, db: Session = Depends(get_db)) -> list[EventSlot]:
    """Generates an optimized festival schedule based on user preferences and AI recommendations.

    This function retrieves performances, selected activities, and announcements,
    runs a constraint solver to optimize the schedule, and returns a chronologically
    sorted list of event slots.

    Args:
        payload: The request containing favorite artist IDs and activity preferences.
        db: The database session used to fetch performances, activities, and distances.

    Returns:
        A list of sorted, optimized event slots for the user's schedule.
    """
    # Grab AI recommendations
    recommended_artists = get_recommendations(db, payload.favorite_artist_ids, limit=10)
    recommended_ids = [a.id for a in recommended_artists]
    target_artist_ids = set(payload.favorite_artist_ids + recommended_ids)
    
    # Fetch Performances
    db_performances = (
        db.query(Performance)
        .options(
            selectinload(Performance.artists),
            joinedload(Performance.location)
        )
        .all()
    )
    
    events_for_solver = []
    
    # Format Performances for solver
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

    # Fetch & Format Activities based on user preferences
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
        
    # Fetch the travel matrix
    distances = db.query(LocationDistance).all()
    travel_matrix = {
        (d.location_a, d.location_b): d.distance_minutes
        for d in distances
    }
    
    # Run the constraint solver ONLY on performances & user-selected activities
    solved_schedule = generate_optimal_schedule(
        events=events_for_solver,
        travel_matrix=travel_matrix,
        favorite_artist_ids=payload.favorite_artist_ids
    )
    
    # Fetch Announcements (bypassing the solver)
    db_announcements = db.query(Announcement).options(joinedload(Announcement.location)).all()

    announcement_slots = []
    for ann in db_announcements:
        # Read announcement_name directly from the DB model with fallbacks
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

    # Merge solved results with announcements
    full_schedule = list(solved_schedule) + announcement_slots

    # Sort chronologically by start_time
    def get_start_key(item):
        st = item["start_time"] if isinstance(item, dict) else item.start_time
        return st.isoformat() if hasattr(st, 'isoformat') else str(st)

    full_schedule.sort(key=get_start_key)

    return full_schedule