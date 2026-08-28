from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from backend.app.schemas.api_models import ArtistResponse
from backend.app.api.deps import get_db
from backend.app.db.models import Artist

router = APIRouter()

@router.get("/artists", response_model=List[ArtistResponse])
def get_artists(q: str = None, limit: int = 50, db: Session = Depends(get_db)):
    """
    Fetch festival artists. 
    Optionally filter by name or genre using the '?q=' query parameter.
    """
    query = db.query(Artist)
    
    # If user types something in the frontend search box, apply a filter
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Artist.name.ilike(search_term),
                Artist.genre.ilike(search_term)
            )
        )
        
    # Order alphabetically, cap total returns if needed
    artists = query.order_by(Artist.name).limit(limit).all()
    
    return [
        ArtistResponse(
            id=a.id, 
            name=a.name, 
            genre=a.genre, 
            description=a.description
        ) for a in artists
    ]