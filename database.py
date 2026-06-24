"""
database.py
─────────────────────────────────────────────
SQLite database setup using SQLAlchemy.
Stores all live alerts (earthquakes + weather-based).
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///./alerts.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Alert(Base):
    """Table storing all disaster alerts."""
    __tablename__ = "alerts"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String)
    location    = Column(String)
    lat         = Column(Float, nullable=True)
    lng         = Column(Float, nullable=True)
    severity    = Column(String)        # High / Medium / Low
    message     = Column(String)
    source      = Column(String)        # "usgs" or "weather-auto"
    external_id = Column(String, unique=True, nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)


def alert_to_dict(a: Alert):
    """Convert an Alert row into a JSON-friendly dictionary."""
    return {
        "id":        a.id,
        "title":     a.title,
        "location":  a.location,
        "lat":       a.lat,
        "lng":       a.lng,
        "severity":  a.severity,
        "message":   a.message,
        "source":    a.source,
        "createdAt": a.created_at.isoformat() if a.created_at else None,
    }