"""Cliente del componente de IA: carga los modelos versionados y predice."""
import json
from functools import lru_cache

import joblib
import numpy as np

from . import config

TAREAS = ("categoria", "prioridad", "equipo")


@lru_cache
def _modelos():
    return {t: joblib.load(config.MODELS_DIR / f"{t}.joblib") for t in TAREAS}


@lru_cache
def version_modelo():
    return json.loads((config.MODELS_DIR / "metricas.json").read_text())["version"]


def _puntajes(modelo, texto):
    # LinearSVC no da probabilidades: se normalizan los márgenes con softmax.
    # Sirve para ordenar alternativas, no es una probabilidad calibrada.
    m = modelo.decision_function([texto])[0]
    e = np.exp(m - m.max())
    p = e / e.sum()
    return sorted(zip(modelo.classes_, p.round(4).tolist()), key=lambda x: -x[1])


def predecir(texto):
    salida = {"version_modelo": version_modelo()}
    for tarea, modelo in _modelos().items():
        ranking = _puntajes(modelo, texto)
        salida[tarea] = {"etiqueta": ranking[0][0], "puntaje": ranking[0][1],
                         "alternativas": [{"etiqueta": e, "puntaje": p} for e, p in ranking[1:3]]}
    return salida
