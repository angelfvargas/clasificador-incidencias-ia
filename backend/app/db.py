from pymongo import MongoClient

from . import config

_db = None


def get_db():
    global _db
    if _db is None:
        _db = MongoClient(config.MONGO_URL, tz_aware=True)[config.MONGO_DB]
        _db.usuarios.create_index("email", unique=True)
    return _db


def set_db(db):
    """Permite inyectar otra base (p. ej. mongomock en las pruebas)."""
    global _db
    _db = db
