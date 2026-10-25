// All communication with the backend lives in this file.
// Every function here matches an endpoint listed in the README "API summary".

// VITE_API_URL is empty on your own computer (the Vite proxy handles /api and /uploads).
// On Vercel it is the address of the Render backend, e.g. https://digi-karigari-api.onrender.com
// Deployed (production) builds fall back to the Render backend below if VITE_API_URL is not set.
const DEPLOYED_BACKEND = "https://digi-karigari.onrender.com";
const API_URL = (import.meta.env.VITE_API_URL || (import.meta.env.PROD ? DEPLOYED_BACKEND : "")).replace(/\/+$/, "");
const BASE = API_URL + "/api";
const ORIGIN = API_URL; // product photos are served by the backend, so they need the same prefix
const TOKEN_KEY = "dk_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) =>
  token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY);

// Backend returns image paths like "/uploads/products/abc.jpg"
export const assetUrl = (path) => (!path ? "" : /^https?:/.test(path) ? path : ORIGIN + path);

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

// FastAPI sends "detail" as text, or as a list of validation problems. Turn both into one sentence.
function formatDetail(detail) {
  if (!detail) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc)
          ? d.loc.filter((x) => !["body", "query", "path"].includes(x)).join(".")
          : "";
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return "Something went wrong. Please try again.";
}

async function request(path, { method = "GET", json, form, params } = {}) {
  let url = BASE + path;
  if (params) {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") sp.append(k, v);
    });
    const qs = sp.toString();
    if (qs) url += "?" + qs;
  }
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let body;
  if (form) {
    body = form; // the browser sets the multipart header itself
  } else if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  }

  let res;
  try {
    res = await fetch(url, { method, headers, body });
  } catch {
    throw new ApiError(
      API_URL
        ? "Cannot reach the server. It may be waking up (free hosting sleeps when idle): wait about a minute and try again."
        : "Cannot reach the server. Is the backend running on port 8000?",
      0
    );
  }

  let data = null;
  let notJson = false;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      notJson = true; // for example an HTML page instead of data
    }
  }
  if (!res.ok) {
    throw new ApiError(notJson ? "The server returned an unexpected error. Please try again." : formatDetail(data && data.detail), res.status);
  }
  if (notJson) {
    // The request "succeeded" but the answer is not data. On a deployed site this almost always means
    // VITE_API_URL is missing, so the browser asked the website itself instead of the backend.
    throw new ApiError(
      API_URL
        ? "The backend sent an unexpected reply. Check that VITE_API_URL is your Render backend address."
        : "Could not find the backend. If this is the deployed site, set VITE_API_URL on Vercel to your Render address and redeploy.",
      res.status
    );
  }
  return data;
}

export const api = {
  // auth
  login: (email, password) => request("/auth/login", { method: "POST", json: { email, password } }),
  register: (payload) => request("/auth/register", { method: "POST", json: payload }),
  me: () => request("/auth/me"),

  // products
  categories: () => request("/products/categories"),
  products: (params) => request("/products", { params }),
  product: (id) => request(`/products/${id}`),
  similar: (id) => request(`/products/${id}/similar`),
  myProducts: () => request("/products/mine"),
  createProduct: (formData) => request("/products", { method: "POST", form: formData }),
  updateProduct: (id, formData) => request(`/products/${id}`, { method: "PUT", form: formData }),
  deleteProduct: (id) => request(`/products/${id}`, { method: "DELETE" }),
  deleteImage: (productId, imageId) =>
    request(`/products/${productId}/images/${imageId}`, { method: "DELETE" }),

  // artisans
  artisans: () => request("/artisans"),
  artisan: (id) => request(`/artisans/${id}`),

  // AI listing assistant
  aiStatus: () => request("/ai/status"),
  aiAssist: (formData) => request("/ai/listing-assist", { method: "POST", form: formData }),

  // orders
  createOrder: (payload) => request("/orders", { method: "POST", json: payload }),
  orders: () => request("/orders"),
  updateItem: (itemId, payload) => request(`/orders/items/${itemId}`, { method: "PATCH", json: payload }),

  // admin
  adminStats: () => request("/admin/stats"),
  adminArtisans: (status) => request("/admin/artisans", { params: { status } }),
  approveArtisan: (id) => request(`/admin/artisans/${id}/approve`, { method: "POST" }),
  rejectArtisan: (id, reason) =>
    request(`/admin/artisans/${id}/reject`, { method: "POST", json: { reason } }),

  // feature status list
  features: () => request("/features"),
};
