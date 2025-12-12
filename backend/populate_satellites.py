# populate_satellites.py
import os
from datetime import datetime
from database import SessionLocal, engine, Base
from models import SpaceObject
from tle_importer import fetch_latest_tle

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Example list of NORAD IDs you want to import
SATELLITE_IDS = [
    25544,  # ISS
    33591,  # OneWeb example
    43205,  # Starlink example
    # Add more NORAD IDs as needed
]

def import_tle_to_db(norad_id, obj_type="satellite", size=5):
    db = SessionLocal()
    try:
        tle_data = fetch_latest_tle(norad_id)
        if not tle_data:
            print(f"No TLE found for NORAD ID {norad_id}")
            return

        # Check if already exists
        obj = db.query(SpaceObject).filter(SpaceObject.name == tle_data["name"]).first()
        if obj:
            print(f"{tle_data['name']} already exists, skipping.")
            return

        new_obj = SpaceObject(
            name=tle_data["name"],
            type=obj_type,
            tle_line1=tle_data["line1"],
            tle_line2=tle_data["line2"],
            size=size
        )
        db.add(new_obj)
        db.commit()
        print(f"Added {tle_data['name']} to DB.")
    except Exception as e:
        print(f"Error importing NORAD ID {norad_id}: {e}")
    finally:
        db.close()

if _name_ == "_main_":
    for norad_id in SATELLITE_IDS:
        import_tle_to_db(norad_id)

