from pydantic import BaseModel
from typing import Optional

class SpaceObjectBase(BaseModel):
    name: str
    type: str
    tle_line1: Optional[str] = None
    tle_line2: Optional[str] = None
    size: float

class SpaceObjectCreate(SpaceObjectBase):
    pass

class SpaceObjectOut(SpaceObjectBase):
    id: int

    class Config:
        orm_mode = True
