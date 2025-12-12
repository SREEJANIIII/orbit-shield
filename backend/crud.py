from sqlalchemy.orm import Session
import models, schemas

def create_space_object(db: Session, data: schemas.SpaceObjectCreate):
    obj = models.SpaceObject(
        name=data.name,
        type=data.type,
        tle_line1=data.tle_line1,
        tle_line2=data.tle_line2,
        size=data.size
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_all_objects(db: Session):
    return db.query(models.SpaceObject).all()

