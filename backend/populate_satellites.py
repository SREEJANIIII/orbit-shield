# populate_satellites.py
from database import SessionLocal, engine, Base
from models import SpaceObject
from tle_importer import import_tle_to_db

# ensure tables (safe because database.py already calls create_all, but keep here for standalone usage)
Base.metadata.create_all(bind=engine)

# Example list (customize)
SATELLITE_IDS = [
    25544,  # ISS
    33591,  # example
    43205,  # example
]

def import_list(ids):
    for nid in ids:
        print(f"Importing {nid} ...")
        obj = import_tle_to_db(nid, obj_type="satellite", size=5)
        if obj:
            print(f" -> {obj.name} added/updated (id={obj.id})")
        else:
            print(" -> failed or not found")

if __name__ == "__main__":
    import_list(SATELLITE_IDS)
