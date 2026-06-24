/* ─────────────────────────────────────────────
   live_alerts.js
   Polls the FastAPI backend every 15s for live alerts
   (USGS earthquakes + weather-based flood/heat alerts)
   and updates:
     - #toast / #toastTitle / #toastMeta  (dashboard rotating toast)
     - #alertCard / #alertTitle / #alertMeta (splash page banner)
   No Socket.IO needed — plain polling via fetch().
───────────────────────────────────────────── */

const API_BASE = 'http://127.0.0.1:8000';
const POLL_INTERVAL = 15000; // 15 seconds

let liveAlerts = [];
let toastIdx = 0;

function severityColor(sev) {
  if (sev === 'High') return '#D32F2F';
  if (sev === 'Medium') return '#F57F17';
  return '#43A047';
}

function timeAgo(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ago`;
}

async function fetchLiveAlerts() {
  try {
    const res = await fetch(`${API_BASE}/api/alerts?limit=20`);
    if (!res.ok) return;
    const data = await res.json();
    liveAlerts = data;
    updateToast();
    updateSplashCard();
    if (typeof window.onLiveAlertsUpdated === 'function') {
      window.onLiveAlertsUpdated(liveAlerts);
    }
  } catch (e) {
    console.warn('live_alerts: fetch failed', e);
  }
}

/* ── Dashboard rotating toast (#toast) ── */
function updateToast() {
  const toast = document.getElementById('toast');
  if (!toast || liveAlerts.length === 0) return;

  const a = liveAlerts[toastIdx % liveAlerts.length];
  const titleEl = document.getElementById('toastTitle');
  const metaEl  = document.getElementById('toastMeta');
  if (titleEl) titleEl.textContent = a.title;
  if (metaEl)  metaEl.textContent  = `${a.location} · ${timeAgo(a.createdAt)} · ${a.severity} severity`;

  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4500);
  toastIdx++;
}

/* ── Splash page banner (#alertCard) ── */
function updateSplashCard() {
  const card = document.getElementById('alertCard');
  if (!card || liveAlerts.length === 0) return;

  const a = liveAlerts[0]; // most recent
  const titleEl = document.getElementById('alertTitle');
  const metaEl  = document.getElementById('alertMeta');
  if (titleEl) titleEl.textContent = a.title;
  if (metaEl)  metaEl.textContent  = `${a.location} · ${timeAgo(a.createdAt)} · ${a.message}`;
}

// Initial fetch + periodic polling
fetchLiveAlerts();
setInterval(fetchLiveAlerts, POLL_INTERVAL);

// Rotate toast independently every 7s using cached alerts
setInterval(() => {
  if (liveAlerts.length > 0) updateToast();
}, 7000);