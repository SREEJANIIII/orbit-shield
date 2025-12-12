# schemas.py
from pydantic import BaseModel
from typing import Optional

class SpaceObjectBase(BaseModel):
    name: str
    type: str
    tle_line1: Optional[str] = None
    tle_line2: Optional[str] = None
    size: Optional[float] = None

    # Pydantic v2 config to allow ORM objects
    model_config = {"from_attributes": True}

class SpaceObjectCreate(SpaceObjectBase):
    pass

class SpaceObjectOut(SpaceObjectBase):
    id: int
    model_config = {"from_attributes": True}
