from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.db.models import Activity

router = APIRouter()


@router.get("/activities")
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