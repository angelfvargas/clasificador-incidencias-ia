import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "incidencias")
JWT_SECRET = os.getenv("JWT_SECRET", "solo-desarrollo-cambiar-en-produccion-0000")
JWT_HORAS = int(os.getenv("JWT_HORAS", "8"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", ROOT / "ai_service" / "models"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@incidencias.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
# por debajo de este puntaje el equipo sugerido no se asigna solo: va a revisión humana
UMBRAL_EQUIPO = float(os.getenv("UMBRAL_EQUIPO", "0.20"))
