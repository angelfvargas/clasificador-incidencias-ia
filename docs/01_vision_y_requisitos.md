# 1. Visión y requisitos

**Proyecto:** Clasificador inteligente de incidencias de software
**Curso:** Optativa III – Deep Learning y Agentes Inteligentes · Docente: Julián René Muñoz Burbano
**Estudiante:** Angel Farid Agreda Vargas · Universidad Libre, Cali · 2026-2

## 1.1 Problema

En una mesa de soporte, cada ticket nuevo tiene que leerlo una persona para decidir **de qué tipo es**, **qué tan urgente es** y **a qué equipo le toca**. Ese triage manual es lento, depende de quién esté de turno y produce reasignaciones: el ticket va a un equipo, no era, y vuelve a la cola. Mientras tanto, el usuario espera.

## 1.2 Visión

Una aplicación web donde el usuario registra su incidencia y el sistema **sugiere de inmediato** categoría, prioridad y equipo responsable, explica qué tan seguro está, y deja que una persona confirme o corrija. Todo cambio queda en el historial del ticket y en las métricas, para poder medir si la IA realmente ayuda.

La IA **apoya** la decisión; no la reemplaza. Cuando el modelo no está seguro, el sistema lo dice y envía el ticket a revisión manual.

## 1.3 Interesados (stakeholders)

| Interesado | Qué necesita |
|---|---|
| Usuario operativo (quien reporta) | Reportar rápido y ver el estado de su ticket |
| Administrador de soporte | Gestionar estados, corregir asignaciones, administrar usuarios |
| Responsable de análisis | Ver métricas del servicio y de la calidad del modelo |
| Equipos de soporte | Recibir solo los tickets que les corresponden |

## 1.4 Alcance

**Incluye:** registro e inicio de sesión con roles; creación de tickets; clasificación automática (categoría, prioridad, equipo); reglas de negocio sobre la sugerencia; seguimiento por estados con historial; reasignación; dashboard de métricas de software y del modelo; API documentada; pruebas automatizadas; despliegue con Docker.

**No incluye:** respuestas automáticas al usuario, notificaciones por correo, adjuntos, integración con herramientas externas (Jira, etc.) ni reentrenamiento automático en producción.

**Restricción:** el modelo se entrenó con tickets en **inglés**; los tickets deben escribirse en inglés.

## 1.5 Actores y roles

| Rol | Puede |
|---|---|
| `operativo` | Registrarse, crear tickets, ver **solo sus** tickets, probar el clasificador |
| `analista` | Todo lo anterior sobre **todos** los tickets, cambiar estados, reasignar, ver dashboard |
| `admin` | Todo lo del analista + listar usuarios y cambiar roles |

## 1.6 Historias de usuario (backlog priorizado)

Prioridad MoSCoW: **M** = debe, **S** = debería, **C** = podría.

| # | Historia | Prioridad | Criterios de aceptación |
|---|---|---|---|
| HU-01 | Como **usuario** quiero registrarme con nombre, correo y clave para poder reportar incidencias. | M | Correo válido y único (si existe → error 409). Clave mínimo 8 caracteres. Queda con rol `operativo`. |
| HU-02 | Como **usuario** quiero iniciar sesión para acceder a mis tickets. | M | Credenciales correctas → token válido por 8 h. Incorrectas → error 401 sin decir cuál campo falló. |
| HU-03 | Como **usuario operativo** quiero crear un ticket con asunto y descripción para reportar un problema. | M | Descripción de 10 a 5000 caracteres. El ticket queda en estado `abierto` y guardado en la base de datos. |
| HU-04 | Como **usuario operativo** quiero que el sistema clasifique mi ticket automáticamente para que llegue al equipo correcto sin esperar triage. | M | Al crear el ticket se guardan categoría, prioridad y equipo sugeridos, con su puntaje y la versión del modelo. Respuesta en < 1 s. |
| HU-05 | Como **administrador** quiero que un ticket con señales críticas (caída, brecha de seguridad…) quede en prioridad alta aunque el modelo diga otra cosa. | M | Si el texto contiene una palabra crítica, la prioridad final es `high` y se registra la regla R1 aplicada. |
| HU-06 | Como **administrador** quiero que los tickets donde el modelo duda del equipo vayan a revisión manual. | M | Si el puntaje del equipo es menor al umbral (0,20), el equipo queda en "Revisión manual" y se registra la regla R2. |
| HU-07 | Como **analista** quiero cambiar el estado de un ticket para reflejar el avance. | M | Solo transiciones válidas: abierto→en progreso/cerrado; en progreso→resuelto/abierto; resuelto→cerrado/abierto. Una transición inválida devuelve 422. El operativo no puede (403). |
| HU-08 | Como **analista** quiero reasignar un ticket a otro equipo cuando la sugerencia es incorrecta. | M | Se actualiza el equipo, se cuenta la reasignación y queda en el historial. Un ticket cerrado no se reasigna. |
| HU-09 | Como **usuario** quiero ver el historial de un ticket para saber quién hizo qué y cuándo. | S | Cada creación, cambio de estado y reasignación aparece con fecha, usuario y comentario. |
| HU-10 | Como **responsable de análisis** quiero un dashboard con métricas del servicio para saber cómo va la operación. | S | Muestra total de tickets, conteos por estado, categoría, prioridad y equipo, tiempo promedio hasta cerrar (lead time) y tasa de reasignación. |
| HU-11 | Como **responsable de análisis** quiero ver la calidad del modelo en el mismo dashboard para saber cuánto confiar en él. | S | Muestra versión del modelo y Macro-F1 y exactitud por tarea, medidos en el conjunto de prueba. |
| HU-12 | Como **usuario operativo** quiero ver solo mis tickets para proteger la información de otros usuarios. | M | El listado y el detalle de tickets ajenos no son accesibles para el rol operativo (403). |
| HU-13 | Como **administrador** quiero cambiar el rol de un usuario para dar permisos de analista. | C | Solo el admin puede; rol inválido → 422. |
| HU-14 | Como **usuario** quiero probar el clasificador sin crear un ticket. | C | `POST /clasificar` devuelve la predicción y no guarda nada. |

