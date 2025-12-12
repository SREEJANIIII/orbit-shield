# tle_importer.py
import os
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from spacetrack import SpaceTrackClient

# Optional DB save
from database import SessionLocal
import models

# Load variables from .env (only used in local/dev; Render will supply env vars)
load_dotenv()

SPACE_TRACK_USER = os.getenv("SPACE_TRACK_USER")
SPACE_TRACK_PASS = os.getenv("SPACE_TRACK_PASS")

# Configure simple logger for this module
logger = logging.getLogger("tle_importer")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
logger.setLevel(os.environ.get("TLE_IMPORTER_LOGLEVEL", "INFO").upper())


def fetch_latest_tle(norad_id: int) -> Optional[Dict[str, str]]:
    """
    Fetch the latest TLE for a given NORAD catalog id using spacetrack.
    Returns a dict with keys: line1, line2, name  OR None if not found/errored.
    """
    if not SPACE_TRACK_USER or not SPACE_TRACK_PASS:
        logger.error("SPACE_TRACK_USER / SPACE_TRACK_PASS not set in environment")
        return None

    try:
        st = SpaceTrackClient(identity=SPACE_TRACK_USER, password=SPACE_TRACK_PASS)

        tle_data = st.tle_latest(
            norad_cat_id=norad_id,
            ordinal=1,
            format="json"
        )

        if not tle_data:
            logger.warning("No TLE data returned for NORAD ID %s", norad_id)
            return None

        # spacetrack returns a list of dict(s)
        entry = tle_data[0]
        return {
            "line1": entry.get("TLE_LINE1"),
            "line2": entry.get("TLE_LINE2"),
            "name": entry.get("OBJECT_NAME")
        }

    except Exception as e:
        logger.exception("Error fetching TLE for NORAD ID %s: %s", norad_id, e)
        return None


def import_tle_to_db(
    norad_id: int,
    obj_type: str = "satellite",
    size: Optional[float] = None,
    db_session: Optional[SessionLocal] = None
) -> Optional[models.SpaceObject]:
    """
    Fetch latest TLE and insert (or update) a SpaceObject row.
    - norad_id: NORAD catalog id (used only for fetching)
    - obj_type: 'satellite' or 'debris'
    - size: optional physical size value (float)
    - db_session: optional SQLAlchemy session (if None, function opens/closes one)

    Returns the created/updated models.SpaceObject instance or None on failure.
    """
    tle = fetch_latest_tle(norad_id)
    if not tle:
        logger.info("No TLE to import for NORAD ID %s", norad_id)
        return None

    close_session = False
    db = db_session
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Try to find an existing object with same name (OBJECT_NAME may not be unique in some edge cases)
        existing = db.query(models.SpaceObject).filter(models.SpaceObject.name == tle["name"]).first()
        if existing:
            logger.info("Updating existing SpaceObject (id=%s, name=%s)", existing.id, existing.name)
            existing.tle_line1 = tle["line1"]
            existing.tle_line2 = tle["line2"]
            if size is not None:
                existing.size = size
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        # Otherwise create new
        new_obj = models.SpaceObject(
            name=tle["name"],
            type=obj_type,
            tle_line1=tle["line1"],
            tle_line2=tle["line2"],
            size=size
        )
        db.add(new_obj)
        db.commit()
        db.refresh(new_obj)
        logger.info("Inserted new SpaceObject id=%s name=%s", new_obj.id, new_obj.name)
        return new_obj

    except Exception as e:
        logger.exception("Failed to import TLE into DB for NORAD ID %s: %s", norad_id, e)
        try:
            db.rollback()
        except Exception:
            pass
        return None

    finally:
        if close_session:
            db.close()
