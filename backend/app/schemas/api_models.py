from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

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