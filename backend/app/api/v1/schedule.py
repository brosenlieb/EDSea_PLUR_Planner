from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.schemas.api_models import ScheduleRequest, PerformanceSlot
from backend.app.api.deps import get_db
from backend.app.core.recommendation import get_recommendations
from backend.app.core.solver import generate_optimal_schedule
from backend.app.db.models import Performance, LocationDistance

router = APIRouter()

@router.post("/schedule/generate", response_model=list[PerformanceSlot])
def generate_schedule(payload: ScheduleRequest, db: Session = Depends(get_db)):
    # Grab AI recommendations to pad out the user's favorites
    recommended_artists = get_recommendations(db, payload.favorite_artist_ids, limit=10)
    recommended_ids = [a.id for a in recommended_artists]
    # Combine them into a single target pool
    target_artist_ids = payload.favorite_artist_ids + recommended_ids
    
    # Fetch all performances for combined pool
    db_performances = db.query(Performance).filter(
        Performance.artist_id.in_(target_artist_ids)
    ).all()
    
    # Format the data for the solver function
    performances_for_solver = []
    for p in db_performances:
        performances_for_solver.append({
            "id": p.id,
            "artist_id": p.artist.id,
            "artist_name": p.artist.name,
            "stage_id": p.stage.id,
            "stage_name": p.stage.name,
            "location": p.stage.location,
            "stage_name": p.stage.name,
            "start_time": p.start_time,
            "end_time": p.end_time
        })
        
    # Fetch the travel matrix and map it to a dictionary keyed by tuples (Locations A, B)
    distances = db.query(LocationDistance).all()
    travel_matrix = {
        (d.location_a, d.locations_b): d.distance_minutes
        for d in distances
    }
    
    # Run the constraint solver
    schedule = generate_optimal_schedule(
        performances=performances_for_solver,
        travel_matrix=travel_matrix,
        favorite_artist_ids=payload.favorite_artist_ids
    )
    
    return schedule