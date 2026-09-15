from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.models import Activity
from backend.app.api.deps import get_db

router = APIRouter()

@router.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    return db.query(Activity).all()