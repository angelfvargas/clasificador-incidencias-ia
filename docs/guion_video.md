# Guion del video de demostración (≈ 5 minutos)

Antes de grabar: `docker-compose up -d --build` y cargar datos demo con `scripts/sembrar_demo.py`. Tener abiertos el navegador en http://localhost:8080 y la terminal.

| Tiempo | Qué mostrar | Qué decir |
|---|---|---|
| 0:00–0:30 | Portada / README | "Este es el clasificador inteligente de incidencias. Recibe tickets de soporte y sugiere categoría, prioridad y equipo, sin reemplazar a la persona que decide." |
| 0:30–1:00 | Terminal: `docker-compose up -d --build` y `docker-compose ps` | "Todo el sistema arranca con un comando: base de datos, API e interfaz." |
| 1:00–2:00 | Registrarse como usuario nuevo y crear un ticket de cobro doble | "El usuario reporta en inglés. La IA dice que es de Billing and Payments; la barra muestra qué tan seguro está y cuáles eran las otras opciones." |
| 2:00–2:40 | Crear "Our main website is down…" | "Aquí actúa una regla de negocio: el texto habla de una caída, así que la prioridad sube a alta aunque el modelo dijera otra cosa. Y como el modelo dudaba del equipo, lo mandó a revisión manual." |
| 2:40–3:30 | Entrar como admin, abrir el ticket, pasarlo a En progreso, reasignarlo, mostrar historial | "El analista corrige y avanza el ticket. Todo queda en el historial, incluida la versión del modelo que lo clasificó." |
| 3:30–4:20 | Dashboard | "Aquí se separan las métricas de software (lead time, tasa de reasignación) de las del modelo: Macro-F1 de 0,86 en categoría, 0,61 en prioridad y 0,56 en equipo, contra un baseline de 0,14, 0,19 y 0,04." |
| 4:20–4:50 | Terminal: `pytest -q` (22 passed) y http://localhost:8000/docs | "Hay 22 pruebas automáticas y la API está documentada con Swagger." |
| 4:50–5:00 | Cierre | "La mayor limitación es la confusión entre Incident y Problem y entre equipos de soporte parecidos; por eso el sistema deja la decisión final a una persona." |
