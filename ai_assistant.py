"""
ai_assistant.py
─────────────────────────────────────────────
AI chat logic:
1. Builds a prompt using city data + live weather
2. Tries Gemini API
3. Falls back to a rule-based smart fallback if Gemini fails or no key set
4. Streams the response word-by-word (SSE)
"""

import httpx, os, json, asyncio, re
from city_data import CITY_DATA

GEMINI_KEY = os.getenv('GEMINI_API_KEY', '')


def build_prompt(question, city_key, weather_ctx):
    """Build the full prompt sent to the AI model, including city-specific data."""
    cd = CITY_DATA.get(city_key, CITY_DATA['hyderabad'])
    city_name   = cd['name']
    high_zones  = '\n'.join(f'  - {z}' for z in cd['zones']['high'])
    med_zones   = '\n'.join(f'  - {z}' for z in cd['zones']['medium'])
    low_zones   = '\n'.join(f'  - {z}' for z in cd['zones']['low'])
    shelters    = '\n'.join(
        f'  - {s["name"]}: {s["address"]} | Capacity: {s["capacity"]} | Call: {s["contact"]}'
        for s in cd['shelters']
    )
    return (
        'You are an expert AI disaster preparedness assistant for India.\n'
        'You help slum residents understand their disaster risks clearly.\n\n'
        f'CITY: {city_name}\n\n'
        f'LIVE WEATHER:\n{weather_ctx}\n\n'
        f'HIGH RISK ZONES ({len(cd["zones"]["high"])}):\n{high_zones}\n\n'
        f'MEDIUM RISK ZONES ({len(cd["zones"]["medium"])}):\n{med_zones}\n\n'
        f'LOW RISK ZONES ({len(cd["zones"]["low"])}):\n{low_zones}\n\n'
        f'EMERGENCY SHELTERS:\n{shelters}\n\n'
        f'EMERGENCY CONTACTS: Ambulance 108, Police 100, Fire 101, NDMA 1078, '
        f'{cd["emergency"]["local"]}, {cd["emergency"]["helpline"]}\n\n'
        f'QUESTION: {question}\n\n'
        'Give a detailed, specific, helpful answer using the data above. '
        'Name actual zones and shelters. Use bullet points. Max 250 words.'
    )


async def call_gemini_full(prompt):
    """Call Google Gemini API. Returns text or None on failure."""
    url = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        'gemini-2.0-flash:generateContent?key=' + GEMINI_KEY
    )
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            url,
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'maxOutputTokens': 600, 'temperature': 0.7}
            }
        )
        data = r.json()
        if r.status_code != 200:
            print(f'Gemini ERROR: {json.dumps(data)[:300]}')
            return None
        try:
            return data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            print(f'Gemini parse error: {e}')
            return None


async def stream_text(text: str):
    """Yield text word-chunks as Server-Sent Events (creates typing effect)."""
    words = text.split(' ')
    chunk_size = 5
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        if i + chunk_size < len(words):
            chunk += ' '
        yield 'data: ' + json.dumps({'text': chunk}) + '\n\n'
        await asyncio.sleep(0.018)
    yield 'data: [DONE]\n\n'


