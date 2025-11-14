from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# --- This is the connection string for a local SQLite database file ---
# Allow override for testing via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmerdirect.db")

engine = create_engine(
    DATABASE_URL,
    # This line is REQUIRED for SQLite to work with FastAPI
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
