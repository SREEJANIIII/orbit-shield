from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from skyfield.api import load
from datetime import datetime
import numpy as np

from tle_loader import load_tles

# ---------------- APP ----------------
app = FastAPI(title="OrbitShield Backend API")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- LOAD ORBIT DATA ----------------
satellites, debris = load_tles()
ts = load.timescale()

# ---------------- HEALTH CHECK ----------------
@app.get("/")
def health():
    return {
        "status": "OrbitShield Backend Running",
        "satellites": len(satellites),
        "debris": len(debris)
    }

# ---------------- CURRENT POSITIONS ----------------
@app.get("/objects")
def get_objects():
    t = ts.now()

    sats = []
    for i, sat in enumerate(satellites):
        pos = sat.at(t).position.km
        period_min = 1440 / sat.model.no

        sats.append({
            "id": f"SAT-{i}",
            "type": "satellite",
            "x": float(pos[0]),
            "y": float(pos[1]),
            "z": float(pos[2]),
            "orbital_period_min": round(period_min, 2)
        })

    debs = []
    for i, d in enumerate(debris):
        pos = d.at(t).position.km
        debs.append({
            "id": f"DEB-{i}",
            "type": "debris",
            "x": float(pos[0]),
            "y": float(pos[1]),
            "z": float(pos[2])
        })

    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "data_source": "NORAD TLE + SGP4 propagation",
        "satellites": sats,
        "debris": debs
    }

# ---------------- TRAJECTORY PREDICTION ----------------
@app.get("/predict")
def predict(object_id: str):
    t0 = ts.now()

    # Predict one full orbit (~90 minutes)
    minutes = list(range(0, 95, 5))
    times = [t0 + m / 1440.0 for m in minutes]

    index = int(object_id.split("-")[1])
    obj = satellites[index] if object_id.startswith("SAT") else debris[index]

    trajectory = []
    for t in times:
        pos = obj.at(t).position.km
        trajectory.append({
            "x": float(pos[0]),
            "y": float(pos[1]),
            "z": float(pos[2])
        })

    # Simple AI-style risk estimation
    distances = [
        np.linalg.norm([p["x"], p["y"], p["z"]])
        for p in trajectory
    ]

    variability = np.std(distances)
    risk_score = int(max(0, min(100, 100 - variability / 10)))

    return {
        "object_id": object_id,
        "trajectory": trajectory,
        "ai_risk_score": risk_score,
        "risk_level": "HIGH" if risk_score > 70 else "LOW",
        "prediction_model": "SGP4 + heuristic AI"
    }
