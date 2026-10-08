# 2. Arquitectura y diseño

Los diagramas están en Mermaid: GitHub los dibuja automáticamente al abrir este archivo.

## 2.1 Diagrama de contexto

```mermaid
flowchart LR
    U([Usuario operativo]) -- crea tickets, consulta estado --> S[Clasificador inteligente<br/>de incidencias]
    A([Analista / Admin]) -- gestiona estados, reasigna,<br/>ve métricas --> S
    S -- sugiere categoría,<br/>prioridad y equipo --> U
    D[(Dataset público de tickets<br/>Hugging Face)] -. entrenamiento offline .-> S
```

## 2.2 Diagrama de contenedores / componentes

```mermaid
flowchart LR
    subgraph Navegador
        FE[Frontend React + Vite<br/>servido por nginx :8080]
    end
    subgraph API["Backend FastAPI :8000"]
        direction TB
        R[Rutas REST<br/>main.py]
        SEG[Autenticación y roles<br/>seguridad.py]
        ESQ[Validación<br/>esquemas.py]
        REG[Reglas de negocio<br/>reglas.py]
        IA[Cliente del modelo<br/>ia.py]
    end
    subgraph Servicio_IA["Servicio de IA (offline)"]
        direction TB
        TR[train.py<br/>entrenamiento y evaluación]
        MOD[(Modelos versionados<br/>*.joblib + metricas.json)]
    end
    DB[(MongoDB<br/>usuarios, tickets)]

    FE -- JSON / HTTP + JWT --> R
    R --> SEG
    R --> ESQ
    R --> IA
    R --> REG
    R --> DB
    IA -- carga --> MOD
    TR -- genera --> MOD
```

**Por qué así:** el modelo se carga desde archivos versionados detrás de una sola interfaz (`ia.predecir(texto)`). Para cambiar de modelo basta con reentrenar y reemplazar los archivos: la API, las reglas y la interfaz no cambian. La versión del modelo queda guardada en cada ticket.

## 2.3 Modelo de datos (MongoDB)

```mermaid
erDiagram
    USUARIO ||--o{ TICKET : crea
    TICKET ||--|{ EVENTO_HISTORIAL : contiene
    TICKET ||--|| RESULTADO_IA : guarda

    USUARIO {
        string email PK "único"
        string nombre
        string clave "hash bcrypt"
        string rol "operativo | analista | admin"
        datetime creado
    }
    TICKET {
        ObjectId _id PK
        string asunto
        string descripcion
        string creado_por FK
        string estado "abierto | en_progreso | resuelto | cerrado"
        string categoria "decisión final"
        string prioridad "decisión final"
        string equipo "decisión final"
        int reasignaciones
        datetime creado
        datetime actualizado
        datetime cerrado
    }
    RESULTADO_IA {
        string version_modelo
        object categoria "etiqueta, puntaje, alternativas"
        object prioridad "etiqueta, puntaje, alternativas"
        object equipo "etiqueta, puntaje, alternativas"
        list reglas_aplicadas
    }
    EVENTO_HISTORIAL {
        datetime fecha
        string usuario
        string accion
        string detalle
    }
```

`RESULTADO_IA` y `EVENTO_HISTORIAL` son subdocumentos dentro del ticket (campos `ia` e `historial`). Se guarda **por separado** lo que dijo el modelo y la decisión final, para poder medir después cuántas veces se corrigió al modelo.

## 2.4 Secuencia del caso principal: crear un ticket

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant API as Backend
    participant IA as Servicio IA
    participant RN as Reglas
    participant DB as MongoDB

    U->>FE: Escribe asunto y descripción
    FE->>API: POST /tickets (JWT)
    API->>API: Valida token y esquema
    API->>IA: predecir(texto)
    IA-->>API: categoría, prioridad, equipo + puntajes + versión
    API->>RN: aplicar(predicción, texto)
    RN-->>API: decisión final + reglas aplicadas
    API->>DB: insert ticket (estado abierto, historial)
    DB-->>API: id
    API-->>FE: 201 ticket clasificado
    FE-->>U: Muestra la sugerencia, puntajes y reglas
