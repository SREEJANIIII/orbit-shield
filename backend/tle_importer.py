# tle_importer.py  (REPLACE your existing file with this)
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from spacetrack import SpaceTrackClient

# DB helper (used by import_tle_to_db)
from database import SessionLocal
import models

load_dotenv()

SPACE_TRACK_USER = os.getenv("SPACE_TRACK_USER")
SPACE_TRACK_PASS = os.getenv("SPACE_TRACK_PASS")

logger = logging.getLogger("tle_importer")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
logger.setLevel(os.environ.get("TLE_IMPORTER_LOGLEVEL", "INFO").upper())


def _normalize_tle_entry(raw_entry: Any, norad_id: int) -> Optional[Dict[str, str]]:
    """
    Normalize a single Space-Track 'tle_latest' entry into a dict:
      { "line1": "...", "line2": "...", "name": "..." }
    Handles cases where the API returns:
      - a dict with keys like 'TLE_LINE1', 'TLE_LINE2', 'OBJECT_NAME'
      - a plain string containing TLE lines (one or two lines)
      - a multiline string (name + lines, or just lines)
    """
    try:
        # Case A: dict-like (typical when format='json')
        if isinstance(raw_entry, dict):
            line1 = raw_entry.get("TLE_LINE1") or raw_entry.get("line1") or raw_entry.get("LINE1")
            line2 = raw_entry.get("TLE_LINE2") or raw_entry.get("line2") or raw_entry.get("LINE2")
            name = raw_entry.get("OBJECT_NAME") or raw_entry.get("name") or f"NORAD-{norad_id}"
            if line1 and line2:
                return {"line1": line1.strip(), "line2": line2.strip(), "name": name.strip() if name else f"NORAD-{norad_id}"}
            # Some JSON entries return the TLE as a single string under a different key
            for k in raw_entry:
                if isinstance(raw_entry[k], str) and ("\n" in raw_entry[k] or raw_entry[k].startswith("1 ")):
                    text = raw_entry[k].strip()
                    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                    if len(lines) >= 2:
                        return {"line1": lines[0], "line2": lines[1], "name": name.strip() if name else f"NORAD-{norad_id}"}
            return None

        # Case B: string-like (sometimes returned)
        if isinstance(raw_entry, str):
            text = raw_entry.strip()
            # If it's a single-line TLE blob separated by newlines
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if len(lines) >= 2:
                # If the first line looks like a name (not starting with '1 '), try to detect
                if not lines[0].startswith("1 ") and not lines[0].startswith("2 "):
                    # name + two tle lines?
                    if len(lines) >= 3 and lines[1].startswith("1 ") and lines[2].startswith("2 "):
                        return {"line1": lines[1], "line2": lines[2], "name": lines[0]}
                # else assume first two lines are TLE lines
                return {"line1": lines[0], "line2": lines[1], "name": f"NORAD-{norad_id}"}

        # Unknown format
        return None
    except Exception as e:
        logger.exception("Normalization failure for NORAD %s: %s", norad_id, e)
        return None


def fetch_latest_tle(norad_id: int) -> Optional[Dict[str, str]]:
    """
    Fetch the latest TLE for a given NORAD id using spacetrack.
    Returns a dict with keys: line1, line2, name  OR None if not found/errored.
    """
    if not SPACE_TRACK_USER or not SPACE_TRACK_PASS:
        logger.error("SPACE_TRACK_USER / SPACE_TRACK_PASS not set in environment")
        return None

    try:
        st = SpaceTrackClient(identity=SPACE_TRACK_USER, password=SPACE_TRACK_PASS)

        # Request JSON first (preferred)
        tle_data = st.tle_latest(
            norad_cat_id=norad_id,
            ordinal=1,
            format="json"
        )

        # If returned value is a single string (some API versions), try a different call
        if not tle_data:
            logger.warning("No TLE JSON returned for NORAD ID %s; trying 'tle' text format", norad_id)
            raw = st.tle_latest(norad_cat_id=norad_id, ordinal=1, format="tle")
            # some clients return the raw text or a list
            if isinstance(raw, list) and raw:
                raw_entry = raw[0]
            else:
                raw_entry = raw
            norm = _normalize_tle_entry(raw_entry, norad_id)
            if norm:
                return norm
            return None

        # tle_data can be a list of dicts or list of strings
        first = tle_data[0] if isinstance(tle_data, (list, tuple)) and len(tle_data) > 0 else tle_data

        norm = _normalize_tle_entry(first, norad_id)
        if norm:
            return norm

        # As a last resort, try fetching raw 'tle' text and normalize
        try:
            raw2 = st.tle_latest(norad_cat_id=norad_id, ordinal=1, format="tle")
            if isinstance(raw2, (list, tuple)) and raw2:
                raw_first = raw2[0]
            else:
                raw_first = raw2
            return _normalize_tle_entry(raw_first, norad_id)
        except Exception:
            return None

    except Exception as e:
        logger.exception("Error fetching TLE for NORAD ID %s: %s", norad_id, e)
        return None


def import_tle_to_db(norad_id: int, obj_type: str = "satellite", size: Optional[float] = None, db_session=None):
    """
    Fetch latest TLE and insert (or update) a SpaceObject row.
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

