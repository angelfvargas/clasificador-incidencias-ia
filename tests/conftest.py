import sys
from pathlib import Path

import mongomock
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import db  # noqa: E402
from app.main import app  # noqa: E402
from app.seguridad import hash_clave  # noqa: E402


@pytest.fixture
def base():
    m = mongomock.MongoClient(tz_aware=True).db
    m.usuarios.create_index("email", unique=True)
    db.set_db(m)
    yield m
    db.set_db(None)


@pytest.fixture
def cliente(base):
    return TestClient(app)


def _token(cliente, email, clave):
    r = cliente.post("/auth/login", data={"username": email, "password": clave})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def operativo(cliente):
    cliente.post("/auth/registro", json={"nombre": "Ana", "email": "ana@test.co", "clave": "clave12345"})
    return _token(cliente, "ana@test.co", "clave12345")


@pytest.fixture
def admin(cliente, base):
    base.usuarios.insert_one({"nombre": "Admin", "email": "admin@test.co", "clave": hash_clave("admin12345"), "rol": "admin"})
    return _token(cliente, "admin@test.co", "admin12345")
