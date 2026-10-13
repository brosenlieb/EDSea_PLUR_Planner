from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.db.models import Artist
from backend.app.schemas.api_models import ArtistResponse

router = APIRouter()


@router.get("/artists", response_model=List[ArtistResponse])
def get_artists(
    q: Optional[str] = None, 
    limit: int = 120, 
    db: Session = Depends(get_db)
) -> List[ArtistResponse]:
    """Fetch festival artists from the database.

    This endpoint retrieves a list of artists. An optional query parameter
    'q' can be used to filter results by name or genre.

    Args:
        q: Optional search string to filter artists by name or genre.
        limit: The maximum number of artists to return. Defaults to 120.
        db: The database session instance.

    Returns:
        A list of ArtistResponse models containing artist details.
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