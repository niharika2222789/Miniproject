"""
alerts.py
─────────────────────────────────────────────
Generates LIVE alerts from two real sources and stores them in SQLite:

1. USGS Earthquake API (free, no key) — real earthquakes magnitude >= 4.5
   in the last 24 hours, filtered to near our 5 monitored cities.

2. Open-Meteo weather — if rain probability or temperature crosses a
   threshold for any monitored city, auto-generate a flood/heat alert.

Each alert is saved with a unique external_id so the same event is
never inserted twice.
"""

import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database import SessionLocal, Alert, alert_to_dict
from city_data import CITY_DATA
from weather import fetch_weather

USGS_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"

# ±3 degree bounding box around each city
CITY_BOUNDS = {
    key: (cd['lat'] - 3, cd['lat'] + 3, cd['lon'] - 3, cd['lon'] + 3)
    for key, cd in CITY_DATA.items()
}


def _within_any_city(lat, lon):
    """Return city name if (lat, lon) is near a monitored city, else None."""
    for key, (lat_min, lat_max, lon_min, lon_max) in CITY_BOUNDS.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return CITY_DATA[key]['name']
    return None


async def fetch_earthquake_alerts():
    """Fetch recent M4.5+ earthquakes from USGS near monitored cities."""
    alerts = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(USGS_FEED)
            data = r.json()
    except Exception as e:
        print(f"USGS fetch error: {e}")
        return alerts

    for feature in data.get("features", []):
        try:
            props  = feature["properties"]
            coords = feature["geometry"]["coordinates"]  # [lon, lat, depth]
            lon, lat = coords[0], coords[1]
            mag = props.get("mag", 0)

            city_name = _within_any_city(lat, lon)
            if not city_name:
                continue

            severity = "High" if mag >= 6 else "Medium" if mag >= 5 else "Low"
            alerts.append({
                "title":       f"M{mag} Earthquake near {city_name}",
                "location":    props.get("place", city_name),
                "lat":         lat,
                "lng":         lon,
                "severity":    severity,
                "message":     (f"Magnitude {mag} earthquake detected near {city_name}. "
                                f"Stay alert and follow earthquake safety protocol."),
                "source":      "usgs",
                "external_id": f"usgs-{feature['id']}",
            })
        except Exception as e:
            print(f"USGS parse error: {e}")
            continue

    return alerts


async def fetch_weather_alerts():
    """Check live weather for each city and generate flood/heat alerts if thresholds crossed."""
    alerts = []

    for key, cd in CITY_DATA.items():
        try:
            wx      = await fetch_weather(cd['lat'], cd['lon'])
            current = wx.get("current_weather", {})
            daily   = wx.get("daily", {})

            temp       = current.get("temperature", 0)
            rain_probs = daily.get("precipitation_probability_max", [])
            max_rain   = max(rain_probs[:2]) if rain_probs else 0
            today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            if temp >= 40:
                alerts.append({
                    "title":       f"Extreme Heat Warning — {cd['name']}",
                    "location":    cd['name'],
                    "lat":         cd['lat'],
                    "lng":         cd['lon'],
                    "severity":    "High" if temp >= 43 else "Medium",
                    "message":     (f"Current temperature in {cd['name']} is {round(temp)}°C. "
                                    f"Slum residents should stay hydrated and avoid sun exposure."),
                    "source":      "weather-auto",
                    "external_id": f"heat-{key}-{today}",
                })

            if max_rain >= 70:
                alerts.append({
                    "title":       f"Heavy Rain / Flood Risk — {cd['name']}",
                    "location":    cd['name'],
                    "lat":         cd['lat'],
                    "lng":         cd['lon'],
                    "severity":    "High" if max_rain >= 85 else "Medium",
                    "message":     (f"Rain probability in {cd['name']} is {max_rain}% over the next 2 days. "
                                    f"Residents in low-lying zones should prepare for possible flooding."),
                    "source":      "weather-auto",
                    "external_id": f"flood-{key}-{today}",
                })

        except Exception as e:
            print(f"Weather alert error for {key}: {e}")
            continue

    return alerts


def save_new_alerts(alert_dicts):
    """Insert alerts into SQLite, skipping duplicates. Returns newly inserted alerts."""
    db: Session = SessionLocal()
    newly_inserted = []
    try:
        for a in alert_dicts:
            exists = db.query(Alert).filter(Alert.external_id == a["external_id"]).first()
            if exists:
                continue
            row = Alert(
                title=a["title"], location=a["location"],
                lat=a["lat"], lng=a["lng"],
                severity=a["severity"], message=a["message"],
                source=a["source"], external_id=a["external_id"],
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            newly_inserted.append(alert_to_dict(row))
    finally:
        db.close()
    return newly_inserted


async def refresh_all_alerts():
    """Fetch from all sources and save new alerts. Returns newly inserted alerts."""
    eq_alerts = await fetch_earthquake_alerts()
    wx_alerts = await fetch_weather_alerts()
    return save_new_alerts(eq_alerts + wx_alerts)


def get_all_alerts(limit: int = 50):
    """Return the most recent alerts from the database (newest first)."""
    db: Session = SessionLocal()
    try:
        rows = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
        return [alert_to_dict(r) for r in rows]
    finally:
        db.close()