from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ValidationInfo

# Accept several different forms of inputs
class RawEventInput(BaseModel):
    location_name: str = Field(
        ..., 
        validation_alias="location_name" | "location" | "area"
    )
    
    event_name: str = Field(
        ..., 
        validation_alias="artist_name" | "artist" | "artist_event" | "event"
    )

    stage_name: str = Field(
            default="n/a", 
            validation_alias="stage_name" | "stage"
        )

    # Clean text casing
    @field_validator("stage_name", "event_name", "location_name", mode="before")
    @classmethod
    def normalize_casing(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().title()
            # Preserve certain acronyms if desired
            # acronyms = {"Dj": "DJ", "Mc": "MC", "Vip": "VIP", "Q&a": "Q&A"}
            # for word, replacement in acronyms.items():
                # v = v.replace(word, replacement)
        return v

# Allow for other time-event types besides just musical performances
class StandardizedEvent(RawEventInput):
    # Derived fields added after validation
    event_type: Literal["performance", "activity", "announcement"] = "performance"
    
    # Classify the event type based on text patterns
    @field_validator("event_type", mode="before")
    @classmethod
    def classify_event(cls, v: str, info: ValidationInfo) -> str:
        entity = info.data.get("entity_name", "").lower()
        
        announcement_keywords = ["opens", "close", "arrive", "safety messaging", "sail away", "all aboard"]
        activity_keywords = [
            "yoga", "convoy", "toast", "cartoons", "brunch", "bingo", "open deck","ravercise",
            "comedy", "sound healing", "weddings", "sandcastle", "appreciation", "feud",
            "class", "mario"
        ]
        
        if any(kw in entity for kw in announcement_keywords):
            return "announcement"
        if any(kw in entity for kw in activity_keywords):
            return "activity"
        return "performance"
