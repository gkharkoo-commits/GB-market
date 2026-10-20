/**
 * GB MARKET — Centralized API Client
 */

const API_BASE = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
  ? `${window.location.origin}/api/v1`
  : "http://127.0.0.1:8000/api/v1";

function getAuthToken() {
  return localStorage.getItem("gbm_token");
}

function setAuthToken(token) {
  localStorage.setItem("gbm_token", token);
}

function clearAuthToken() {
  localStorage.removeItem("gbm_token");
  localStorage.removeItem("gbm_user");
}

function getCurrentUser() {
  const user = localStorage.getItem("gbm_user");
  try {
    return user ? JSON.parse(user) : null;
  } catch (e) {
    return null;
  }
}

function setCurrentUser(user) {
  localStorage.setItem("gbm_user", JSON.stringify(user));
}

function getSessionId() {
  let sId = localStorage.getItem("gbm_session_id");
  if (!sId) {
    sId = "guest_" + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem("gbm_session_id", sId);
  }
  return sId;
}

async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  
  const headers = {
    "Content-Type": "application/json",
    "x-session-id": getSessionId(),
    ...(options.headers || {})
  };

  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  try {
    const res = await fetch(url, config);
    const contentType = res.headers.get("content-type");
    let data = null;
    if (contentType && contentType.includes("application/json")) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      const errMsg = (data && data.detail) 
        ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
        : (data && data.message) ? data.message : `Request failed with status ${res.status}`;
      
      // Auto logout on 401 if token was present
      if (res.status === 401 && token) {
        clearAuthToken();
      }
      throw new Error(errMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

async function uploadImageFile(file, folder = "general") {
  const token = getAuthToken();
  if (!token) throw new Error("Please log in to upload files");

  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE}/uploads/image?folder=${encodeURIComponent(folder)}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "x-session-id": getSessionId()
    },
    body: formData
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Image upload failed");
  }
  return data; // { url: "/uploads/..." }
}
