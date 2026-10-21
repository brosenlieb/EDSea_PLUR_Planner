from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db
from app.db.models import Activity
from app.schemas.api_models import ActivitySchema

router = APIRouter()

@router.get("/activities", response_model=List[ActivitySchema])
def get_activities(db: Session = Depends(get_db)) -> List[ActivitySchema]:
    """
    Retrieve a paginated list of activities from the database.

    This endpoint fetches a subset of activities registered in the festival schedule,
    allowing for pagination to handle large datasets efficiently.

   Args:
        db (Session): The database session instance for querying records.

    Returns:
        List[ActivitySchema]: A list of all Activity objects currently in the database.

    Raises:
        HTTPException: If an error occurs while querying the database.
    """
    try:
        return db.query(Activity).all()
    except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Database error") from e
