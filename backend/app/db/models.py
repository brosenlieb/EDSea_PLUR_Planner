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
    
    # 384 dimensions is standard for lightweight local embedding models
    # may increase to 768 if using nomic instead
    embedding = Column(Vector(384))
    
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


class StageDistance(Base):
    """
    The Travel Matrix: Defines how long it takes to walk from Stage A to Stage B.
    This is crucial for the Google OR-Tools scheduling engine later.
    """
    __tablename__ = 'stage_distances'
    
    id = Column(Integer, primary_key=True, index=True)
    stage_a_id = Column(Integer, ForeignKey('stages.id'))
    stage_b_id = Column(Integer, ForeignKey('stages.id'))
    distance_minutes = Column(Integer)