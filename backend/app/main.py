import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from . import config, ia, reglas
from .db import get_db
from .esquemas import CambioEstado, CambioRol, Reasignacion, Registro, TextoTicket
from .seguridad import crear_token, hash_clave, requiere, usuario_actual, verificar_clave

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("incidencias")

GESTORES = ("admin", "analista")


def ahora():
    return datetime.now(timezone.utc)


def crear_admin():
    if config.ADMIN_PASSWORD and not get_db().usuarios.find_one({"email": config.ADMIN_EMAIL}):
        get_db().usuarios.insert_one({"nombre": "Administrador", "email": config.ADMIN_EMAIL,
                                      "clave": hash_clave(config.ADMIN_PASSWORD), "rol": "admin", "creado": ahora()})
        log.info("Administrador inicial creado: %s", config.ADMIN_EMAIL)


@asynccontextmanager
async def ciclo_de_vida(_app):
    crear_admin()
    ia.predecir("precarga")  # carga los modelos al arrancar para que la primera petición no tarde
    yield


app = FastAPI(title="Clasificador inteligente de incidencias", version="1.0.0", lifespan=ciclo_de_vida,
              description="Recibe tickets de soporte, sugiere categoría, prioridad y equipo, y sigue su ciclo de vida.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def medir_tiempo(request: Request, call_next):
    inicio = time.perf_counter()
    try:
        resp = await call_next(request)
    except Exception:
        log.exception("Error no controlado en %s %s", request.method, request.url.path)
        raise
    ms = (time.perf_counter() - inicio) * 1000
    resp.headers["X-Tiempo-ms"] = f"{ms:.1f}"
    log.info("%s %s %s %.1fms", request.method, request.url.path, resp.status_code, ms)
    return resp


def serializar(t):
    t["id"] = str(t.pop("_id"))
    return t


def buscar_ticket(ticket_id):
    try:
        t = get_db().tickets.find_one({"_id": ObjectId(ticket_id)})
    except InvalidId:
        t = None
    if not t:
        raise HTTPException(404, "Ticket no encontrado")
    return t


# ---------- salud ----------

@app.get("/salud")
def salud():
    return {"estado": "ok", "version_modelo": ia.version_modelo()}


# ---------- autenticación ----------

@app.post("/auth/registro", status_code=201)
def registro(datos: Registro):
    try:
        get_db().usuarios.insert_one({"nombre": datos.nombre, "email": datos.email.lower(),
                                      "clave": hash_clave(datos.clave), "rol": "operativo", "creado": ahora()})
    except DuplicateKeyError:
        raise HTTPException(409, "Ese correo ya está registrado")
    return {"email": datos.email.lower(), "rol": "operativo"}


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    u = get_db().usuarios.find_one({"email": form.username.lower()})
    if not u or not verificar_clave(form.password, u["clave"]):
        raise HTTPException(401, "Correo o clave incorrectos")
    return {"access_token": crear_token(u["email"], u["rol"]), "token_type": "bearer", "rol": u["rol"]}


@app.get("/auth/yo")
def yo(u=Depends(usuario_actual)):
    return u


@app.get("/usuarios")
def listar_usuarios(_=Depends(requiere("admin"))):
    return list(get_db().usuarios.find({}, {"_id": 0, "clave": 0}))


@app.patch("/usuarios/{email}/rol")
def cambiar_rol(email: str, datos: CambioRol, _=Depends(requiere("admin"))):
    r = get_db().usuarios.update_one({"email": email.lower()}, {"$set": {"rol": datos.rol}})
    if not r.matched_count:
        raise HTTPException(404, "Usuario no encontrado")
    return {"email": email.lower(), "rol": datos.rol}


# ---------- IA ----------

@app.post("/clasificar")
def clasificar(datos: TextoTicket, _=Depends(usuario_actual)):
    """Solo inferencia: no guarda nada. Útil para probar el modelo."""
    texto = f"{datos.asunto} . {datos.descripcion}"
    pred = ia.predecir(texto)
    return {"prediccion": pred, "decision": reglas.aplicar(pred, texto)}


# ---------- tickets ----------

@app.post("/tickets", status_code=201)
def crear_ticket(datos: TextoTicket, u=Depends(usuario_actual)):
    texto = f"{datos.asunto} . {datos.descripcion}"
    pred = ia.predecir(texto)
    decision = reglas.aplicar(pred, texto)
    t = {
        "asunto": datos.asunto, "descripcion": datos.descripcion, "creado_por": u["email"],
        "estado": "abierto", "creado": ahora(), "actualizado": ahora(), "cerrado": None,
        "categoria": decision["categoria"], "prioridad": decision["prioridad"], "equipo": decision["equipo"],
        "ia": {"prediccion": pred, "reglas_aplicadas": decision["reglas_aplicadas"]},
        "reasignaciones": 0,
        "historial": [{"fecha": ahora(), "usuario": u["email"], "accion": "creado",
                       "detalle": f"Clasificado con modelo {pred['version_modelo']}"}],
    }
    t["_id"] = get_db().tickets.insert_one(t).inserted_id
    return serializar(t)


@app.get("/tickets")
def listar_tickets(estado: str | None = None, equipo: str | None = None, u=Depends(usuario_actual)):
    filtro = {} if u["rol"] in GESTORES else {"creado_por": u["email"]}
    if estado:
        filtro["estado"] = estado
    if equipo:
        filtro["equipo"] = equipo
    return [serializar(t) for t in get_db().tickets.find(filtro, {"historial": 0}).sort("creado", -1).limit(200)]


@app.get("/tickets/{ticket_id}")
def ver_ticket(ticket_id: str, u=Depends(usuario_actual)):
    t = buscar_ticket(ticket_id)
    if u["rol"] not in GESTORES and t["creado_por"] != u["email"]:
        raise HTTPException(403, "No tiene permiso para ver este ticket")
    return serializar(t)


@app.patch("/tickets/{ticket_id}/estado")
def cambiar_estado(ticket_id: str, datos: CambioEstado, u=Depends(requiere(*GESTORES))):
    t = buscar_ticket(ticket_id)
    if not reglas.puede_pasar(t["estado"], datos.estado):
        raise HTTPException(422, f"No se puede pasar de '{t['estado']}' a '{datos.estado}'")
    cambios = {"estado": datos.estado, "actualizado": ahora(),
               "cerrado": ahora() if datos.estado == "cerrado" else None}
    evento = {"fecha": ahora(), "usuario": u["email"], "accion": f"estado: {t['estado']} → {datos.estado}",
              "detalle": datos.comentario}
    get_db().tickets.update_one({"_id": t["_id"]}, {"$set": cambios, "$push": {"historial": evento}})
    return serializar(buscar_ticket(ticket_id))


@app.patch("/tickets/{ticket_id}/asignacion")
def reasignar(ticket_id: str, datos: Reasignacion, u=Depends(requiere(*GESTORES))):
    t = buscar_ticket(ticket_id)
    if t["estado"] == "cerrado":
        raise HTTPException(422, "Un ticket cerrado no se puede reasignar")
    evento = {"fecha": ahora(), "usuario": u["email"], "accion": f"equipo: {t['equipo']} → {datos.equipo}",
              "detalle": datos.comentario}
    get_db().tickets.update_one({"_id": t["_id"]}, {"$set": {"equipo": datos.equipo, "actualizado": ahora()},
                                                    "$inc": {"reasignaciones": 1}, "$push": {"historial": evento}})
    return serializar(buscar_ticket(ticket_id))


# ---------- métricas ----------

@app.get("/metricas")
def metricas(_=Depends(requiere(*GESTORES))):
    tickets = list(get_db().tickets.find({}, {"historial": 0, "descripcion": 0}))
    total = len(tickets)

    def contar(campo):
        c = {}
        for t in tickets:
            c[t[campo]] = c.get(t[campo], 0) + 1
        return c

    cerrados = [t for t in tickets if t.get("cerrado")]
    horas = [(t["cerrado"] - t["creado"]).total_seconds() / 3600 for t in cerrados]
    reasignados = sum(1 for t in tickets if t.get("reasignaciones", 0) > 0)
    modelo = json.loads((config.MODELS_DIR / "metricas.json").read_text())
    return {
        "software": {
            "total_tickets": total,
            "por_estado": contar("estado"), "por_categoria": contar("categoria"),
            "por_prioridad": contar("prioridad"), "por_equipo": contar("equipo"),
            "lead_time_horas_promedio": round(sum(horas) / len(horas), 2) if horas else None,
            "tasa_reasignacion": round(reasignados / total, 4) if total else None,
        },
        "modelo": {
            "version": modelo["version"],
            "test": {k: {"macro_f1": v["test"]["macro_f1"], "exactitud": v["test"]["exactitud"],
                         "modelo": v["modelo_elegido"]} for k, v in modelo["tareas"].items()},
        },
    }
