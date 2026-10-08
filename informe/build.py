"""Arma el informe final en PDF a partir de docs/*.md y las capturas de img/.

Uso: .venv/bin/python build.py   →   Informe_Final_Clasificador_Incidencias.pdf
"""
import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
DOCS = AQUI.parent / "docs"
SALIDA = AQUI / "Informe_Final_Clasificador_Incidencias.pdf"


def md(texto):
    # bloques mermaid → <pre class="mermaid"> para que mermaid.js los dibuje
    texto = re.sub(r"```mermaid\n(.*?)```", lambda m: f'<pre class="mermaid">\n{m.group(1)}</pre>', texto, flags=re.S)
    return markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])


def doc(nombre, quitar=()):
    t = (DOCS / nombre).read_text()
    for q in quitar:
        t = t.replace(q, "")
    return t


def anexo(nombre, letra, titulo):
    t = doc(nombre)
    t = re.sub(r"^# .*\n", f"# Anexo {letra}. {titulo}\n", t, count=1)
    t = re.sub(r"^## (\d+)\. ", rf"## {letra}.\1 ", t, flags=re.M)
    return t


PORTADA = """
<section class="portada">
  <p class="u">UNIVERSIDAD LIBRE · SECCIONAL CALI<br>Facultad de Ingeniería · Ingeniería de Sistemas</p>
  <h1>Clasificador inteligente de incidencias de software</h1>
  <p class="sub">Informe final del proyecto de curso</p>
  <p class="curso">Optativa III – Deep Learning y Agentes Inteligentes</p>
  <div class="datos">
    <p><b>Estudiante</b><br>Angel Farid Agreda Vargas</p>
    <p><b>Docente</b><br>Julián René Muñoz Burbano</p>
    <p><b>Repositorio</b><br>github.com/angelfvargas/clasificador-incidencias-ia</p>
  </div>
  <p class="fecha">Santiago de Cali, octubre de 2026</p>
</section>
"""

RESUMEN = """
# Resumen

Este proyecto construye una aplicación web que recibe tickets de soporte y **sugiere su categoría, su prioridad y el equipo responsable** mediante procesamiento de lenguaje natural y aprendizaje supervisado. La inteligencia artificial no se entrega como un notebook aislado: es un componente dentro de un sistema completo con requisitos, arquitectura por capas, base de datos, API REST, interfaz, autenticación por roles, reglas de negocio, pruebas automatizadas, integración continua y despliegue con Docker.

Se entrenó con 11.923 tickets en inglés del dataset público *Customer Support Tickets*. Se compararon un baseline (clase más frecuente), regresión logística y SVM lineal sobre TF-IDF. El SVM lineal obtuvo en el conjunto de prueba un **Macro-F1 de 0,863 en categoría, 0,607 en prioridad y 0,563 en equipo**, frente a 0,140, 0,193 y 0,043 del baseline.

El sistema separa lo que decide el modelo de lo que decide el negocio. Una regla eleva a prioridad alta los tickets con señales críticas, y otra envía a revisión manual los tickets donde el modelo duda del equipo. Con el umbral elegido, el 45 % de los tickets se asigna automáticamente con un 78 % de acierto. Cada predicción guarda la versión del modelo, sus puntajes y las reglas aplicadas, y el dashboard separa las métricas de software (lead time, tasa de reasignación) de las métricas del modelo.

**Palabras clave:** ingeniería de software, clasificación de texto, NLP, TF-IDF, SVM, FastAPI, MongoDB, React, MLOps.

# Introducción

En una mesa de ayuda, cada ticket nuevo debe leerlo una persona para decidir de qué se trata, qué tan urgente es y a quién le corresponde. Este triage manual consume tiempo, depende de quien esté de turno y genera reasignaciones cuando el ticket llega al equipo equivocado.

**Objetivo general.** Desarrollar un producto de software mantenible, probado, seguro y trazable que incorpore un modelo de clasificación de texto para sugerir la categoría, la prioridad y el equipo responsable de un ticket, manteniendo la supervisión humana sobre la decisión final.

**Objetivos específicos.**

1. Levantar los requisitos del sistema como historias de usuario con criterios de aceptación verificables.
2. Diseñar una arquitectura por capas en la que el modelo se pueda reemplazar sin reescribir la aplicación.
3. Entrenar y evaluar modelos de clasificación frente a un baseline, sin fuga de información entre los conjuntos.
4. Integrar el modelo en una API con persistencia, autenticación, reglas de negocio y seguimiento por estados.
5. Verificar el sistema con pruebas unitarias, de integración, del modelo y de aceptación, y desplegarlo de forma reproducible.
6. Documentar los riesgos éticos, los sesgos y las limitaciones del componente inteligente.

**Metodología.** Se siguió el proceso del enunciado del curso: descubrimiento, análisis, diseño, datos, baseline, modelo, backend, frontend, integración, pruebas, DevOps, evaluación, ética y entrega. Los capítulos 1 a 5 de este informe recogen esos productos; el capítulo 6 muestra la aplicación funcionando.
"""

