"""
CRUD operations for SavedSchedule model.

This module provides database operations for creating and retrieving
saved festival schedules.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.db.models import SavedSchedule


def create_saved_schedule(
    db: Session,
    slug: str,
    preferences_hash: str,
    input_payload: Dict[str, Any],
    schedule_data: List[Dict[str, Any]]
) -> SavedSchedule:
    """
    Create a new saved schedule and persist it to the database.

    Args:
        db: Database session from FastAPI dependency injection
        slug: Unique identifier for the schedule (e.g., "8f9a2b")
        preferences_hash: SHA-256 hash of user preferences for cache lookups
        input_payload: Raw user input containing artists and constraints
        schedule_data: Final calculated schedule output from OR-Tools solver

    Returns:
        SavedSchedule: The newly created schedule object

    Example:
        >>> schedule = create_saved_schedule(
        ...     db=session,
        ...     slug="abc123",
        ...     preferences_hash="sha256hash...",
        ...     input_payload={"artist_ids": [1, 2, 3]},
        ...     schedule_data=[{"title": "Artist A", "start_time": "2024-01-01T10:00:00Z"}]
        ... )
    """
    db_schedule = SavedSchedule(
        slug=slug,
        preferences_hash=preferences_hash,
        input_payload=input_payload,
        schedule_data=schedule_data
    )

    db.add(db_schedule)
    
    try:
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    except SQLAlchemyError as e:
        db.rollback()  # Revert changes if something went wrong
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while saving the schedule. Please try again later."
        )


def get_saved_schedule_by_slug(
    db: Session,
    slug: str
) -> Optional[SavedSchedule]:
    """
    Retrieve a saved schedule by its unique slug.

    Args:
        db: Database session from FastAPI dependency injection
        slug: Unique identifier of the schedule to retrieve

    Returns:
        Optional[SavedSchedule]: The schedule object if found, None otherwise

    Example:
        >>> schedule = get_saved_schedule_by_slug(db=session, slug="abc123")
        >>> if schedule:
        ...     print(schedule.schedule_data)
    """
    return (
        db.query(SavedSchedule)
        .filter(SavedSchedule.slug == slug)
        .first()
    )


def get_saved_schedule_by_preferences_hash(
    db: Session,
    preferences_hash: str
) -> Optional[SavedSchedule]:
    """
    Retrieve a saved schedule by its preferences hash for cache lookups.

    Args:
        db: Database session from FastAPI dependency injection
        preferences_hash: SHA-256 hash of user preferences

    Returns:
        Optional[SavedSchedule]: The schedule object if found, None otherwise

    Example:
        >>> schedule = get_saved_schedule_by_preferences_hash(
        ...     db=session,
        ...     preferences_hash="sha256hash..."
        ... )
        >>> if schedule:
        ...     print("Cache hit!")
    """
    return (
        db.query(SavedSchedule)
        .filter(SavedSchedule.preferences_hash == preferences_hash)
        .first()
    )