# trajectory_ws.py
import asyncio
import json
import math
import os
import time
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import joblib
from sgp4.api import Satrec, jday
import numpy as np
from datetime import datetime

app = FastAPI(title="OrbitShield Trajectory WS")

# Token store for WS
TOKEN_STORE = {}
TOKEN_TTL_SEC = int(os.environ.get("TOKEN_TTL_SEC", 600))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "")

# AI model loading (path configurable via env)
AI_MODEL_PATH = os.environ.get("AI_MODEL_PATH", "collision_ai_model.pkl")
try:
    ai_model = joblib.load(AI_MODEL_PATH)
except Exception:
    ai_model = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.clients = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.add(ws)

    def disconnect(self, ws: WebSocket):
        self.clients.discard(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(json.dumps(data))
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

manager = ConnectionManager()

async def get_token(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token or token not in TOKEN_STORE:
        raise HTTPException(status_code=4001, detail="Auth failed")
    if TOKEN_STORE[token] < int(time.time() * 1000):
        TOKEN_STORE.pop(token, None)
        raise HTTPException(status_code=4001, detail="Token expired")
    return token

@app.post("/auth/token")
async def create_token():
    token = str(uuid.uuid4())
    expiry = int(time.time() * 1000) + TOKEN_TTL_SEC * 1000
    TOKEN_STORE[token] = expiry
    return {"token": token, "expiry": expiry}

def propagate_tle(line1: str, line2: str, timestamp: datetime):
    try:
        sat = Satrec.twoline2rv(line1, line2)
        jd, fr = jday(
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second + timestamp.microsecond * 1e-6,
        )
        error, r, v = sat.sgp4(jd, fr)
        if error != 0:
            return None
        return {
            "x": float(r[0]),
            "y": float(r[1]),
            "z": float(r[2]),
            "vx": float(v[0]),
            "vy": float(v[1]),
            "vz": float(v[2]),
        }
    except:
        return None

def relative_speed(p1, p2):
    dv = np.array([p1["vx"] - p2["vx"], p1["vy"] - p2["vy"], p1["vz"] - p2["vz"]])
    return float(np.linalg.norm(dv))

def run_ai(distance, speed, size_sat, size_deb, history=0, noise=0.2):
    if ai_model:
        X = np.array([[distance, speed, size_sat, size_deb, history, noise]])
        prob = ai_model.predict_proba(X)[0][1]
        risk_score = int(prob * 100)
    else:
        risk_score = int(max(0, min(100, (20 - distance) * 3 + speed * 5 + size_deb * 4)))
    if risk_score > 70:
        return {"risk_score": risk_score, "risk_class": "HIGH"}
    if risk_score > 40:
        return {"risk_score": risk_score, "risk_class": "MEDIUM"}
    return {"risk_score": risk_score, "risk_class": "LOW"}

@app.websocket("/ws/positions")
async def ws_positions(ws: WebSocket, token: str = Depends(get_token), db: Session = Depends(get_db)):
    # Optional origin check
    origin = ws.headers.get("origin")
    if FRONTEND_URL and origin != FRONTEND_URL:
        await ws.close(code=1008)
        return

    await manager.connect(ws)
    try:
        while True:
            timestamp = datetime.utcnow()
            satellites = db.query(models.SpaceObject).filter(models.SpaceObject.type == "satellite").all()
            debris = db.query(models.SpaceObject).filter(models.SpaceObject.type == "debris").all()
            objs_msg, alerts_msg, sat_pos, deb_pos = [], [], {}, {}

            for s in satellites:
                p = propagate_tle(s.tle_line1, s.tle_line2, timestamp)
                if p:
                    sat_pos[s.id] = p
                    objs_msg.append({"id": s.id, "name": s.name, "type": "satellite", **p})
            for d in debris:
                p = propagate_tle(d.tle_line1, d.tle_line2, timestamp)
                if p:
                    deb_pos[d.id] = p
                    objs_msg.append({"id": d.id, "name": d.name, "type": "debris", **p})

            for sid, sp in sat_pos.items():
                for did, dp in deb_pos.items():
                    dx = sp["x"] - dp["x"]
                    dy = sp["y"] - dp["y"]
                    dz = sp["z"] - dp["z"]
                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                    if dist < 100:
                        speed = relative_speed(sp, dp)
                        ai = run_ai(dist, speed, 5, 1, 0, 0.2)
                        alerts_msg.append({
                            "sat_id": sid,
                            "debris_id": did,
                            "distance": dist,
                            "speed": speed,
                            "risk_score": ai["risk_score"],
                            "risk_class": ai["risk_class"]
                        })

            await manager.broadcast({"timestamp": timestamp.isoformat() + "Z", "objects": objs_msg, "alerts": alerts_msg})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    finally:
        db.close()
