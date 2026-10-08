# 3. Datos, modelo y análisis de errores

## 3.1 Origen y licencia de los datos

| | |
|---|---|
| Dataset | *Customer Support Tickets* — `Tobi-Bueck/customer-support-tickets` (Hugging Face) |
| Archivo | `dataset-tickets-multi-lang-4-20k.csv` (20.000 tickets) |
| Licencia | CC BY-NC 4.0: uso no comercial con atribución. Este proyecto es académico. |
| Naturaleza | Tickets **sintéticos**: generados para simular una mesa de soporte, no son de clientes reales. |
| Cómo obtenerlo | Se descarga con `huggingface_hub` a `data/raw/` (no se sube al repositorio por tamaño y licencia). El conjunto de prueba usado está en `data/processed/test.csv`. |

## 3.2 Variables

| Columna | Uso en el proyecto |
|---|---|
| `subject`, `body` | Entrada: se unen como `asunto . cuerpo` |
| `type` | Objetivo **categoría**: Incident, Request, Problem, Change |
| `priority` | Objetivo **prioridad**: high, medium, low |
| `queue` | Objetivo **equipo**: 10 colas (Technical Support, Product Support, Customer Service, IT Support, Billing and Payments, Returns and Exchanges, Service Outages and Maintenance, Sales and Pre-Sales, Human Resources, General Inquiry) |
| `language` | Filtro: solo `en` |
| `answer`, `tag_1..8` | **No se usan.** La respuesta y las etiquetas se escriben después de atender el ticket; usarlas sería *fuga de información* (el modelo vería datos que no existen al momento de crear el ticket). |

## 3.3 Calidad y limpieza

- 20.000 filas: 11.923 en inglés y 8.077 en alemán. Se usa solo inglés: 11.923.
- `subject` vacío en 1.032 tickets en inglés (8,7 %). Se reemplaza por texto vacío; el cuerpo sigue sirviendo.
- `body` vacío en 1 ticket: se conserva porque tiene asunto. Solo se descartaría un ticket sin asunto ni cuerpo (no hay ninguno).
- Duplicados exactos del texto: ninguno en inglés. Igual se aplica `drop_duplicates` antes de partir, para que el mismo texto no quede en entrenamiento y en prueba a la vez.

## 3.4 Desbalance y sesgos

| Objetivo | Clase más grande | Clase más pequeña |
|---|---|---|
| Categoría | Incident 38,9 % | Change 10,8 % |
| Prioridad | medium 41,5 % | low 20,1 % |
| Equipo | Technical Support 28,6 % | General Inquiry 1,4 % (29 tickets en prueba) |

Riesgos de sesgo:
- **Idioma:** solo inglés. Un ticket en español se clasifica peor.
- **Datos sintéticos:** la redacción es más limpia y uniforme que la de usuarios reales. El rendimiento en producción puede ser menor.
- **Clases pequeñas:** con pocos ejemplos (General Inquiry, Human Resources) las métricas por clase son inestables.
- Se usa `class_weight="balanced"` para que el modelo no ignore las clases pequeñas, y se reporta **Macro-F1**, que pesa igual cada clase.

## 3.5 Partición

Estratificada por categoría, semilla **42**:

| Conjunto | Tickets | Uso |
|---|---|---|
| Entrenamiento | 8.346 (70 %) | Ajustar los modelos |
| Validación | 1.788 (15 %) | Elegir el mejor modelo |
| Prueba | 1.789 (15 %) | Se usa **una sola vez**, al final, para reportar |

El modelo elegido se reentrena con entrenamiento + validación y se evalúa en prueba. Ningún texto de prueba se usa para entrenar ni para elegir.

## 3.6 Baseline y modelos comparados

Representación del texto: **TF-IDF** con unigramas y bigramas (`min_df=2`, `sublinear_tf`).

| Modelo | Categoría | Prioridad | Equipo |
|---|---|---|---|
| Baseline: siempre la clase más frecuente | 0,140 | 0,193 | 0,043 |
| TF-IDF + Regresión logística | 0,824 | 0,556 | 0,442 |
| **TF-IDF + SVM lineal** (elegido) | **0,843** | **0,573** | **0,552** |

*Macro-F1 en validación.* El SVM gana en las tres tareas.

Hiperparámetros, semilla y modelo serializado: `ai_service/src/train.py` y `ai_service/models/*.joblib`. Versión: `v202610082247`.

## 3.7 Resultados en prueba

| Tarea | Macro-F1 | Exactitud | Baseline (Macro-F1) |
|---|---|---|---|
| Categoría | **0,863** | 85,9 % | 0,140 |
| Prioridad | **0,607** | 62,2 % | 0,193 |
| Equipo | **0,563** | 56,6 % | 0,043 |

La prueba automática `tests/test_modelo.py` vuelve a calcular estas cifras con el modelo guardado y falla si no coinciden con `metricas.json` (reproducibilidad).

### Categoría por clase

| Clase | Precisión | Recall | F1 | Tickets |
|---|---|---|---|---|
| Change | 0,98 | 0,93 | 0,95 | 193 |
| Incident | 0,82 | 0,84 | 0,83 | 697 |
| Problem | 0,69 | 0,67 | 0,68 | 374 |
| Request | 0,98 | 0,99 | 0,98 | 525 |

Matriz de confusión (filas = real, columnas = predicho):

| | Change | Incident | Problem | Request |
|---|---|---|---|---|
| **Change** | **179** | 2 | 1 | 11 |
| **Incident** | 0 | **587** | 110 | 0 |
| **Problem** | 1 | 122 | **250** | 1 |
| **Request** | 2 | 3 | 0 | **520** |

### Prioridad por clase

