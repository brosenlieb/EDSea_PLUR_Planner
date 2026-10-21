from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Activity
from app.schemas.api_models import ActivitySchema

router = APIRouter()


@router.get("/activities", response_model=List[ActivitySchema])
def get_activities(db: Session = Depends(get_db)) -> List[Activity]:
    """Retrieve all activities from the database.

    This endpoint fetches the complete list of activities registered
    in the festival schedule.

    Args:
        db: The database session instance for querying records.

    Returns:
        A list of all Activity objects currently in the database.
    """
    return db.query(Activity).all()