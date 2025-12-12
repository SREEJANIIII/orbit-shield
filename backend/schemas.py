from pydantic import BaseModel

class SpaceObjectBase(BaseModel):
    name: str
    type: str
    tle_line1: str
    tle_line2: str
    size: float

class SpaceObjectCreate(SpaceObjectBase):
    pass

class SpaceObjectOut(SpaceObjectBase):
    id: int
    class Config:
        orm_mode = True
