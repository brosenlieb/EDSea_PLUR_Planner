from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.schemas.api_models import RecommendationRequest, RecommendedArtist
from backend.app.api.deps import get_db
from backend.app.core.recommendation import get_recommendations

router = APIRouter()

@router.post("/recommendations", response_model=list[RecommendedArtist])
def create_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)):
    if not payload.favorite_artist_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one favorite artist.")
    
    # Call the recommendation engine
    matches = get_recommendations(db, payload.favorite_artist_ids, payload.limit)
    
    # Map the SQLAlchemy database models to the Pydantic response models
    return [
        RecommendedArtist(id=m.id, name=m.name, genre=m.genre)
        for m in matches
    ]