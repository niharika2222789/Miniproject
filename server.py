"""
main.py
─────────────────────────────────────────────
FastAPI application — ties everything together.

- AI assistant uses Gemini (if GEMINI_API_KEY set) with a smart rule-based
  fallback otherwise.
- Live alerts are fetched periodically in the background and stored in
  SQLite. The frontend polls GET /api/alerts every ~15s — no socket needed.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio

from city_data import CITY_DATA
from weather import fetch_weather, build_weather_context
from ai_assistant import build_prompt, call_gemini_full, server_smart_fallback, stream_text, GEMINI_KEY
from alerts import refresh_all_alerts, get_all_alerts
from database import Base, engine

load_dotenv()

# Ensure DB tables exist on startup
Base.metadata.create_all(bind=engine)

ALERT_REFRESH_SECONDS = 60


async def _alert_background_loop():
    """Background task: periodically refresh alerts from USGS + weather."""
    while True:
        try:
            new_alerts = await refresh_all_alerts()
            if new_alerts:
                print(f"[alerts] {len(new_alerts)} new alert(s) saved")
        except Exception as e:
            print(f"[alerts] background refresh error: {e}")
        await asyncio.sleep(ALERT_REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run one refresh immediately on startup, then keep looping
    try:
        initial = await refresh_all_alerts()
        print(f"[alerts] startup refresh — {len(initial)} alert(s) saved")
    except Exception as e:
        print(f"[alerts] startup refresh error: {e}")
    task = asyncio.create_task(_alert_background_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['*'],
)


@app.get('/')
async def root():
    provider = 'gemini' if GEMINI_KEY else 'rule-based fallback'
    return {'status': 'Backend is running', 'provider': provider}


@app.get('/api/stats')
async def stats():
    provider = 'gemini' if GEMINI_KEY else 'rule-based fallback'
    alerts = get_all_alerts(limit=100)
    high   = sum(1 for a in alerts if a['severity'] == 'High')
    medium = sum(1 for a in alerts if a['severity'] == 'Medium')
    low    = sum(1 for a in alerts if a['severity'] == 'Low')
    latest = alerts[0]['title'] if alerts else 'No active alerts'
    return {
        'activeEmergencies': len(alerts),
        'high': high,
        'medium': medium,
        'low': low,
        'provider': provider,
        'latestAlert': latest,
    }


@app.get('/api/weather')
async def weather(city: str = 'hyderabad'):
    cd = CITY_DATA.get(city, CITY_DATA['hyderabad'])
    try:
        return await fetch_weather(cd['lat'], cd['lon'])
    except Exception as e:
        return {'error': str(e)}


@app.get('/api/alerts')
async def get_alerts_route(limit: int = 50):
    """Return live alerts stored in SQLite (newest first)."""
    return get_all_alerts(limit=limit)


@app.post('/api/alerts/refresh')
async def force_refresh_alerts():
    """Manually trigger an alert refresh (useful for testing/demo)."""
    new_alerts = await refresh_all_alerts()
    return {'newAlerts': new_alerts, 'count': len(new_alerts)}


@app.post('/api/chat')
async def chat(request: Request):
    try:
        body     = await request.json()
        question = body.get('question', '').strip()
        city_key = body.get('city', 'hyderabad').lower()

        if not question:
            return JSONResponse({'error': 'No question provided'})

        cd = CITY_DATA.get(city_key, CITY_DATA['hyderabad'])

        # Fetch live weather
        weather_ctx = 'Weather data unavailable.'
        try:
            wx = await fetch_weather(cd['lat'], cd['lon'])
            weather_ctx = build_weather_context(wx, cd['name'])
        except Exception as e:
            print(f'Weather fetch error: {e}')

        sse_headers = {
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
        }

        # Try Gemini first
        if GEMINI_KEY:
            print(f'Calling Gemini for: {question[:60]}')
            prompt = build_prompt(question, city_key, weather_ctx)
            text = await call_gemini_full(prompt)
            if text:
                return StreamingResponse(
                    stream_text(text),
                    media_type='text/event-stream',
                    headers=sse_headers
                )
            print('Gemini failed — using smart fallback')

        # Smart fallback
        print(f'Using smart fallback for: {question[:60]}')
        fallback = server_smart_fallback(question, city_key, weather_ctx)
        return StreamingResponse(
            stream_text(fallback),
            media_type='text/event-stream',
            headers=sse_headers
        )

    except Exception as e:
        print(f'Chat endpoint error: {e}')
        err = 'Server error. Please try again. For emergencies call: 112'
        return StreamingResponse(
            stream_text(err),
            media_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'Access-Control-Allow-Origin': '*'}
        )