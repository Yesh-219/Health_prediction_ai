/**
 * API base: empty string uses Vite dev proxy (/api → FastAPI).
 * For production build + separate hosting: VITE_API_URL=http://localhost:8000
 */
const base = import.meta.env.VITE_API_URL || '';

export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}
