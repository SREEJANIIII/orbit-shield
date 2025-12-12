from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
import models, schemas, crud
import os
import math, numpy as np, joblib
from datetime import datetime

app = FastAPI(title="OrbitShield Backend API")

# -----------------------------
# Database setup
# -----------------------------
Base.metadata.create_all(bind=engine)

# -----------------------------
# CORS for deployed frontend
# -----------------------------
FRONTEND_URL = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load AI model
# -----------------------------
AI_MODEL_PATH = os.environ.get("AI_MODEL_PATH", "collision_ai_model.pkl")
try:
    ai_model = joblib.load(AI_MODEL_PATH)
    print("AI model loaded successfully.")
except Exception:
    ai_model = None
    print("AI model NOT FOUND, fallback enabled.")

# -----------------------------
# AI risk scoring
# -----------------------------
def run_ai_scoring(distance, speed, size_sat, size_deb, history, noise):
    if ai_model:
        X = np.array([[distance, speed, size_sat, size_deb, history, noise]])
        prob = ai_model.predict_proba(X)[0][1]
        risk_score = int(prob * 100)
    else:
        risk_score = int(max(0, min(100, (20-distance)*3 + speed*5 + size_deb*4 + history*2 + noise*10)))

    if risk_score > 70:
        return {"risk_score": risk_score, "risk_class": "HIGH"}
    elif risk_score > 40:
        return {"risk_score": risk_score, "risk_class": "MEDIUM"}
    else:
        return {"risk_score": risk_score, "risk_class": "LOW"}

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
def root():
    return {"message": "OrbitShield Backend is running!"}

@app.post("/add_object", response_model=schemas.SpaceObjectOut)
def add_object(obj: schemas.SpaceObjectCreate, db: Session = Depends(get_db)):
    return crud.create_space_object(db, obj)

@app.get("/objects")
def list_objects(db: Session = Depends(get_db)):
    return crud.get_all_objects(db)

@app.post("/ai_predict")
def ai_predict(distance: float, speed: float, size_sat: float, size_deb: float, history: int, tle_noise: float):
    return run_ai_scoring(distance, speed, size_sat, size_deb, history, tle_noise)

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

