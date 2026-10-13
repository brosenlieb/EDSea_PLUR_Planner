"""
Module for database models.

This module defines the SQLAlchemy ORM models representing the database schema
for the Festival Planner application. It includes models for locations, artists,
performances, activities, announcements, and location distances.
"""
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

"""
Association table linking performances to artists (Many-to-Many).

Attributes:
    performance_id (int): The ID of the performance.
    artist_id (int): The ID of the artist.
"""
performance_artists = Table(
    'performance_artists',
    Base.metadata,
    Column('performance_id', Integer, ForeignKey('performances.id', ondelete="CASCADE"), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id', ondelete="CASCADE"), primary_key=True)
)

class Location(Base):
    """
    Represents a physical location or stage within the festival venue.

    Attributes:
        id (int): Unique identifier for the location.
        location_name (str): The primary name of the location.
        stage_name (str): The specific stage name within the location (optional).
        performances (Relationship): Associated performances at this location.
        activities (Relationship): Associated activities at this location.
        announcements (Relationship): Associated announcements at this location.
    """
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
    """
    Represents a musical act performing at the festival.

    Attributes:
        id (int): Unique identifier for the artist.
        name (str): The name of the artist.
        genre (str): The genre of music performed.
        description (str): A description of the artist.
        embedding (Vector): Vector embedding for the artist for similarity search.
        performances (Relationship): Associated performances by this artist.
    """
    __tablename__ = 'artists'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    genre = Column(String)
    description = Column(String)
    embedding = Column(Vector(768))
    
    performances = relationship("Performance", secondary=performance_artists, back_populates="artists")

class Performance(Base):
    """
    Represents a scheduled performance slot for one or more artists.

    Attributes:
        id (int): Unique identifier for the performance.
        title (str): The title of the performance (if any).
        location_id (int): Foreign key referencing the location.
        start_time (datetime): Start time of the performance.
        end_time (datetime): End time of the performance.
        artists (Relationship): Artists performing in this slot.
        location (Relationship): Location where the performance takes place.
    """
    __tablename__ = 'performances'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    artists = relationship("Artist", secondary=performance_artists, back_populates="performances")
    location = relationship("Location", back_populates="performances")

class Activity(Base):
    """
    Represents a non-musical event or activity at the festival.

    Attributes:
        id (int): Unique identifier for the activity.
        activity_name (str): The name of the activity.
        location_id (int): Foreign key referencing the location.
        start_time (datetime): Start time of the activity.
        end_time (datetime): End time of the activity.
        location (Relationship): Location where the activity takes place.
    """
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, index=True)
    activity_name = Column(String, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    location = relationship("Location", back_populates="activities")

class Announcement(Base):
    """
    Represents a scheduled announcement or general event.

    Attributes:
        id (int): Unique identifier for the announcement.
        announcement_name (str): The name or content of the announcement.
        location_id (int): Foreign key referencing the location.
        start_time (datetime): Start time of the announcement.
        end_time (datetime): End time of the announcement.
        location (Relationship): Location where the announcement is displayed.
    """
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True, index=True)
    announcement_name = Column(String, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    location = relationship("Location", back_populates="announcements")

class LocationDistance(Base):
    """
    Represents pre-computed travel distances between festival locations.

    Attributes:
        id (int): Unique identifier for the distance record.
        location_a (str): Name of the starting location.
        location_b (str): Name of the destination location.
        distance_minutes (int): Estimated travel time in minutes.
    """
    __tablename__ = 'location_distances'
    
    id = Column(Integer, primary_key=True, index=True)
    location_a = Column(String, index=True)
    location_b = Column(String, index=True)
    distance_minutes = Column(Integer)