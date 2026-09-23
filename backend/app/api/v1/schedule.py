from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload, joinedload
from backend.app.schemas.api_models import ScheduleRequest, EventSlot
from backend.app.api.deps import get_db
from backend.app.core.recommendation import get_recommendations
from backend.app.core.solver import generate_optimal_schedule
from backend.app.db.models import Performance, Activity, LocationDistance, Announcement
from zoneinfo import ZoneInfo
from datetime import timedelta

router = APIRouter()

EASTERN_TZ = ZoneInfo("America/New_York")

def to_eastern(dt):
    """Converts DB datetime to Eastern Time wall-clock time."""
    if dt is None:
        return None
    # Strip attached timezone (e.g. UTC from DB driver) then assign Eastern
    dt_naive = dt.replace(tzinfo=None)
    
    # If the event is between 12:00 AM and 5:59 AM, shift it to 
    # the next calendar day so chronological sorting and solving work properly.
    if dt_naive.hour < 6:
        dt_naive += timedelta(days=1)

    return dt_naive.replace(tzinfo=EASTERN_TZ)

# Location name extraction for null values
def get_location_name(entity, default: str) -> str:
    if entity and getattr(entity, "location", None):
        return getattr(entity.location, "location_name", None) or default
    return default

@router.post("/schedule/generate", response_model=list[EventSlot])
def generate_schedule(payload: ScheduleRequest, db: Session = Depends(get_db)):
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