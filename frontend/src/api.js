const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return handle(res);
}

export async function sendMessage(sessionId, message) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return handle(res);
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}
