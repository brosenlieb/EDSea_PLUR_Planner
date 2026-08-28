from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Stage(Base):
    __tablename__ = 'stages'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location_name = Column(String, index=True)
    
    # Ensures the combination of stage name and location is unique
    __table_args__ = (
        UniqueConstraint('name', 'location_name', name='uq_stage_name_location'),
    )
    
    performances = relationship("Performance", back_populates="stage")


class Artist(Base):
    __tablename__ = 'artists'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    genre = Column(String)
    description = Column(String)

    # 768-dimensions using Nomic 1.5.  Small list size should not present
    # any computational concerns compared to 384-dimensions.
    embedding = Column(Vector(768))
    
    performances = relationship("Performance", back_populates="artist")


class Performance(Base):
    __tablename__ = 'performances'
    
    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey('artists.id'))
    stage_id = Column(Integer, ForeignKey('stages.id'))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    artist = relationship("Artist", back_populates="performances")
    stage = relationship("Stage", back_populates="performances")


class LocationDistance(Base):
    """
    The Travel Matrix: Defines how long it takes to walk from Stage A to Stage B.
    Necessary for Google OR-Tools scheduling engine.
    """
    __tablename__ = 'location_distances'
    
    id = Column(Integer, primary_key=True, index=True)
    location_a = Column(String, index=True)
    location_b = Column(String, index=True)
    distance_minutes = Column(Integer)