```

## 2.5 Pipeline de IA

```mermaid
flowchart TB
    A[CSV 20.000 tickets<br/>EN + DE] --> B[Filtrar inglés<br/>asunto + cuerpo<br/>quitar duplicados]
    B --> C[Partición estratificada<br/>70 / 15 / 15<br/>semilla 42]
    C --> D[TF-IDF<br/>unigramas + bigramas]
    D --> E1[Baseline<br/>clase más frecuente]
    D --> E2[Regresión logística]
    D --> E3[SVM lineal]
    E1 & E2 & E3 --> F[Elegir mejor por<br/>Macro-F1 en validación]
    F --> G[Reentrenar con<br/>train + validación]
    G --> H[Evaluar una vez<br/>en test]
    H --> I[(categoria / prioridad / equipo<br/>.joblib + metricas.json)]
```

## 2.6 Ciclo de vida del ticket

```mermaid
stateDiagram-v2
    [*] --> abierto
    abierto --> en_progreso
    abierto --> cerrado
    en_progreso --> resuelto
    en_progreso --> abierto
    resuelto --> cerrado
    resuelto --> abierto: reabrir
    cerrado --> [*]
```

## 2.7 API REST

Documentación interactiva completa: `http://localhost:8000/docs`.

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `/salud` | público | Estado y versión del modelo |
| POST | `/auth/registro` | público | Crea usuario operativo |
| POST | `/auth/login` | público | Devuelve token JWT |
| GET | `/auth/yo` | cualquiera | Datos del usuario actual |
| GET | `/usuarios` | admin | Lista usuarios |
| PATCH | `/usuarios/{email}/rol` | admin | Cambia rol |
| POST | `/clasificar` | cualquiera | Solo predicción, no guarda |
| POST | `/tickets` | cualquiera | Crea y clasifica |
| GET | `/tickets?estado=&equipo=` | cualquiera | Lista (operativo: solo los suyos) |
| GET | `/tickets/{id}` | dueño o gestor | Detalle con historial |
| PATCH | `/tickets/{id}/estado` | analista, admin | Cambia estado (solo transiciones válidas) |
| PATCH | `/tickets/{id}/asignacion` | analista, admin | Reasigna equipo |
| GET | `/metricas` | analista, admin | Métricas de software y del modelo |

**Contrato del servicio de IA** (lo que devuelve `ia.predecir`):

```json
{
  "version_modelo": "v202610082247",
  "categoria": {"etiqueta": "Problem", "puntaje": 0.3686,
                "alternativas": [{"etiqueta": "Change", "puntaje": 0.243}, {"etiqueta": "Incident", "puntaje": 0.197}]},
  "prioridad": {"etiqueta": "low", "puntaje": 0.4516, "alternativas": ["…"]},
  "equipo":    {"etiqueta": "IT Support", "puntaje": 0.129, "alternativas": ["…"]}
}
```

Ejemplo real para *"VPN not connecting…"*. Aquí el puntaje del equipo (0,129) queda por debajo del umbral, así que la regla R2 lo envía a revisión manual: el modelo duda entre IT Support (0,129) y Customer Service (0,126), y el sistema lo deja ver en lugar de esconderlo.


## 2.8 Wireframes (pantallas implementadas)

1. **Ingreso / registro:** correo, clave y botón para cambiar a registro.
2. **Tickets:** tabla con asunto, categoría, prioridad, equipo, estado y fecha; filtro por estado.
3. **Nuevo ticket:** asunto, descripción y, al guardar, la tarjeta *"Lo que sugirió la IA"* con barras de puntaje, alternativas y reglas aplicadas.
4. **Detalle:** datos del ticket, resultado de la IA, panel *Gestionar* (estados y reasignación) e historial.
5. **Dashboard:** indicadores (tickets, lead time, tasa de reasignación), tabla de calidad del modelo y conteos por estado, prioridad, categoría y equipo.

## 2.9 Decisiones técnicas

| Decisión | Alternativa descartada | Motivo |
|---|---|---|
| FastAPI | Flask, Django | Validación con Pydantic y OpenAPI incluidos; sugerido por el enunciado |
| MongoDB | PostgreSQL | El ticket es un documento con subdocumentos (IA, historial); sugerido por el enunciado |
| TF-IDF + SVM lineal | Transformer (BERT) | Supera claramente al baseline, entrena en segundos sin GPU y es fácil de explicar; un transformer queda como trabajo futuro |
| Modelo cargado dentro del proceso de la API | Microservicio aparte | Para un solo modelo pequeño evita latencia de red; la interfaz `ia.py` permite separarlo después |
| React + Vite | Plantillas del servidor | Sugerido por el enunciado; interfaz independiente del backend |