CAPTURAS = [
    ("01_login.png", "Ingreso y registro de usuarios."),
    ("02_nuevo_ticket.png", "Creación de un ticket por un usuario operativo. La tarjeta muestra la decisión final, el puntaje del modelo, las alternativas y las reglas aplicadas: R1 subió la prioridad porque el texto habla de una caída, y R2 envió el ticket a revisión manual porque el modelo dudaba del equipo."),
    ("03_lista.png", "Listado de tickets visto por el administrador, con categoría, prioridad, equipo y estado."),
    ("04_detalle.png", "Detalle del ticket con el panel de gestión (cambio de estado y reasignación) y el historial."),
    ("05_dashboard.png", "Dashboard con métricas de software y del modelo sobre 42 tickets de demostración. El lead time aparece en 0 h porque los tickets de demostración se crean y cierran en segundos; con uso real refleja horas de atención."),
    ("06_swagger.png", "Documentación interactiva de la API (OpenAPI / Swagger)."),
]

CONCLUSIONES = """
# 7. Conclusiones

1. **El componente de IA funciona como parte de un producto, no como un experimento aislado.** El flujo completo (registro → creación → clasificación → reglas → persistencia → gestión → métricas) se ejecuta de extremo a extremo y está cubierto por 22 pruebas automáticas que corren en integración continua.
2. **Un modelo sencillo bien evaluado es suficiente para aportar valor.** TF-IDF con SVM lineal multiplica por 6, 3 y 13 el Macro-F1 del baseline en categoría, prioridad y equipo. Además entrena en segundos y responde en unos 5 ms por ticket, sin necesidad de GPU.
3. **Un solo número esconde los errores importantes.** El análisis por clase mostró que casi todos los errores de categoría son entre *Incident* y *Problem*, y que los errores de equipo se concentran en colas de soporte que se solapan. Ese análisis sirvió para tomar decisiones de diseño.
4. **Separar modelo y reglas hace el sistema más seguro y explicable.** Las decisiones que son política del negocio (prioridad mínima ante una caída, umbral de revisión manual, ciclo de vida, permisos) quedaron como reglas deterministas, probadas y visibles para el usuario. El umbral de revisión manual se eligió midiendo su efecto en lugar de fijarlo a ojo: el primer valor (0,35) mandaba el 92 % de los tickets a revisión.
5. **La supervisión humana sigue siendo necesaria.** Con un Macro-F1 de 0,56 en equipo, la IA debe presentarse como apoyo. La tasa de reasignación del dashboard permite medir en operación si realmente ayuda.

**Trabajo futuro:** probar un transformer multilingüe para mejorar la distinción Incident/Problem y aceptar tickets en español, calibrar los puntajes como probabilidades y reentrenar periódicamente con las correcciones de los analistas.
"""

REFERENCIAS = """
# 8. Referencias

1. Pressman, R. S., y Maxim, B. R. *Software Engineering: A Practitioner's Approach*. McGraw-Hill.
2. Sommerville, I. *Software Engineering*. Pearson.
3. Géron, A. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. O'Reilly.
4. Gamma, E., Helm, R., Johnson, R., y Vlissides, J. *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.
5. Treveil, M., et al. *Introducing MLOps*. O'Reilly.
6. National Institute of Standards and Technology (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*.
7. Bueck, T. *Customer Support Tickets* [conjunto de datos]. Hugging Face: `Tobi-Bueck/customer-support-tickets`. Licencia CC BY-NC 4.0.
8. Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.
9. Muñoz Burbano, J. R. (2026). *Proyectos de Curso – Ingeniería de Software: guía detallada de formulación, desarrollo, arquitectura, pruebas y evaluación*. Universidad Libre.
"""

