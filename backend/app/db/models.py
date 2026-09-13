from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Location(Base):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, index=True)  # Primary spatial anchor
    stage_name = Column(String, index=True)     # Optional/Nullable sub-location
    
    # Ensures the combination of location and stage is unique
    __table_args__ = (
        UniqueConstraint('location_name', 'stage_name', name='uq_location_stage_name'),
    )
    
    performances = relationship("Performance", back_populates="location")
    activities = relationship("Activity", back_populates="location")
    announcements = relationship("Announcement", back_populates="location")

class Artist(Base):
    __tablename__ = 'artists'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    genre = Column(String)
    description = Column(String)
    embedding = Column(Vector(768))
    
    performances = relationship("Performance", back_populates="artist")

class Performance(Base):
    __tablename__ = 'performances'
    
    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey('artists.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    artist = relationship("Artist", back_populates="performances")
    location = relationship("Location", back_populates="performances")

class Activity(Base):
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, index=True)
    activity_name = Column(String, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    location = relationship("Location", back_populates="activities")

class Announcement(Base):
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True, index=True)
    announcement_name = Column(String, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    location = relationship("Location", back_populates="announcements")

class LocationDistance(Base):
    __tablename__ = 'location_distances'
    
    id = Column(Integer, primary_key=True, index=True)
    location_a = Column(String, index=True)
    location_b = Column(String, index=True)
    distance_minutes = Column(Integer)