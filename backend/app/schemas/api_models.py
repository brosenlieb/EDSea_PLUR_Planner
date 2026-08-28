from pydantic import BaseModel
from typing import List
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

class ScheduleRequest(BaseModel):
    favorite_artist_ids: List[int]

class PerformanceSlot(BaseModel):
    id: int
    artist_id: int
    artist_name: str
    stage_id: int
    stage_name: str
    location:str
    start_time: datetime
    end_time: datetime