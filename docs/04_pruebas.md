# 4. Pruebas y calidad

Ejecutar todas: `.venv/bin/python -m pytest -v` → **22 pruebas, todas pasan**.
Se ejecutan también en GitHub Actions en cada `push` (`.github/workflows/ci.yml`), junto con la compilación del frontend.

## 4.1 Pruebas unitarias — reglas de negocio (`tests/test_reglas.py`)

No dependen del modelo: prueban la política del negocio de forma aislada.

| Prueba | Tipo de caso | Qué verifica |
|---|---|---|
| `test_sin_reglas_respeta_al_modelo` | normal | Sin señales especiales, la decisión final es la del modelo |
| `test_palabra_critica_sube_prioridad` | normal | R1: "server is down" sube la prioridad a high |
| `test_palabra_critica_no_cambia_si_ya_es_high` | límite | R1 no se registra si ya era high |
| `test_palabra_dentro_de_otra_no_dispara` | límite | "download" contiene "down" pero no activa R1 |
| `test_equipo_con_poco_puntaje_va_a_revision` | normal | R2: puntaje bajo el umbral → Revisión manual |
| `test_umbral_exacto_no_va_a_revision` | límite | Puntaje igual al umbral se asigna normal |
| `test_transiciones_validas_e_invalidas` | normal / inválido | Ciclo de vida: permitidas, prohibidas y estado inexistente |

## 4.2 Pruebas de integración — API (`tests/test_api.py`)

Usan la API real con el modelo real y una base MongoDB simulada en memoria (`mongomock`).

| Prueba | Qué verifica | HU |
|---|---|---|
| `test_salud` | La API responde con la versión del modelo | — |
| `test_registro_duplicado` | Correo repetido (incluso en mayúsculas) → 409 | HU-01 |
| `test_registro_invalido` | Nombre corto, correo inválido, clave corta → 422 | HU-01 |
| `test_login_clave_mala` | Clave incorrecta → 401 | HU-02 |
| `test_sin_token_no_entra` | Sin token o con token falso → 401 | RNF-01 |
| `test_clasificar_no_guarda` | `/clasificar` predice pero no guarda; puntajes entre 0 y 1 | HU-14 |
| `test_descripcion_muy_corta` | Descripción < 10 caracteres → 422 | HU-03 |
| `test_flujo_completo` | Crear → clasificar → operativo no puede cambiar estado (403) → no se salta estados (422) → reasignar → en progreso → resuelto → cerrado → no reasignar cerrado → métricas | HU-03 a HU-11 |
| `test_operativo_solo_ve_sus_tickets` | Listado y detalle de tickets ajenos protegidos | HU-12 |
| `test_ticket_inexistente` | Id mal formado o inexistente → 404 | — |
| `test_cambio_de_rol` | Solo admin cambia roles; rol inválido → 422 | HU-13 |

## 4.3 Pruebas del modelo (`tests/test_modelo.py`)

| Prueba | Qué verifica |
|---|---|
| `test_supera_minimo_y_es_reproducible[...]` | Para cada tarea, recalcula el Macro-F1 sobre el conjunto de prueba con el modelo guardado: debe superar un mínimo (0,75 / 0,45 / 0,45) y coincidir con lo registrado en `metricas.json` |
| `test_supera_al_baseline` | Cada modelo elegido supera al baseline por más de 0,20 de Macro-F1 en validación |

## 4.4 Pruebas de sistema y aceptación (manuales, con Docker)

Realizadas con `docker-compose up -d --build` y el navegador en `http://localhost:8080`:

| # | Paso | Resultado esperado | Resultado |
|---|---|---|---|
| A1 | Registrar usuario nuevo e iniciar sesión | Entra y ve "Mis tickets" vacío | ✔ |
| A2 | Crear ticket "Website down…" | Prioridad high por R1 y tarjeta con reglas aplicadas | ✔ |
| A3 | Crear ticket de cobro doble | Equipo Billing and Payments | ✔ |
| A4 | Como admin abrir un ticket y pasarlo a En progreso | Estado cambia y aparece en el historial | ✔ |
| A5 | Reasignar a otro equipo | Contador de reasignación y evento en historial | ✔ |
| A6 | Abrir Dashboard con 40 tickets de demostración | KPIs, tabla de calidad del modelo y conteos | ✔ |
| A7 | Ingresar como operativo y buscar Dashboard | La opción no aparece; la API responde 403 | ✔ |

## 4.5 Seguridad y rendimiento básico

- Claves con bcrypt; nunca se devuelven en la API (`/usuarios` y `/auth/yo` las excluyen).
- Token JWT firmado con un secreto que vive en `.env` (fuera del repositorio) y vence en 8 h.
- Entradas validadas con Pydantic: longitudes máximas para evitar textos gigantes.
- Tiempo de respuesta de `/clasificar` medido con la cabecera `X-Tiempo-ms`: unos **5 ms** por petición en el equipo de desarrollo.

## 4.6 Defectos encontrados durante las pruebas

| Defecto | Cómo se detectó | Corrección |
|---|---|---|
| Las fechas se mostraban 5 horas adelantadas | Prueba manual: hora UTC leída como hora local | `MongoClient(tz_aware=True)` para que las fechas salgan con zona horaria |
| 92 % de tickets terminaban en revisión manual | Carga de 40 tickets de demostración | Se midió el umbral sobre el conjunto de prueba y se bajó de 0,35 a 0,20 (sección 3.9) |
| Pantalla en blanco al entrar como operativo después de un admin | Prueba de aceptación A7 | La vista vuelve a "Tickets" en cada inicio de sesión |
| La primera clasificación tardaba 1,5 s | Log de tiempos (`X-Tiempo-ms`) | Los modelos se cargan al arrancar la API |
