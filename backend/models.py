# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base
from datetime import datetime

class SpaceObject(Base):
    __tablename__ = "space_objects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)  # "satellite" or "debris"
    tle_line1 = Column(String, nullable=True)
    tle_line2 = Column(String, nullable=True)
    size = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    object1_id = Column(Integer, ForeignKey("space_objects.id"), nullable=False)
    object2_id = Column(Integer, ForeignKey("space_objects.id"), nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_class = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
