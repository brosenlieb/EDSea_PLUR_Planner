from pydantic import BaseModel, field_serializer
from typing import List, Optional, Literal
from datetime import datetime
from zoneinfo import ZoneInfo

EASTERN_TZ = ZoneInfo("America/New_York")

class ArtistResponse(BaseModel):
    id: int
    name: str
    genre: str
    description: str | None = None

class RecommendationRequest(BaseModel):
    favorite_artist_ids: List[int]
    limit: int = 10

class RecommendedArtist(BaseModel):
    id: int
    name: str
    genre: str

class ActivityPreference(BaseModel):
    activity_id: int
    priority: Literal["must_have", "nice_to_have"]

class ScheduleRequest(BaseModel):
    favorite_artist_ids: List[int]
    activity_preferences: Optional[List[ActivityPreference]] = []

class PerformanceSlot(BaseModel):
    id: int
    artist_id: int
    artist_name: str
    stage_id: int
    stage_name: str
    location:str
    start_time: datetime
    end_time: datetime

class EventSlot(BaseModel):
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
    def serialize_dt_to_eastern(self, dt: datetime, _info):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        # Returns ISO 8601 string with Eastern offset (-04:00 or -05:00)
        return dt.astimezone(EASTERN_TZ).isoformat()
    
    class Config:
        from_attributes = True