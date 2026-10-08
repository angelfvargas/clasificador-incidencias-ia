# Manual técnico

## Requisitos
- Docker 20+ y docker-compose (opción recomendada), **o**
- Python 3.11, Node.js 22 y MongoDB 7.

## Opción A: Docker
```bash
cp .env.example .env              # editar JWT_SECRET (≥ 32 caracteres) y ADMIN_PASSWORD
docker-compose up -d --build      # levanta mongo, api (:8000) y web (:8080)
docker-compose logs -f api        # ver logs con tiempos por petición
docker-compose down               # detener (agregar -v para borrar la base)
```

## Opción B: local
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
docker run -d --name incidencias-mongo -p 27017:27017 mongo:7    # o un Mongo instalado
cd backend && ADMIN_PASSWORD=... ../.venv/bin/uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev                          # http://localhost:5173
```

## Variables de entorno
| Variable | Por defecto | Uso |
|---|---|---|
| `MONGO_URL` | `mongodb://localhost:27017` | Conexión a MongoDB |
| `MONGO_DB` | `incidencias` | Nombre de la base |
| `JWT_SECRET` | (solo desarrollo) | Firma de tokens. **Cambiar** |
| `JWT_HORAS` | `8` | Vigencia del token |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | — | Se crea este admin al arrancar si no existe |
| `UMBRAL_EQUIPO` | `0.20` | Puntaje mínimo para asignar equipo sin revisión manual |
| `MODELS_DIR` | `ai_service/models` | Carpeta de los modelos |
| `VITE_API_URL` (frontend) | `http://localhost:8000` | URL de la API |

## Reentrenar el modelo
```bash
.venv/bin/python - <<'PY'
from huggingface_hub import hf_hub_download; import shutil
p = hf_hub_download("Tobi-Bueck/customer-support-tickets", "dataset-tickets-multi-lang-4-20k.csv", repo_type="dataset")
shutil.copy(p, "data/raw/tickets_multilang_20k.csv")
PY
.venv/bin/python ai_service/src/train.py
```
Genera `ai_service/models/{categoria,prioridad,equipo}.joblib`, `metricas.json` (con versión, métricas por clase y matrices de confusión) y `data/processed/test.csv`. Después hay que reiniciar la API (o reconstruir la imagen con Docker).

## Pruebas
```bash
.venv/bin/python -m pytest -v
```
GitHub Actions ejecuta las pruebas y compila el frontend en cada push.

## Dónde está cada cosa
| Archivo | Responsabilidad |
|---|---|
| `backend/app/main.py` | Rutas REST, middleware de tiempos y errores, métricas |
| `backend/app/seguridad.py` | Hash de claves, JWT, control por roles |
| `backend/app/esquemas.py` | Validación de entradas |
| `backend/app/reglas.py` | Reglas R1/R2 y transiciones de estado |
| `backend/app/ia.py` | Carga de modelos y predicción con puntajes |
| `ai_service/src/train.py` | Partición, baseline, comparación, entrenamiento final, métricas |
| `frontend/src/App.jsx` | Pantallas |
| `frontend/src/api.js` | Cliente HTTP y sesión |
