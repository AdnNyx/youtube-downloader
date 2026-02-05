import axios from "axios";

const BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export const api = axios.create({
  baseURL: `${BASE}/api`,
  timeout: 60000,
});
