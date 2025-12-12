from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://orbit_shield_db_user:BuZzucvmlIsffBV32fK3oXd4H8K7Xjw7@dpg-d4tuechr0fns739fdkng-a.oregon-postgres.render.com/orbit_shield_db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
