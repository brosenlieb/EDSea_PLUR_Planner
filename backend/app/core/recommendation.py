from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.db.models import Artist

def get_recommendations(db: Session, favorite_artist_ids: list[int], limit: int = 10):
    """
    Takes a list of artist IDs a user likes, computes their average vector profile,
    and returns similar artists from the festival lineup.
    """
    # 1. Fetch the embeddings for the user's favorite artists
    favorites = db.query(Artist).filter(Artist.id.in_(favorite_artist_ids)).all()
    
    if not favorites:
        return []
        
    # Extract just the vector lists
    vectors = [f.embedding for f in favorites if f.embedding is not None]
    
    if not vectors:
        return []

    # 2. Compute the "Average Taste Vector"
    # We use zip(*vectors) to group all the 1st dimensions, 2nd dimensions, etc., 
    # and then calculate the mean of each dimension.
    num_dimensions = len(vectors[0])
    avg_vector = [
        sum(col) / len(col) for col in zip(*vectors)
    ]

    # 3. Use pgvector's cosine distance (<=>) to find the closest matches
    # We exclude the artists they already selected from the recommendations
    closest_matches = (
        db.query(Artist)
        .filter(~Artist.id.in_(favorite_artist_ids))
        .order_by(Artist.embedding.cosine_distance(avg_vector))
        .limit(limit)
        .all()
    )
    
    return closest_matches