| Clase | Precisión | Recall | F1 | Tickets |
|---|---|---|---|---|
| high | 0,64 | 0,67 | 0,65 | 673 |
| medium | 0,62 | 0,65 | 0,63 | 730 |
| low | 0,59 | 0,49 | 0,54 | 386 |

| | high | low | medium |
|---|---|---|---|
| **high** | **449** | 49 | 175 |
| **low** | 82 | **190** | 114 |
| **medium** | 173 | 84 | **473** |

### Equipo por clase

| Clase | Precisión | Recall | F1 | Tickets |
|---|---|---|---|---|
| Billing and Payments | 0,77 | 0,77 | 0,77 | 189 |
| Service Outages and Maintenance | 0,68 | 0,62 | 0,65 | 82 |
| Human Resources | 0,61 | 0,59 | 0,60 | 32 |
| Technical Support | 0,56 | 0,61 | 0,58 | 470 |
| General Inquiry | 0,55 | 0,55 | 0,55 | 29 |
| IT Support | 0,52 | 0,54 | 0,53 | 206 |
| Product Support | 0,55 | 0,49 | 0,52 | 362 |
| Customer Service | 0,53 | 0,49 | 0,51 | 295 |
| Sales and Pre-Sales | 0,46 | 0,46 | 0,46 | 52 |
| Returns and Exchanges | 0,42 | 0,47 | 0,45 | 72 |

Confusiones más frecuentes: Product Support → Technical Support (87), Technical Support → Product Support (57), Customer Service → Technical Support (55), IT Support → Technical Support (48).

## 3.8 Análisis de errores

1. **Incident vs. Problem (232 de los 253 errores de categoría).** En ITIL un *incidente* es una falla puntual y un *problema* es la causa de fondo de varios incidentes. En el texto se describen casi igual ("the system crashes when…"); la diferencia suele estar en el contexto, que el ticket no trae. Change y Request, que tienen palabras muy propias ("upgrade", "please provide"), salen casi perfectos.
2. **La prioridad es en parte subjetiva.** La mayoría de errores son entre clases vecinas (high↔medium 348, low↔medium 198). Solo 131 son errores graves (high↔low). Low tiene el recall más bajo (0,49): el modelo tiende a subir la urgencia, que es el error menos costoso.
3. **Los equipos de soporte se solapan.** Technical, Product e IT Support atienden temas parecidos, y "Technical Support", la clase más grande, absorbe gran parte de los errores. Los equipos con vocabulario propio (Billing: "invoice", "charge", "refund"; Outages: "maintenance", "downtime") salen mejor.
4. **Un solo número esconde esto.** La exactitud del equipo (56,6 %) parece baja, pero el modelo multiplica por 13 al baseline en Macro-F1, y su puntaje permite separar los casos fáciles de los difíciles (sección 3.9).

## 3.9 Umbral de revisión manual (regla R2)

El SVM no da probabilidades; da márgenes. Se normalizan con *softmax* para obtener un **puntaje** entre 0 y 1 que sirve para ordenar las opciones, pero **no es una probabilidad calibrada**. Con 10 equipos, el puntaje más alto suele estar entre 0,15 y 0,32.

Efecto del umbral sobre el conjunto de prueba:

| Umbral | Se asigna solo | Acierto en lo asignado solo |
|---|---|---|
| 0,12 | 100 % | 57 % |
| 0,15 | 89 % | 60 % |
| 0,18 | 60 % | 71 % |
| **0,20** (elegido) | **45 %** | **78 %** |
| 0,25 | 22 % | 90 % |
| 0,30 | 13 % | 95 % |

Con 0,20, casi la mitad de los tickets se asigna sola y acierta 4 de cada 5 veces; el resto va a una persona. El valor se configura con `UMBRAL_EQUIPO`: si el negocio prefiere menos errores, se sube.

*Nota de diseño:* el primer umbral fue 0,35. Con los datos de demostración, el 92 % de los tickets terminaba en revisión manual. Por eso se midió esta tabla y se ajustó el valor.

## 3.10 Efecto de la regla R1 (palabras críticas)

172 de los 1.789 tickets de prueba contienen una palabra crítica ("outage", "down", "breach", "hacked", "ransomware", "data loss"…). Solo el 51 % de ellos es realmente `high` en el dataset.

| | Macro-F1 prioridad | Recall de high | Precisión de high |
|---|---|---|---|
| Solo modelo | 0,607 | 0,667 | 0,638 |
| Modelo + R1 | 0,593 | 0,698 | 0,604 |

R1 baja un poco el Macro-F1, pero **sube la detección de tickets urgentes**. Es una decisión de negocio, no de precisión: se prefiere revisar algunos tickets de más antes que dejar una caída real en prioridad media. Por eso R1 es una regla explícita y no algo que el modelo aprenda.

## 3.11 Métricas de software (dashboard)

Se separan de las métricas de IA:

- **Lead time:** horas promedio entre la creación y el cierre de un ticket.
- **Tasa de reasignación:** tickets reasignados al menos una vez / total. Mide en la operación real cuánto se equivoca la sugerencia de equipo (incluye los que pasaron por revisión manual).
- Conteos por estado, categoría, prioridad y equipo.
- **Tiempo de respuesta de la API:** mediana de unos 5 ms por clasificación (cabecera `X-Tiempo-ms`). Los modelos se cargan al arrancar para que la primera petición no tarde.

## 3.12 Trabajo futuro

- Probar un transformer multilingüe (p. ej. DistilBERT) para mejorar Incident/Problem y aceptar tickets en español.
- Calibrar los puntajes (`CalibratedClassifierCV`) para que sean probabilidades reales.
- Reentrenar con las correcciones de los analistas (las reasignaciones son etiquetas nuevas).
