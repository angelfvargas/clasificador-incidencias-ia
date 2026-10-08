# Clasificador inteligente de incidencias de software

Proyecto de curso — **Optativa III: Deep Learning y Agentes Inteligentes** (Universidad Libre, Cali, 2026-2)
Docente: Julián René Muñoz Burbano · Estudiante: Angel Farid Agreda Vargas

Aplicación web que recibe tickets de soporte y **sugiere categoría, prioridad y equipo responsable** con un modelo de NLP + aprendizaje supervisado, aplica reglas de negocio deterministas, sigue el ciclo de vida del ticket y mide tanto la operación como la calidad del modelo.

| Tarea | Macro-F1 (prueba) | Baseline |
|---|---|---|
| Categoría (Incident / Request / Problem / Change) | **0,863** | 0,140 |
| Prioridad (high / medium / low) | **0,607** | 0,193 |
| Equipo (10 colas) | **0,563** | 0,043 |

## Arranque rápido (Docker)

```bash
cp .env.example .env        # y cambiar JWT_SECRET y ADMIN_PASSWORD
docker-compose up -d --build
```

- Aplicación: http://localhost:8080 (admin: el `ADMIN_EMAIL` / `ADMIN_PASSWORD` del `.env`)
- API y documentación Swagger: http://localhost:8000/docs
- Datos de demostración (opcional): `ADMIN_PASSWORD=... python scripts/sembrar_demo.py`

Instalación sin Docker, entrenamiento y pruebas: ver [manual técnico](docs/manual_tecnico.md).

## Estructura

```
backend/        API FastAPI (rutas, seguridad, reglas, cliente del modelo)
frontend/       Interfaz React + Vite
ai_service/     src/train.py (entrenamiento) y models/ (modelos versionados + métricas)
data/           raw/ (descarga, no versionado) y processed/test.csv (conjunto de prueba)
tests/          pruebas unitarias, de integración y del modelo (pytest)
scripts/        carga de datos de demostración
docs/           requisitos, arquitectura, datos y modelo, pruebas, ética, manuales
```

## Documentación

1. [Visión y requisitos](docs/01_vision_y_requisitos.md) — problema, historias de usuario, requisitos, IA vs. reglas
2. [Arquitectura](docs/02_arquitectura.md) — diagramas de contexto, componentes, datos, secuencia, pipeline de IA, API
3. [Datos y modelo](docs/03_datos_y_modelo.md) — dataset, partición, baseline, métricas, matrices de confusión, análisis de errores
4. [Pruebas](docs/04_pruebas.md)
5. [Ética y seguridad](docs/05_etica_y_seguridad.md)
6. [Manual de usuario](docs/manual_usuario.md) · [Manual técnico](docs/manual_tecnico.md)
7. Colección de API: [`docs/api.http`](docs/api.http)

## Tecnologías

Python 3.11 · FastAPI · scikit-learn · MongoDB 7 · React 19 + Vite · Docker Compose · pytest · GitHub Actions

## Datos

*Customer Support Tickets* (`Tobi-Bueck/customer-support-tickets`, Hugging Face), licencia CC BY-NC 4.0. Datos sintéticos; uso académico.
