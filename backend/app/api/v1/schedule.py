from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload, joinedload
from backend.app.schemas.api_models import ScheduleRequest, EventSlot
from backend.app.api.deps import get_db
from backend.app.core.recommendation import get_recommendations
from backend.app.core.solver import generate_optimal_schedule
from backend.app.db.models import Performance, Activity, LocationDistance

router = APIRouter()

@router.post("/schedule/generate", response_model=list[EventSlot])
def generate_schedule(payload: ScheduleRequest, db: Session = Depends(get_db)):
    # 1. Grab AI recommendations
    recommended_artists = get_recommendations(db, payload.favorite_artist_ids, limit=10)
    recommended_ids = [a.id for a in recommended_artists]
    target_artist_ids = set(payload.favorite_artist_ids + recommended_ids)
    
    # 2. Fetch Performances (using selectinload for the Many-to-Many artists relationship)
    db_performances = (
        db.query(Performance)
        .options(
            selectinload(Performance.artists),
            joinedload(Performance.location)
        )
        .all()
    )
    
    events_for_solver = []
    
    # 3. Format Performances
    for p in db_performances:
        p_artist_ids = [a.id for a in p.artists]
        
        # Only include performance if at least one artist is in favorites or recommendations
        if not any(aid in target_artist_ids for aid in p_artist_ids):
            continue
            
        artist_names = [a.name for a in p.artists]
        # Use custom title if it exists, otherwise join artist names with " B2B "
        display_title = p.title if p.title else " B2B ".join(artist_names)
        
        events_for_solver.append({
            "id": f"perf_{p.id}",  # String prefix prevents ID collisions between tables
            "title": display_title,
            "event_type": "performance",
            "start_time": p.start_time,
            "end_time": p.end_time,
            "location_id": p.location_id,
            "location_name": p.location.location_name,
            "stage_name": p.location.stage_name,
            "artist_ids": p_artist_ids,
        })

    # 4. Fetch & Format Activities based on user preferences
    # Convert incoming prefs to a dictionary: {101: "must_have", 102: "nice_to_have"}
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
                "start_time": a.start_time,
                "end_time": a.end_time,
                "location_id": a.location_id,
                "location_name": a.location.location_name,
                "stage_name": a.location.stage_name,
                "category": a.category,
                "priority": activity_prefs.get(a.id)
            })
        
    # 5. Fetch the travel matrix
    distances = db.query(LocationDistance).all()
    travel_matrix = {
        (d.location_a, d.location_b): d.distance_minutes
        for d in distances
    }
    
    # 6. Run the constraint solver
    schedule = generate_optimal_schedule(
        events=events_for_solver,
        travel_matrix=travel_matrix,
        favorite_artist_ids=payload.favorite_artist_ids
    )
    
    return schedule