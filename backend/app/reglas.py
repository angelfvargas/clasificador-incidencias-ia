"""Reglas de negocio deterministas. Lo que decide el modelo es una sugerencia;
lo que está aquí es política del negocio y no depende del entrenamiento."""
import re

from . import config

ESTADOS = ("abierto", "en_progreso", "resuelto", "cerrado")
TRANSICIONES = {
    "abierto": {"en_progreso", "cerrado"},
    "en_progreso": {"resuelto", "abierto"},
    "resuelto": {"cerrado", "abierto"},
    "cerrado": set(),
}
EQUIPO_REVISION = "Revisión manual"
PALABRAS_CRITICAS = re.compile(
    r"\b(outage|down|breach|hacked|ransomware|data loss|security incident|not working at all)\b", re.I)


def puede_pasar(actual, nuevo):
    return nuevo in TRANSICIONES.get(actual, set())


def aplicar(prediccion, texto):
    """Devuelve la decisión final y qué reglas se aplicaron (trazabilidad)."""
    reglas = []
    prioridad = prediccion["prioridad"]["etiqueta"]
    if PALABRAS_CRITICAS.search(texto) and prioridad != "high":
        prioridad = "high"
        reglas.append("R1: texto con señal crítica eleva la prioridad a high")

    equipo = prediccion["equipo"]["etiqueta"]
    if prediccion["equipo"]["puntaje"] < config.UMBRAL_EQUIPO:
        equipo = EQUIPO_REVISION
        reglas.append(f"R2: puntaje del equipo < {config.UMBRAL_EQUIPO}, se envía a revisión manual")

    return {"categoria": prediccion["categoria"]["etiqueta"], "prioridad": prioridad,
            "equipo": equipo, "reglas_aplicadas": reglas}