def server_smart_fallback(question, city_key, weather_ctx):
    """Rule-based fallback answer used when Gemini fails or no key is set."""
    cd   = CITY_DATA.get(city_key, CITY_DATA['hyderabad'])
    city = cd['name']
    q    = question.lower()
    hz   = cd['zones']['high']
    mz   = cd['zones']['medium']
    lz   = cd['zones']['low']
    sh   = cd['shelters']
    em   = cd['emergency']

    temp_str = ''
    try:
        m = re.search(r'(\d+)°C,', weather_ctx)
        if m:
            temp_str = f"{m.group(1)}°C"
    except Exception:
        pass

    rain_pct = 0
    try:
        vals = re.findall(r'Rain chance: (\d+)%', weather_ctx)
        if vals:
            rain_pct = max(int(v) for v in vals)
    except Exception:
        pass

    if any(w in q for w in ['shelter', 'evacuate', 'evacuation', 'safe place', 'refuge', 'where to go', 'relief']):
        lines = [f"🏠 Emergency Shelters & Evacuation — {city}\n"]
        for i, s in enumerate(sh, 1):
            lines.append(f"{i}. {s['name']}")
            lines.append(f"   📍 {s['address']}")
            lines.append(f"   👥 Capacity: {s['capacity']}")
            lines.append(f"   📞 {s['contact']}\n")
        lines.append(f"📞 Quick Helplines: Ambulance 108 | Police 100 | NDMA 1078 | {em['helpline']}")
        lines += ["\n🚶 Evacuation Steps:",
                  "1. Call NDMA 1078 immediately",
                  "2. Take documents, medicine, water & 3-day food supply",
                  "3. Go to the nearest shelter above",
                  "4. Do NOT return until authorities give all-clear"]
        return '\n'.join(lines)

    if any(w in q for w in ['high risk', 'high-risk', 'dangerous', 'most dangerous', 'eight high', '8 high', 'which zone', 'risk zone', 'all zone', 'list zone']):
        lines = [f"🔴 High-Risk Zones — {city} ({len(hz)} zones)\n",
                 "These areas have the highest vulnerability to floods, fires and structural collapse:\n"]
        for i, z in enumerate(hz, 1):
            lines.append(f"{i}. {z}")
        lines.append(f"\n🟠 Medium-Risk Zones ({len(mz)}):\n" + '\n'.join(f"{i+1}. {z}" for i, z in enumerate(mz)))
        lines.append(f"\n🟢 Low-Risk Zones ({len(lz)}):\n" + '\n'.join(f"{i+1}. {z}" for i, z in enumerate(lz)))
        lines.append(f"\n⚠️ Residents of high-risk zones should register at the nearest shelter.")
        lines.append(f"📞 NDMA: 1078 | {em['local']}")
        return '\n'.join(lines)

    if any(w in q for w in ['flood', 'rain', 'water', 'waterlog', 'nala', 'inundation']):
        risk_level = 'HIGH ⚠️' if rain_pct >= 60 else 'MODERATE' if rain_pct >= 30 else 'LOW ✅'
        lines = [f"🌧️ Flood Risk Assessment — {city}: {risk_level}\n"]
        if temp_str:
            lines.append(f"Current weather: {temp_str}, Rain chance this week: {rain_pct}%\n")
        lines.append("Most flood-vulnerable zones:")
        for z in hz[:5]:
            lines.append(f"  • {z}")
        lines += ["\n🚨 What to do if flooding starts:",
                  "  1. Move to higher ground IMMEDIATELY — do not wait",
                  "  2. Never walk through moving floodwater",
                  "  3. Turn off electricity at the main switch",
                  "  4. Go to the nearest shelter:"]
        lines.append(f"     → {sh[0]['name']}, {sh[0]['address']} | 📞 {sh[0]['contact']}")
        lines.append(f"     → {sh[1]['name']}, {sh[1]['address']} | 📞 {sh[1]['contact']}")
        lines.append(f"\n📞 NDMA: 1078 | Ambulance: 108 | {em['helpline']}")
        return '\n'.join(lines)

    if any(w in q for w in ['safe', 'outside', 'go out', 'travel', 'today']):
        safe_level = 'CAUTION ADVISED' if rain_pct >= 40 or (temp_str and int(re.search(r'\d+', temp_str).group()) >= 38) else 'GENERALLY SAFE'
        lines = [f"🛡️ Safety Assessment — {city}: {safe_level}\n"]
        if temp_str:
            lines.append(f"• Current temperature: {temp_str}")
        if rain_pct:
            lines.append(f"• Rain probability this week: {rain_pct}%")
        lines.append(f"\nAvoid these HIGH-RISK areas today:")
        for z in hz[:5]:
            lines.append(f"  🔴 {z}")
        lines.append(f"\nRelatively SAFER areas:")
        for z in lz[:3]:
            lines.append(f"  🟢 {z}")
        lines += ["\n💡 Tips:",
                  "  • Carry your phone fully charged",
                  "  • Keep NDMA helpline 1078 saved",
                  "  • Avoid nala and riverbank areas after rain",
                  "\n📞 Emergency: Police 100 | Ambulance 108 | NDMA 1078"]
        return '\n'.join(lines)

    if any(w in q for w in ['heat', 'temperature', 'hot', 'sun', 'heatwave', 'temp']):
        lines = [f"🌡️ Heat Advisory — {city}\n"]
        if temp_str:
            lines.append(f"• Current temperature: {temp_str}")
        lines += ["• Dense slum areas face the highest heat risk due to metal roofing and lack of shade",
                  f"• Most affected: {hz[0].split(' — ')[0]}, {hz[1].split(' — ')[0]}",
                  "\n⚠️ Heat Safety Rules:",
                  "  1. Stay indoors between 12 noon and 4pm",
                  "  2. Drink water every 30 minutes — do NOT wait for thirst",
                  "  3. Wear light, loose cotton clothing",
                  "  4. Check on elderly neighbours daily",
                  "  5. If someone collapses: move to shade, apply wet cloth, call 108",
                  f"\n📞 Ambulance: 108 | NDMA: 1078 | {em['local']}"]
        return '\n'.join(lines)

    if any(w in q for w in ['earthquake', 'tremor', 'shake', 'quake', 'seismic']):
        lines = [f"🏚️ Earthquake Preparedness — {city}\n",
                 "Most vulnerable structures are in high-risk zones:"]
        for z in hz[:4]:
            lines.append(f"  • {z}")
        lines += ["\n⚡ During an earthquake:",
                  "  1. DROP to the ground immediately",
                  "  2. Take COVER under a sturdy table or interior wall",
                  "  3. HOLD ON until all shaking stops",
                  "  4. Stay away from windows, outer walls and heavy objects",
                  "\nAfter shaking stops:",
                  "  • Check yourself and others for injuries",
                  "  • Evacuate carefully — watch for fallen debris",
                  f"  • Go to: {sh[0]['name']} — {sh[0]['address']}",
                  "\n📞 Emergency: 112 | NDMA: 1078 | Fire: 101"]
        return '\n'.join(lines)

    if any(w in q for w in ['hospital', 'medical', 'ambulance', 'doctor', 'injury', 'hurt', 'first aid']):
        lines = [f"🏥 Medical Emergency — {city}\n",
                 "📞 CALL IMMEDIATELY:",
                 "  • Ambulance: 108 (free, 24/7 — dispatches nearest unit)",
                 "  • National Emergency: 112",
                 "  • NDMA Helpline: 1078",
                 f"  • {em['local']}",
                 "\n🩹 While waiting for ambulance:",
                 "  • Keep the person calm and lying down",
                 "  • Do NOT move if spinal injury suspected",
                 "  • Apply pressure on bleeding wounds",
                 "  • Give water only if person is conscious",
                 f"\n🏠 Nearest shelter with first aid:",
                 f"  {sh[0]['name']} — {sh[0]['address']} | 📞 {sh[0]['contact']}"]
        return '\n'.join(lines)

    if any(w in q for w in ['contact', 'number', 'helpline', 'call', 'phone']):
        lines = [f"📞 Emergency Contacts — {city}\n",
                 "  🚑 Ambulance: 108 (free, 24/7)",
                 "  🚓 Police: 100",
                 "  🔥 Fire Brigade: 101",
                 "  🆘 National Emergency: 112",
                 "  🏠 NDMA Helpline: 1078",
                 f"  🏙️ {em['local']}",
                 f"  📋 {em['helpline']}",
                 "\n💡 Save ALL these numbers in your phone right now.",
                 "In a real disaster there is no time to search for numbers."]
        return '\n'.join(lines)

    if any(w in q for w in ['cyclone', 'storm', 'wind', 'hurricane', 'typhoon']):
        lines = [f"🌀 Cyclone & Storm Safety — {city}\n",
                 "Coastal and low-lying zones most at risk:"]
        for z in hz[:4]:
            lines.append(f"  • {z}")
        lines += ["\n⚠️ Before a cyclone:",
                  "  • Stock water, food, medicine for 3 days",
                  "  • Secure loose objects outside your home",
                  f"  • Know your nearest cyclone shelter:",
                  f"    → {sh[-1]['name']}, {sh[-1]['address']} | 📞 {sh[-1]['contact']}",
                  "\nDuring a cyclone:",
                  "  • Stay indoors, away from windows",
                  "  • Do NOT go outside during the eye of the storm",
                  f"\n📞 NDMA: 1078 | {em['helpline']}"]
        return '\n'.join(lines)

    # Default greeting
    lines = [f"Hello! I'm your Disaster Preparedness Assistant for {city}.\n",
             "I have detailed information about:\n",
             f"  🔴 {len(hz)} High-risk zones by name and hazard type",
             f"  🟠 {len(mz)} Medium-risk zones",
             f"  🟢 {len(lz)} Low-risk zones",
             f"  🏠 {len(sh)} Shelters with addresses and contact numbers",
             "  📞 All emergency helplines",
             "  🌧️ Live weather and flood/heat risk",
             "\nTry asking:",
             '  • "Where is the nearest shelter?"',
             '  • "What are the eight high risk zones?"',
             '  • "What should I do during a flood?"',
             '  • "Is it safe to go outside today?"',
             '  • "List all emergency contacts"',
             f"\n📞 Quick help: Ambulance 108 | Police 100 | NDMA 1078"]
    return '\n'.join(lines)