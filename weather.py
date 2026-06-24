"""
weather.py
─────────────────────────────────────────────
Fetches live weather from Open-Meteo (free, no API key)
and converts weather codes into readable labels.
"""

import httpx


def wc_label(wc):
    """Convert Open-Meteo weather code into a readable label."""
    if wc == 0:  return 'Clear sky'
    if wc <= 2:  return 'Partly cloudy'
    if wc <= 3:  return 'Overcast'
    if wc <= 48: return 'Foggy'
    if wc <= 57: return 'Drizzle'
    if wc <= 67: return 'Rainy'
    if wc <= 77: return 'Snowy'
    if wc <= 82: return 'Rain showers'
    if wc <= 99: return 'Thunderstorm'
    return 'Cloudy'


async def fetch_weather(lat, lon):
    """Fetch current + 5-day forecast for given coordinates."""
    url = (
        f'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}'
        f'&current_weather=true'
        f'&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max'
        f'&timezone=Asia/Kolkata&forecast_days=5'
    )
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        return r.json()


def build_weather_context(wx, city_name):
    """Convert raw weather JSON into a readable text summary (used by AI assistant)."""
    try:
        cw = wx.get('current_weather', {})
        d  = wx.get('daily', {})
        lines = [
            f'Current in {city_name}: {round(cw.get("temperature", 0))}°C, '
            f'{wc_label(cw.get("weathercode", 0))}, Wind {cw.get("windspeed", 0)} km/h',
            '5-Day Forecast:'
        ]
        for i in range(min(5, len(d.get('time', [])))):
            lines.append(
                f'  {d["time"][i]}: '
                f'{round(d["temperature_2m_max"][i])}°C max / '
                f'{round(d["temperature_2m_min"][i])}°C min, '
                f'{wc_label(d["weathercode"][i])}, '
                f'Rain chance: {d["precipitation_probability_max"][i]}%'
            )
        return '\n'.join(lines)
    except Exception as e:
        return f'Weather unavailable: {e}'