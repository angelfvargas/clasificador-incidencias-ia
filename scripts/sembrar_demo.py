"""Carga tickets de demostración a través de la API (no toca la base directamente).

Uso: python scripts/sembrar_demo.py [URL_API] [cantidad]
Toma tickets del conjunto de prueba, los crea con un usuario operativo y
simula su ciclo de vida con el admin para que el dashboard tenga datos.
"""
import os
import random
import sys
from pathlib import Path

import httpx
import pandas as pd

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
ROOT = Path(__file__).resolve().parents[1]
random.seed(7)

c = httpx.Client(base_url=API, timeout=30)


def token(email, clave):
    r = c.post("/auth/login", data={"username": email, "password": clave})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


c.post("/auth/registro", json={"nombre": "Usuario Demo", "email": "demo@ejemplo.com", "clave": "demo12345"})
op = token("demo@ejemplo.com", "demo12345")
adm = token(os.getenv("ADMIN_EMAIL", "admin@incidencias.local"), os.environ["ADMIN_PASSWORD"])

d = pd.read_csv(ROOT / "data" / "processed" / "test.csv").sample(N, random_state=7)
aciertos = 0
for _, fila in d.iterrows():
    asunto, _, cuerpo = fila.text.partition(" . ")
    t = c.post("/tickets", json={"asunto": asunto[:200], "descripcion": cuerpo[:5000]}, headers=op).json()
    tid = t["id"]
    # si el equipo sugerido no coincide con el real, el admin lo corrige (reasignación)
    if t["equipo"] != fila.queue:
        c.patch(f"/tickets/{tid}/asignacion", json={"equipo": fila.queue, "comentario": "corrección demo"}, headers=adm)
    else:
        aciertos += 1
    for estado in ["en_progreso", "resuelto", "cerrado"][: random.randint(0, 3)]:
        c.patch(f"/tickets/{tid}/estado", json={"estado": estado}, headers=adm)

print(f"{N} tickets creados; equipo acertado sin reasignar: {aciertos}/{N}")
