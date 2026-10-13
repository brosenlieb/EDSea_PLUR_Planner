"""
Pydantic models for API request and response schemas.

This module defines the data models used for validation and serialization
within the Festival Planner API.
"""
from pydantic import BaseModel, field_serializer
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

EASTERN_TZ = ZoneInfo("America/New_York")

class ArtistResponse(BaseModel):
    """
    Schema representing an artist for API responses.

    Attributes:
        id (int): The unique identifier for the artist.
        name (str): The name of the artist.
        genre (str): The genre of music performed by the artist.
        description (Optional[str]): A brief description of the artist.
    """
    id: int
    name: str
    genre: str
    description: str | None = None

class RecommendationRequest(BaseModel):
    """
    Request schema for generating artist recommendations.

    Attributes:
        favorite_artist_ids (List[int]): A list of IDs of the user's favorite artists.
        limit (int): The maximum number of recommendations to return. Defaults to 10.
    """
    favorite_artist_ids: List[int]
    limit: int = 10

class RecommendedArtist(BaseModel):
    """
    Schema representing a recommended artist.

    Attributes:
        id (int): The unique identifier for the recommended artist.
        name (str): The name of the recommended artist.
        genre (str): The genre of the recommended artist.
    """
    id: int
    name: str
    genre: str

class ActivityPreference(BaseModel):
    """
    Schema representing a user's preference for a specific activity.

    Attributes:
        activity_id (int): The unique identifier for the activity.
        priority (Literal["must_have", "nice_to_have"]): The priority level of this activity.
    """
    activity_id: int
    priority: Literal["must_have", "nice_to_have"]

class ScheduleRequest(BaseModel):
    """
    Request schema for generating a personalized schedule.

    Attributes:
        favorite_artist_ids (List[int]): A list of IDs of the user's favorite artists.
        activity_preferences (Optional[List[ActivityPreference]]): A list of activity preferences.
    """
    favorite_artist_ids: List[int]
    activity_preferences: Optional[List[ActivityPreference]] = []

class PerformanceSlot(BaseModel):
    """
    Schema representing a performance slot in the festival schedule.

    Attributes:
        id (int): The unique identifier for the slot.
        artist_id (int): The ID of the performing artist.
        artist_name (str): The name of the performing artist.
        stage_id (int): The ID of the stage where the performance takes place.
        stage_name (str): The name of the stage.
        location (str): The location description.
        start_time (datetime): The start time of the performance.
        end_time (datetime): The end time of the performance.
    """
    id: int
    artist_id: int
    artist_name: str
    stage_id: int
    stage_name: str
    location: str
    start_time: datetime
    end_time: datetime

class EventSlot(BaseModel):
    """
    Schema representing an event slot (performance or activity).

    Attributes:
        id (str): The unique identifier for the event.
        title (str): The title of the event.
        event_type (Literal["performance", "activity"]): The type of the event.
        start_time (datetime): The start time of the event.
        end_time (datetime): The end time of the event.
        location_id (Optional[int]): The ID of the location.
        location_name (str): The name of the location.
        stage_name (Optional[str]): The name of the stage, if applicable.
        artist_ids (Optional[list[int]]): List of artist IDs for performances.
        category (Optional[str]): The category for activities.
        priority (Optional[str]): The priority for activities.
    """
    id: str 
    title: str
    event_type: Literal["performance", "activity"]
    start_time: datetime
    end_time: datetime
    location_id: int | None = None
    location_name: str = "All Locations"
    stage_name: Optional[str] = "n/a"
    
    # Performance-specific fields
    artist_ids: Optional[list[int]] = None
    
    # Activity-specific fields
    category: Optional[str] = None
    priority: Optional[str] = None

    # Help catch instances where times are still in UTC
    @field_serializer('start_time', 'end_time')
    def serialize_dt_to_eastern(self, dt: datetime, _info) -> str:
        """
        Serializes datetime objects to Eastern timezone ISO 8601 string.

        If the datetime is naive (no timezone info), it assumes UTC and converts to Eastern.

        Args:
            dt (datetime): The datetime object to serialize.
            _info: Serializer info context (required by Pydantic).

        Returns:
            str: The datetime as an ISO 8601 string with Eastern offset.
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        # Returns ISO 8601 string with Eastern offset (-04:00 or -05:00)
        return dt.astimezone(EASTERN_TZ).isoformat()
    
    class Config:
        """
        Configuration for the Pydantic model.
        """
        from_attributes = True