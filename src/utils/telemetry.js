// src/utils/telemetry.js
// Lightweight, privacy-aware telemetry. No PII beyond coarse event properties.
// Currently logs to console and enqueues to localStorage for later upload.
// Backend endpoint can be added later (e.g., POST /telemetry) without changing callers.

const STORAGE_KEY = "pm_telemetry_queue";

function safeGetQueue() {
  try {
    const txt = localStorage.getItem(STORAGE_KEY);
    if (!txt) return [];
    const arr = JSON.parse(txt);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function safeSetQueue(arr) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(arr).slice(0, 200_000)); // cap size
  } catch {
    // ignore quota errors
  }
}

export function trackEvent(name, props = {}) {
  try {
    const evt = {
      name,
      ts: new Date().toISOString(),
      props: sanitizeProps(props),
      v: 1,
    };
    // Console for immediate feedback in dev
    if (import.meta?.env?.MODE !== "production") {
      // eslint-disable-next-line no-console
      console.debug("[telemetry]", evt);
    }
    // Enqueue for potential later upload
    const q = safeGetQueue();
    q.push(evt);
    if (q.length > 1000) q.shift(); // keep last 1000
    safeSetQueue(q);
  } catch {
    // no-op
  }
}

function sanitizeProps(input) {
  // Drop obviously sensitive keys
  const banned = new Set(["password", "token", "email", "username"]);
  const out = {};
  Object.entries(input || {}).forEach(([k, v]) => {
    if (banned.has(String(k).toLowerCase())) return;
    // Normalize large objects
    if (typeof v === "object" && v !== null) {
      out[k] = JSON.stringify(v).slice(0, 500);
    } else {
      out[k] = v;
    }
  });
  return out;
}

// Optional: expose a flush that callers could invoke from a settings page later
export async function flushTelemetry(uploader) {
  // uploader is an async function that takes an array of events and returns true on success
  const q = safeGetQueue();
  if (!q.length) return true;
  if (typeof uploader !== "function") return false;
  const ok = await uploader(q);
  if (ok) safeSetQueue([]);
  return ok;
}