CSS = """
@page { size: Letter; margin: 2.2cm 2cm 2.2cm 2cm; }
body { font-family: "Noto Serif", Georgia, serif; font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-family: "Noto Sans", Arial, sans-serif; font-size: 17pt; color: #12345a; border-bottom: 2px solid #12345a;
     padding-bottom: 4px; margin: 0 0 12px; page-break-before: always; }
h2 { font-family: "Noto Sans", Arial, sans-serif; font-size: 12.5pt; color: #12345a; margin: 18px 0 6px; page-break-after: avoid; }
h3 { font-family: "Noto Sans", Arial, sans-serif; font-size: 11pt; margin: 14px 0 4px; page-break-after: avoid; }
p { margin: 0 0 8px; text-align: justify; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 12px; font-size: 8.8pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #e8eef6; text-align: left; }
th, td { border: 1px solid #b9c3d0; padding: 3px 6px; vertical-align: top; }
code { font-family: "Noto Sans Mono", monospace; font-size: 8.6pt; background: #f2f4f7; padding: 0 2px; }
pre { background: #f5f7fa; border: 1px solid #dde3ea; padding: 8px; font-size: 8pt; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; }
pre.mermaid { background: none; border: 0; text-align: center; }
pre.mermaid p { text-align: center; margin: 0; }
pre.mermaid svg { max-width: 100%; max-height: 17cm; }
ul, ol { margin: 0 0 8px; padding-left: 22px; }
li { margin-bottom: 2px; }
figure { margin: 10px 0 16px; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; max-height: 15.5cm; border: 1px solid #ccd3dc; }
figcaption { font-size: 9pt; color: #444; margin-top: 4px; text-align: center; }
.portada { height: 23cm; display: flex; flex-direction: column; justify-content: space-between; text-align: center; }
.portada h1 { border: 0; font-size: 26pt; page-break-before: avoid; margin-top: 3cm; }
.portada .u { font-family: "Noto Sans", sans-serif; letter-spacing: .5px; color: #12345a; }
.portada .sub { font-size: 14pt; text-align: center; }
.portada .curso { font-size: 12pt; text-align: center; color: #333; }
.portada .datos p { text-align: center; margin-bottom: 14px; }
.portada .fecha { text-align: center; }
.toc h1 { page-break-before: always; }
.toc ol { list-style: none; padding-left: 0; }
.toc li { margin: 4px 0; }
.toc li.sub { padding-left: 18px; font-size: 9.5pt; color: #333; }
"""


def main():
    capitulos = [
        doc("01_vision_y_requisitos.md", quitar=[
            "**Proyecto:** Clasificador inteligente de incidencias de software\n",
            "**Curso:** Optativa III – Deep Learning y Agentes Inteligentes · Docente: Julián René Muñoz Burbano\n",
            "**Estudiante:** Angel Farid Agreda Vargas · Universidad Libre, Cali · 2026-2\n"]),
        doc("02_arquitectura.md", quitar=["Los diagramas están en Mermaid: GitHub los dibuja automáticamente al abrir este archivo.\n"]),
        doc("03_datos_y_modelo.md"),
        doc("04_pruebas.md"),
        doc("05_etica_y_seguridad.md"),
    ]
    figuras = "# 6. La aplicación en funcionamiento\n\n" + "".join(
        f'<figure><img src="img/{f}"><figcaption>Figura {i}. {c}</figcaption></figure>\n'
        for i, (f, c) in enumerate(CAPTURAS, 1))
    anexos = [anexo("manual_usuario.md", "A", "Manual de usuario"),
              anexo("manual_tecnico.md", "B", "Manual técnico")]

    cuerpo_md = "\n\n".join([RESUMEN, *capitulos, figuras, CONCLUSIONES, REFERENCIAS, *anexos])
    cuerpo = md(cuerpo_md)

    # tabla de contenido a partir de los h1/h2
    toc = []
    for nivel, titulo in re.findall(r"<h([12])>(.*?)</h\1>", cuerpo):
        toc.append(f'<li class="{"sub" if nivel == "2" else ""}">{titulo}</li>')
    toc_html = f'<section class="toc"><h1>Contenido</h1><ol>{"".join(toc)}</ol></section>'

    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Informe final – Clasificador inteligente de incidencias</title><style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script></head>
<body>{PORTADA}{toc_html}{cuerpo}
<script>mermaid.initialize({{startOnLoad: false, theme: "neutral", themeVariables: {{fontSize: "17px"}}, flowchart: {{useMaxWidth: true}}, sequence: {{useMaxWidth: true, actorFontSize: 15, messageFontSize: 15}}}});
mermaid.run().then(() => document.body.dataset.listo = "1");</script></body></html>"""
    (AQUI / "informe.html").write_text(html)

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto((AQUI / "informe.html").as_uri())
        pg.wait_for_selector("body[data-listo='1']", timeout=60000)
        pg.pdf(path=str(SALIDA), format="Letter", print_background=True, display_header_footer=True,
               header_template="<span></span>",
               footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#666;">'
                               'Clasificador inteligente de incidencias · <span class="pageNumber"></span> / '
                               '<span class="totalPages"></span></div>',
               margin={"top": "2.2cm", "bottom": "2.2cm", "left": "2cm", "right": "2cm"})
        b.close()
    print(SALIDA)


if __name__ == "__main__":
    main()
