# 🛰️ OrbitShield

**OrbitShield** is a full‑stack space situational awareness (SSA) web application that visualizes satellites and space debris in real time, predicts close approaches, and highlights potential collision risks using orbital mechanics and AI‑assisted risk scoring.

Built for hackathons and demos, OrbitShield combines **FastAPI**, **WebSockets**, **SGP4/Skyfield**, and **Three.js** into an interactive 3D experience.

---

## 🚀 Features

* 🌍 **Real‑time 3D Earth visualization** (Three.js)
* 🛰️ **Live satellite & debris tracking** using TLE data
* 🔄 **WebSocket streaming** for continuous position updates
* ⚠️ **Collision risk classification** (LOW / MEDIUM / HIGH)
* 🤖 **AI fallback model** for collision probability estimation
* 🔐 **Login & dashboard flow** (session‑based)
* ☁️ **Deployable backend & frontend** (Render + Vercel)

---

## 🧱 Tech Stack

### Frontend

* HTML, CSS, JavaScript
* **Three.js** (3D rendering)
* WebSockets (real‑time updates)

### Backend

* **FastAPI** (Python)
* WebSockets
* SGP4 / Skyfield (orbital propagation)
* SQLAlchemy (database ORM)
* Joblib (AI model loading)

### Data

* TLEs from CelesTrak (with offline fallback)
* Satellite & debris metadata

---

## 📂 Project Structure

```
project-root/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── collision_ai_model.pkl
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── style.css
│   ├── app.js
│   └── assets/
│
├── .env
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/orbit-shield.git
cd orbit-shield
```

---

### 2️⃣ Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn app:app --reload
```

Backend will start at: `http://127.0.0.1:8000`

---

### 3️⃣ Frontend Setup

Simply open:

```text
frontend/index.html
```

in your browser **OR** deploy it via Vercel.

---

## 🔌 API Overview

| Endpoint        | Method | Description                          |
| --------------- | ------ | ------------------------------------ |
| `/objects`      | GET    | Current satellite & debris positions |
| `/ws/positions` | WS     | Live orbital updates                 |
| `/login`        | POST   | User authentication                  |
| `/dashboard`    | GET    | Protected dashboard view             |

---

## 🧠 Collision Risk Logic

* Uses orbital distance & velocity vectors
* Predicts conjunctions within time windows
* AI model provides probabilistic risk scoring
* Color‑coded alerts:

  * 🟢 LOW
  * 🟡 MEDIUM
  * 🔴 HIGH

---

## 🌐 Deployment

### Backend (Render)

* Root directory: `backend`
* Start command:

```bash
uvicorn app:app --host 0.0.0.0 --port 10000
```

### Frontend (Vercel)

* Root directory: `frontend`
* Framework: **Other / Static**

---

## 🔐 Environment Variables

Create a `.env` file in `backend/`:

```env
DATABASE_URL=your_db_url
ALLOWED_ORIGINS=*
AI_MODEL_PATH=collision_ai_model.pkl
```

---

## 🧪 Demo Mode

If live TLE download fails, OrbitShield automatically switches to **fallback TLE data**, ensuring uninterrupted demos.

---

## 📌 Use Cases

* Hackathons & demos
* Space safety awareness
* Visualization of orbital congestion
* Educational SSA tools

---

## 🧑‍🚀 Team

Built with 💙 during hackathons by a student team passionate about **space, safety, and software**.

---

## 📄 License

This project is open‑source and free to use for **educational and non‑commercial purposes**.

---

✨ *OrbitShield — because space deserves traffic control too.*
