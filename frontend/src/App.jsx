import { useEffect, useState } from "react";
import { api, cerrarSesion, guardarSesion, leerSesion } from "./api";

const ESTADOS = { abierto: "Abierto", en_progreso: "En progreso", resuelto: "Resuelto", cerrado: "Cerrado" };
const SIGUIENTES = { abierto: ["en_progreso", "cerrado"], en_progreso: ["resuelto", "abierto"], resuelto: ["cerrado", "abierto"], cerrado: [] };
const EQUIPOS = ["Technical Support", "Product Support", "Customer Service", "IT Support", "Billing and Payments",
  "Returns and Exchanges", "Service Outages and Maintenance", "Sales and Pre-Sales", "Human Resources", "General Inquiry"];
const pct = (x) => `${Math.round(x * 100)}%`;
const fecha = (f) => new Date(f).toLocaleString("es-CO");

function Login({ alEntrar }) {
  const [modo, setModo] = useState("login");
  const [f, setF] = useState({ nombre: "", email: "", clave: "" });
  const [error, setError] = useState("");
  const cambiar = (e) => setF({ ...f, [e.target.name]: e.target.value });

  async function enviar(e) {
    e.preventDefault();
    setError("");
    try {
      if (modo === "registro") await api.registro(f.nombre, f.email, f.clave);
      const r = await api.login(f.email, f.clave);
      guardarSesion({ token: r.access_token, rol: r.rol, email: f.email });
      alEntrar();
    } catch (err) { setError(err.message); }
  }

  return (
    <form className="tarjeta login" onSubmit={enviar}>
      <h1>Clasificador de incidencias</h1>
      <p className="suave">{modo === "login" ? "Ingresa con tu cuenta" : "Crea una cuenta de usuario operativo"}</p>
      {modo === "registro" && <input name="nombre" placeholder="Nombre" value={f.nombre} onChange={cambiar} required />}
      <input name="email" type="email" placeholder="Correo" value={f.email} onChange={cambiar} required />
      <input name="clave" type="password" placeholder="Clave (mín. 8)" value={f.clave} onChange={cambiar} required />
      {error && <p className="error">{error}</p>}
      <button>{modo === "login" ? "Entrar" : "Registrarme"}</button>
      <button type="button" className="enlace" onClick={() => setModo(modo === "login" ? "registro" : "login")}>
        {modo === "login" ? "¿No tienes cuenta? Regístrate" : "Ya tengo cuenta"}
      </button>
    </form>
  );
}

function Puntaje({ titulo, p, final }) {
  return (
    <div className="pred">
      <span className="suave">{titulo}</span>
      <strong>{final}</strong>
      <div className="barra"><div style={{ width: pct(p.puntaje) }} /></div>
      <small className="suave">Modelo: {p.etiqueta} ({pct(p.puntaje)})
        {p.alternativas.length > 0 && <> · otras: {p.alternativas.map((a) => `${a.etiqueta} ${pct(a.puntaje)}`).join(", ")}</>}
      </small>
    </div>
  );
}

function ResultadoIA({ t }) {
  const p = t.ia.prediccion;
  return (
    <div className="tarjeta">
      <h3>Lo que sugirió la IA</h3>
      <div className="preds">
        <Puntaje titulo="Categoría" p={p.categoria} final={t.categoria} />
        <Puntaje titulo="Prioridad" p={p.prioridad} final={t.prioridad} />
        <Puntaje titulo="Equipo" p={p.equipo} final={t.equipo} />
      </div>
      {t.ia.reglas_aplicadas.length > 0 && (
        <ul className="reglas">{t.ia.reglas_aplicadas.map((r) => <li key={r}>{r}</li>)}</ul>
      )}
      <small className="suave">Modelo {p.version_modelo}. El puntaje sirve para comparar opciones; no es una probabilidad exacta.</small>
    </div>
  );
}

