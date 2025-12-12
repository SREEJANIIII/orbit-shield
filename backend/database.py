# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# load local .env when running locally
load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./orbitshield.db"
)

# create engine, allow SQLite's special arg only when using sqlite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Ensure models are imported when create_all runs (avoid missing table definitions)
# If your models are in the same package, importing them here helps ensure metadata is populated.
try:
    # import models  # uncomment if relative imports cause issues; ensure no circular import
    pass
except Exception:
    pass

# Create tables (idempotent) — safe for both local & Render
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
