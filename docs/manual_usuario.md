# Manual de usuario

## 1. Entrar
Abra http://localhost:8080. Si no tiene cuenta, pulse **¿No tienes cuenta? Regístrate**, escriba nombre, correo y una clave de al menos 8 caracteres. Las cuentas nuevas son de tipo **operativo**.

## 2. Reportar una incidencia (todos los usuarios)
1. Pulse **Nuevo**.
2. Escriba un asunto corto y describa el problema **en inglés** (mínimo 10 caracteres).
3. Pulse **Crear y clasificar**.
4. Aparece la tarjeta **Lo que sugirió la IA**:
   - **Categoría, Prioridad y Equipo** en negrilla: la decisión final.
   - La barra y el texto "Modelo: …" muestran qué tan seguro estuvo el modelo y cuáles eran las otras opciones.
   - Si aparece un recuadro amarillo, el sistema aplicó una regla. Por ejemplo, subió la prioridad porque el texto habla de una caída, o envió el ticket a **Revisión manual** porque el modelo no estaba seguro del equipo.

## 3. Ver mis tickets
En **Tickets** aparece la lista con su estado. Puede filtrar por estado y pulsar un ticket para ver el detalle y el historial. Un usuario operativo solo ve sus propios tickets.

## 4. Gestionar tickets (analista y administrador)
En el detalle de un ticket aparece el panel **Gestionar**:
- **Pasar a …**: cambia el estado. Solo se ofrecen los pasos permitidos (Abierto → En progreso → Resuelto → Cerrado; se puede reabrir).
- **Reasignar**: elija otro equipo si la sugerencia no era correcta.
- **Comentario**: opcional; queda en el historial.

Un ticket cerrado ya no se puede modificar.

## 5. Dashboard (analista y administrador)
- **Tickets**: total registrados.
- **Tiempo promedio hasta cerrar**: horas entre la creación y el cierre.
- **Tasa de reasignación**: porcentaje de tickets que hubo que mover de equipo. Si sube, la IA está ayudando menos.
- **Calidad del modelo**: Macro-F1 y exactitud medidos con tickets que el modelo nunca vio.
- Conteos por estado, prioridad, categoría y equipo.

## 6. Preguntas frecuentes
- **¿Por qué mi ticket quedó en "Revisión manual"?** El modelo no estaba seguro del equipo; una persona lo asignará.
- **¿Puedo escribir en español?** Sí, pero la sugerencia será menos precisa: el modelo aprendió con tickets en inglés.
- **¿El "puntaje" es una probabilidad?** No exactamente. Sirve para comparar las opciones del modelo entre sí.
