from datetime import datetime, timedelta
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo, AliasChoices, model_validator

# Accept several different forms of inputs
class RawEventInput(BaseModel):
    location_name: Optional[str] = Field(
        default="Shipwide", 
        validation_alias=AliasChoices("location_name", "location", "area"),
        allow_none=True
    )
    
    event_name: Union[str, list[str]] = Field(
        ..., 
        validation_alias=AliasChoices("artist_name", "artist", "artist_event", "event", "artist_names")
    )

    stage_name: Optional[str] = Field(
        default="n/a", 
        validation_alias=AliasChoices("stage_name", "stage"),
        allow_none=True
        )

    # Add a blank event_date field, which will be populated in seed_db.py based on the
    # SCHEDULE_FILES field.
    event_date: Optional[str] = None

    # Time variable names are currently consistent across JSON files, so no aliases are needed
    start_time: datetime
    # end_times optional for several announcments which only provide start times
    end_time: Optional[datetime] = None

    # Clean text casing; works for both single strings or lists
    @field_validator("stage_name", "event_name", "location_name", mode="before")
    @classmethod
    def normalize_casing(cls, v: Union[str, list[str], None]) -> Union[str, list[str], None]:
        def _clean(text: str) -> str:
            text = text.strip().title()
            acronyms = {"W/": "w/", "It'S": "It's", "Og": "OG", "Edsea": "EDSea"}
            for word, replacement in acronyms.items():
                text = text.replace(word, replacement)
            return text

        if isinstance(v, str):
            return _clean(v)
        elif isinstance(v, list):
            return [_clean(item) for item in v if isinstance(item, str)]
        return v

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_time_string(cls, v: str | datetime, info: ValidationInfo) -> Optional[datetime]:
        # Pass through None values to be handled by finalize_timestamps
        if v is None:
            return None

        # If already a datetime, pass through
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            # Catch various forms of "none" in JSON due to OCR extraction
            clean_str = v.strip().lower()
            if not clean_str or clean_str in ("none", "null", "n/a", "undefined"):
                return None

            v_str = v.strip().upper()
            
            # Retrieve date injected into validation context (defaults to today if missing)
            base_date_str = info.data.get("event_date")
            if not base_date_str:
                base_date_str = datetime.today().strftime("%Y-%m-%d")
            
            # Parse time string formats like "5:30PM" or "05:30 PM"
            for fmt in ("%I:%M%p", "%I:%M %p"):
                try:
                    parsed_time = datetime.strptime(v_str, fmt).time()
                    base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
                    return datetime.combine(base_date, parsed_time)
                except ValueError:
                    continue
            
            # Fallback for ISO strings or already formatted date-time strings
            try:
                return datetime.fromisoformat(v_str)
            except ValueError:
                pass

        raise ValueError(f"Could not parse time string: '{v}'")

    @model_validator(mode="after")
    def finalize_timestamps(self) -> "RawEventInput":
        # After field-level parsing, check for missing end_times and set them to 15 minutes
        # after the event's start_time.
        if self.end_time is None and self.start_time is not None:
            self.end_time = self.start_time + timedelta(minutes=15)
        
        # Seems like an unlikely issue, but adding same post-midnight collision handling
        elif self.end_time and self.start_time and self.end_time < self.start_time:
            self.end_time += timedelta(days=1)
            
        return self

# Allow for other time-event types besides just musical performances
class StandardizedEvent(RawEventInput):
    # Derived fields added after validation
    event_type: Literal["performance", "activity", "announcement"] = "performance"
    
    # Classify the event type based on text patterns
    @model_validator(mode="after")
    def classify_event(self) -> "StandardizedEvent":
        # Flattens artist list for B2B performances w/ multiple artists
        if isinstance(self.event_name, list):
            entity = " ".join(self.event_name).lower()
        else:
            entity = self.event_name.lower()
        
        announcement_keywords = ["opens", "close", "arrive", "safety messaging", "sail away", "all aboard"]
        activity_keywords = [
            "yoga", "convoy", "toast", "cartoons", "brunch", "bingo", "open deck","ravercise",
            "comedy", "sound healing", "weddings", "sandcastle", "appreciation", "feud",
            "class", "mario", "up to date"
        ]
        
        if any(kw in entity for kw in announcement_keywords):
            self.event_type = "announcement"
        elif any(kw in entity for kw in activity_keywords):
            self.event_type = "activity"
        else:
            self.event_type = "performance"
            
        return self
