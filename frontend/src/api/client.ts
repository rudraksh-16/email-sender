import axios from "axios";

// In production (served by FastAPI same-origin) all requests are relative.
// In dev mode Vite proxies /api/* to the backend port.
export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg =
      err.response?.data?.error?.message ||
      err.response?.data?.detail ||
      err.message ||
      "Unknown error";
    return Promise.reject(new Error(msg));
  },
);