## 1.7 Requisitos no funcionales

| # | Requisito | Cómo se cumple / verifica |
|---|---|---|
| RNF-01 Seguridad | Autenticación con JWT y control por roles; claves con bcrypt. | `seguridad.py`; pruebas de 401/403. |
| RNF-02 Validación | Toda entrada se valida con esquemas (longitudes, formato de correo, estados permitidos). | Pydantic; pruebas de 422. |
| RNF-03 Rendimiento | Clasificación y creación de ticket en menos de 1 s. | Cabecera `X-Tiempo-ms` y log de cada petición. |
| RNF-04 Trazabilidad | Cada predicción guarda versión del modelo, puntajes y reglas aplicadas; cada cambio queda en el historial. | Campo `ia` e `historial` del ticket. |
| RNF-05 Registro de errores | Los errores no controlados se registran con traza. | Middleware en `main.py`. |
| RNF-06 Reproducibilidad | Semilla fija, partición documentada, métricas guardadas en `metricas.json` y verificadas por prueba automática. | `train.py`, `test_modelo.py`. |
| RNF-07 Despliegue | El sistema completo arranca con un comando. | `docker-compose up -d --build`. |
| RNF-08 Documentación de API | OpenAPI/Swagger automático. | `http://localhost:8000/docs`. |
| RNF-09 Protección de datos | El operativo no ve tickets ajenos; las claves nunca se devuelven; secretos en `.env` fuera del repositorio. | Pruebas HU-12; `.gitignore`. |
| RNF-10 Mantenibilidad | Capas separadas (frontend, API, reglas, servicio de IA, datos); el modelo se puede reemplazar sin tocar la API. | Ver arquitectura. |

## 1.8 Qué decide la IA y qué deciden las reglas

El enunciado pide justificar esta separación.

| Decisión | Quién | Por qué |
|---|---|---|
| Categoría, prioridad y equipo **sugeridos** | Modelo de IA | Dependen del significado del texto; escribir reglas a mano para miles de redacciones no escala. |
| Prioridad mínima ante señales críticas (R1) | Regla determinista | Es política del negocio: una caída o una brecha **nunca** debe quedar en prioridad baja. No se le delega al modelo. |
| Enviar a revisión manual si el modelo duda (R2) | Regla determinista | Controla el riesgo: el umbral lo fija el negocio según cuánto error tolera. |
| Transiciones de estado permitidas | Regla determinista | Es el ciclo de vida del proceso; debe ser predecible y auditable. |
| Permisos por rol | Regla determinista | Seguridad; nunca puede depender de una predicción. |
| Corrección final del equipo | Persona (analista/admin) | Supervisión humana; además alimenta la métrica de reasignación. |

## 1.9 Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El modelo asigna mal el equipo (Macro-F1 0,55) | Reasignaciones, demora | Regla R2 + reasignación manual + métrica de tasa de reasignación |
| Tickets en otro idioma | Predicción poco confiable | Aviso en la interfaz; trabajo futuro: entrenar con alemán/español |
| Datos del dataset no representan la operación real | El rendimiento real puede ser menor | Documentado en el análisis de datos; reentrenar con datos propios |
| Uso indebido de datos personales en los tickets | Privacidad | Roles, acceso solo a tickets propios, secretos fuera del repositorio |
