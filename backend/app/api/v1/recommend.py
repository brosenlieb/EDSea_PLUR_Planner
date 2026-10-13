from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.core.recommendation import get_recommendations
from backend.app.schemas.api_models import RecommendationRequest, RecommendedArtist

router = APIRouter()


@router.post("/recommendations", response_model=List[RecommendedArtist])
def create_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)) -> List[RecommendedArtist]:
    """Generate artist recommendations based on user preferences.

    This endpoint takes a list of favorite artist IDs, retrieves AI-generated
    recommendations based on those preferences, and returns a list of suggested artists.

    Args:
        payload: The request payload containing the list of favorite artist IDs.
        db: The database session instance.

    Returns:
        A list of RecommendedArtist models representing the suggested artists.

    Raises:
        HTTPException: Raised if no favorite artist IDs are provided in the payload.
    """
    if not payload.favorite_artist_ids:
        raise HTTPException(status_code=400, detail="Must provide at least one favorite artist.")
    
    # Call the recommendation engine
    matches = get_recommendations(db, payload.favorite_artist_ids, payload.limit)
    
    # Map the SQLAlchemy database models to the Pydantic response models
    return [
        RecommendedArtist(id=m.id, name=m.name, genre=m.genre)
        for m in matches
    ]