function NuevoTicket({ alCrear }) {
  const [asunto, setAsunto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState("");
  const [creado, setCreado] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setError("");
    try {
      const t = await api.crearTicket(asunto, descripcion);
      setCreado(t); setAsunto(""); setDescripcion(""); alCrear();
    } catch (err) { setError(err.message); }
  }

  return (
    <>
      <form className="tarjeta" onSubmit={enviar}>
        <h2>Nuevo ticket</h2>
        <p className="suave">Escribe en inglés: el modelo fue entrenado con tickets en inglés.</p>
        <input placeholder="Asunto" value={asunto} onChange={(e) => setAsunto(e.target.value)} maxLength={200} />
        <textarea placeholder="Describe el problema (mín. 10 caracteres)" rows={5} value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)} required minLength={10} maxLength={5000} />
        {error && <p className="error">{error}</p>}
        <button>Crear y clasificar</button>
      </form>
      {creado && <ResultadoIA t={creado} />}
    </>
  );
}

function Detalle({ id, rol, alCambiar, alCerrar }) {
  const [t, setT] = useState(null);
  const [equipo, setEquipo] = useState("");
  const [comentario, setComentario] = useState("");
  const [error, setError] = useState("");
  const gestor = rol === "admin" || rol === "analista";

  useEffect(() => { api.ticket(id).then(setT).catch((e) => setError(e.message)); }, [id]);

  async function hacer(accion) {
    setError("");
    try { setT(await accion()); setComentario(""); alCambiar(); } catch (e) { setError(e.message); }
  }

  if (!t) return error ? <p className="error">{error}</p> : <p>Cargando…</p>;
  return (
    <div>
      <button className="enlace" onClick={alCerrar}>← Volver</button>
      <div className="tarjeta">
        <h2>{t.asunto || "(sin asunto)"}</h2>
        <p>{t.descripcion}</p>
        <p className="suave">Creado por {t.creado_por} · {fecha(t.creado)} · <span className={`estado ${t.estado}`}>{ESTADOS[t.estado]}</span></p>
      </div>
      <ResultadoIA t={t} />
      {gestor && t.estado !== "cerrado" && (
        <div className="tarjeta">
          <h3>Gestionar</h3>
          <input placeholder="Comentario (opcional)" value={comentario} onChange={(e) => setComentario(e.target.value)} />
          <div className="fila">
            {SIGUIENTES[t.estado].map((e) => (
              <button key={e} onClick={() => hacer(() => api.cambiarEstado(t.id, e, comentario))}>Pasar a {ESTADOS[e]}</button>
            ))}
          </div>
          <div className="fila">
            <select value={equipo} onChange={(e) => setEquipo(e.target.value)}>
              <option value="">Reasignar a otro equipo…</option>
              {EQUIPOS.filter((e) => e !== t.equipo).map((e) => <option key={e}>{e}</option>)}
            </select>
            <button disabled={!equipo} onClick={() => hacer(() => api.reasignar(t.id, equipo, comentario))}>Reasignar</button>
          </div>
          {error && <p className="error">{error}</p>}
        </div>
      )}
      <div className="tarjeta">
        <h3>Historial</h3>
        <ul className="historial">
          {t.historial.map((h, i) => (
            <li key={i}><strong>{h.accion}</strong> — {h.usuario} · {fecha(h.fecha)}{h.detalle && <> · <em>{h.detalle}</em></>}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Lista({ rol, version }) {
  const [tickets, setTickets] = useState([]);
  const [estado, setEstado] = useState("");
  const [abierto, setAbierto] = useState(null);
  const [recarga, setRecarga] = useState(0);

  useEffect(() => { api.tickets(estado).then(setTickets).catch(() => setTickets([])); }, [estado, version, recarga]);

  if (abierto) return <Detalle id={abierto} rol={rol} alCambiar={() => setRecarga((x) => x + 1)} alCerrar={() => setAbierto(null)} />;
  return (
    <div className="tarjeta">
      <div className="fila entre">
        <h2>{rol === "operativo" ? "Mis tickets" : "Tickets"}</h2>
        <select value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todos los estados</option>
          {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      {tickets.length === 0 ? <p className="suave">No hay tickets.</p> : (
        <div className="tabla">
          <table>
            <thead><tr><th>Asunto</th><th>Categoría</th><th>Prioridad</th><th>Equipo</th><th>Estado</th><th>Creado</th></tr></thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} onClick={() => setAbierto(t.id)}>
                  <td>{t.asunto || "(sin asunto)"}</td><td>{t.categoria}</td>
                  <td><span className={`prio ${t.prioridad}`}>{t.prioridad}</span></td><td>{t.equipo}</td>
                  <td><span className={`estado ${t.estado}`}>{ESTADOS[t.estado]}</span></td><td>{fecha(t.creado)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Conteo({ titulo, datos }) {
  const max = Math.max(1, ...Object.values(datos));
  return (
    <div className="tarjeta">
      <h3>{titulo}</h3>
      {Object.entries(datos).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
        <div key={k} className="conteo"><span>{ESTADOS[k] || k}</span><div className="barra"><div style={{ width: pct(v / max) }} /></div><b>{v}</b></div>
      ))}
    </div>
  );
}

function Dashboard() {
  const [m, setM] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.metricas().then(setM).catch((e) => setError(e.message)); }, []);
  if (error) return <p className="error">{error}</p>;
  if (!m) return <p>Cargando…</p>;
  const s = m.software;
  return (
    <>
      <div className="kpis">
        <div className="tarjeta kpi"><span className="suave">Tickets</span><b>{s.total_tickets}</b></div>
        <div className="tarjeta kpi"><span className="suave">Tiempo promedio hasta cerrar</span><b>{s.lead_time_horas_promedio ?? "—"} h</b></div>
        <div className="tarjeta kpi"><span className="suave">Tasa de reasignación</span><b>{s.tasa_reasignacion == null ? "—" : pct(s.tasa_reasignacion)}</b></div>
      </div>
      <div className="tarjeta">
        <h3>Calidad del modelo (conjunto de prueba) · {m.modelo.version}</h3>
        <table>
          <thead><tr><th>Tarea</th><th>Modelo</th><th>Macro-F1</th><th>Exactitud</th></tr></thead>
          <tbody>
            {Object.entries(m.modelo.test).map(([k, v]) => (
              <tr key={k}><td>{k}</td><td>{v.modelo}</td><td>{v.macro_f1.toFixed(3)}</td><td>{pct(v.exactitud)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rejilla">
        <Conteo titulo="Por estado" datos={s.por_estado} />
        <Conteo titulo="Por prioridad" datos={s.por_prioridad} />
        <Conteo titulo="Por categoría" datos={s.por_categoria} />
        <Conteo titulo="Por equipo" datos={s.por_equipo} />
      </div>
    </>
  );
}

export default function App() {
  const [sesion, setSesion] = useState(leerSesion());
  const [vista, setVista] = useState("lista");
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (sesion) api.yo().catch(() => { cerrarSesion(); setSesion(null); });
  }, [sesion]);

  if (!sesion) return <main><Login alEntrar={() => setSesion(leerSesion())} /></main>;
  const gestor = sesion.rol === "admin" || sesion.rol === "analista";
  return (
    <>
      <header>
        <b>Incidencias IA</b>
        <nav>
          <button className={vista === "lista" ? "activo" : ""} onClick={() => setVista("lista")}>Tickets</button>
          <button className={vista === "nuevo" ? "activo" : ""} onClick={() => setVista("nuevo")}>Nuevo</button>
          {gestor && <button className={vista === "dash" ? "activo" : ""} onClick={() => setVista("dash")}>Dashboard</button>}
        </nav>
        <span className="suave">{sesion.email} ({sesion.rol}) <button className="enlace" onClick={() => { cerrarSesion(); setSesion(null); }}>Salir</button></span>
      </header>
      <main>
        {vista === "lista" && <Lista rol={sesion.rol} version={version} />}
        {vista === "nuevo" && <NuevoTicket alCrear={() => setVersion((v) => v + 1)} />}
        {vista === "dash" && gestor && <Dashboard />}
      </main>
    </>
  );
}
