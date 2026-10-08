"""Pruebas unitarias de las reglas de negocio (no dependen del modelo)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import config, reglas  # noqa: E402


def pred(prioridad="low", equipo="IT Support", puntaje_equipo=0.9):
    return {"categoria": {"etiqueta": "Incident", "puntaje": 0.8},
            "prioridad": {"etiqueta": prioridad, "puntaje": 0.6},
            "equipo": {"etiqueta": equipo, "puntaje": puntaje_equipo}}


def test_sin_reglas_respeta_al_modelo():
    d = reglas.aplicar(pred(), "My printer prints blank pages")
    assert d == {"categoria": "Incident", "prioridad": "low", "equipo": "IT Support", "reglas_aplicadas": []}


def test_palabra_critica_sube_prioridad():
    d = reglas.aplicar(pred("low"), "The whole server is down since morning")
    assert d["prioridad"] == "high" and d["reglas_aplicadas"][0].startswith("R1")


def test_palabra_critica_no_cambia_si_ya_es_high():
    assert reglas.aplicar(pred("high"), "Service outage")["reglas_aplicadas"] == []


def test_palabra_dentro_de_otra_no_dispara():
    # "download" contiene "down" pero no es una caída
    assert reglas.aplicar(pred("low"), "How do I download the invoice?")["prioridad"] == "low"


def test_equipo_con_poco_puntaje_va_a_revision():
    d = reglas.aplicar(pred(puntaje_equipo=config.UMBRAL_EQUIPO - 0.01), "texto cualquiera")
    assert d["equipo"] == reglas.EQUIPO_REVISION


def test_umbral_exacto_no_va_a_revision():
    assert reglas.aplicar(pred(puntaje_equipo=config.UMBRAL_EQUIPO), "x")["equipo"] == "IT Support"


def test_transiciones_validas_e_invalidas():
    assert reglas.puede_pasar("abierto", "en_progreso")
    assert reglas.puede_pasar("resuelto", "abierto")
    assert not reglas.puede_pasar("abierto", "resuelto")
    assert not reglas.puede_pasar("cerrado", "abierto")
    assert not reglas.puede_pasar("inventado", "abierto")
