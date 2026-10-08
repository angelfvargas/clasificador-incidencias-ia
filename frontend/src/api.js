const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function guardarSesion(s) { localStorage.setItem("sesion", JSON.stringify(s)); }
export function leerSesion() {
  try { return JSON.parse(localStorage.getItem("sesion")); } catch { return null; }
}
export function cerrarSesion() { localStorage.removeItem("sesion"); }

async function pedir(ruta, { metodo = "GET", cuerpo, form } = {}) {
  const s = leerSesion();
  const headers = {};
  if (s?.token) headers.Authorization = `Bearer ${s.token}`;
  let body;
  if (form) body = new URLSearchParams(form);
  else if (cuerpo) { headers["Content-Type"] = "application/json"; body = JSON.stringify(cuerpo); }
  const r = await fetch(BASE + ruta, { method: metodo, headers, body });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) {
    const d = datos.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => e.msg).join(". ") : d || `Error ${r.status}`);
  }
  return datos;
}

export const api = {
  login: (email, clave) => pedir("/auth/login", { metodo: "POST", form: { username: email, password: clave } }),
  registro: (nombre, email, clave) => pedir("/auth/registro", { metodo: "POST", cuerpo: { nombre, email, clave } }),
  yo: () => pedir("/auth/yo"),
  clasificar: (asunto, descripcion) => pedir("/clasificar", { metodo: "POST", cuerpo: { asunto, descripcion } }),
  crearTicket: (asunto, descripcion) => pedir("/tickets", { metodo: "POST", cuerpo: { asunto, descripcion } }),
  tickets: (estado) => pedir("/tickets" + (estado ? `?estado=${estado}` : "")),
  ticket: (id) => pedir(`/tickets/${id}`),
  cambiarEstado: (id, estado, comentario) => pedir(`/tickets/${id}/estado`, { metodo: "PATCH", cuerpo: { estado, comentario } }),
  reasignar: (id, equipo, comentario) => pedir(`/tickets/${id}/asignacion`, { metodo: "PATCH", cuerpo: { equipo, comentario } }),
  metricas: () => pedir("/metricas"),
};
