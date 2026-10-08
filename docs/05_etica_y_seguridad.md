# 5. Ética, seguridad y uso responsable

## 5.1 Datos sensibles
Un ticket real puede traer nombres, correos, números de cuenta o datos de salud (sobre todo en Human Resources). En este proyecto los datos de entrenamiento son **sintéticos**, pero el sistema en operación recibiría datos reales. Medidas:
- El usuario operativo solo ve sus propios tickets.
- Las claves se guardan con bcrypt y nunca se devuelven.
- Los secretos (`JWT_SECRET`, clave del admin) están en `.env`, que no se sube al repositorio.
- El modelo no guarda el texto de los tickets nuevos ni se reentrena solo.
- Pendiente para producción: HTTPS, política de retención y anonimización de tickets antes de usarlos para reentrenar.

## 5.2 Sesgos
- **Idioma:** entrenado solo en inglés. Quien escriba en español recibe peores sugerencias. Por eso la interfaz lo avisa, y por eso existe la revisión manual.
- **Clases pequeñas:** equipos con pocos ejemplos (General Inquiry, Human Resources) tienen métricas menos estables.
- **Prioridad:** el modelo aprende lo que el dataset consideró urgente, que puede no coincidir con la política de una organización real.

## 5.3 Abuso y ataques
- Un usuario podría escribir palabras críticas ("outage", "breach") para subir su prioridad. Mitigación: el analista ve qué regla se aplicó y puede corregir; el historial deja registro.
- Textos enormes o malformados: limitados por validación (máx. 5000 caracteres).
- Acceso no autorizado: JWT + roles, probado con pruebas de 401/403.

## 5.4 Explicabilidad
Cada sugerencia muestra la etiqueta elegida, su puntaje, las dos alternativas siguientes y las reglas aplicadas. Así se ve cuándo el modelo duda. El puntaje **no** es una probabilidad calibrada y la interfaz lo advierte.

## 5.5 Supervisión humana
La IA **sugiere**; el analista decide. Los tickets dudosos van a revisión manual (R2), cualquier asignación se puede corregir y cada corrección queda medida en la tasa de reasignación. El sistema no cierra ni resuelve tickets por sí solo.

## 5.6 Limitaciones
- Macro-F1 de equipo 0,56: sin revisión humana se equivocaría en casi la mitad de los casos.
- Incident y Problem se confunden con frecuencia (sección 3.8).
- Datos sintéticos: el rendimiento con tickets reales debe medirse otra vez antes de usarlo en producción.
