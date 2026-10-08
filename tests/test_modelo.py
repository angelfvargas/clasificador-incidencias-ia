"""Evaluación del modelo con el conjunto de prueba (nunca usado para entrenar)."""
import json
from pathlib import Path

import joblib
import pandas as pd
import pytest
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[1]
MODELOS = ROOT / "ai_service" / "models"
TEST = ROOT / "data" / "processed" / "test.csv"
MINIMOS = {"categoria": ("type", 0.75), "prioridad": ("priority", 0.45), "equipo": ("queue", 0.45)}


@pytest.mark.skipif(not TEST.exists(), reason="falta data/processed/test.csv (correr train.py)")
@pytest.mark.parametrize("tarea", MINIMOS)
def test_supera_minimo_y_es_reproducible(tarea):
    col, minimo = MINIMOS[tarea]
    d = pd.read_csv(TEST)
    f1 = f1_score(d[col], joblib.load(MODELOS / f"{tarea}.joblib").predict(d.text), average="macro")
    assert f1 >= minimo
    registrado = json.loads((MODELOS / "metricas.json").read_text())["tareas"][tarea]["test"]["macro_f1"]
    assert abs(f1 - registrado) < 1e-3


def test_supera_al_baseline():
    m = json.loads((MODELOS / "metricas.json").read_text())
    for t in m["tareas"].values():
        v = t["macro_f1_validacion"]
        assert v[t["modelo_elegido"]] > v["baseline_mas_frecuente"] + 0.2
