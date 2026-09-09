# Revisor adversario

Busca un motivo para descartar. Si hay objeción grave, corrige solo ese bloque de `cv.yaml` y vuelve a `cvtool match` + `cvtool verify`. Si el score T1 no sube, descarta el cambio.

## Objeciones

- Afirmación sin `evidencia_id` del vault
- Número, %, o métrica que no está en `base/evidencias.yaml`
- Tecnología, empresa o fecha que no está en `base/`
- Verbo débil: responsable de, colaboré en, ayudé a, me encargué de
- Cliché de IA: apasionado por, excelentes habilidades, me permito presentar, orientado a resultados, dinámico entorno, altamente motivado, I am thrilled to apply
- Keyword stuffing (el mismo T1 más de 3 veces fuera de contexto)
- Headline que no está en `titulos_defendibles` ni es el título de la oferta de forma honesta
- Presentación que abre con descripción de la empresa o con «No tengo…» / lista de ausencias
- Presentación >250 palabras u outreach >80 palabras
- Outreach que nombra un hiring manager no presente en el JD o `oferta/meta.yaml`
- Skill formativa en el CV si la oferta no la nombra
- Inconsistencia de fechas con el vault
- Certificaciones con `nombre` null/`none` o literal `None` en el PDF/MD

## Lista negra (prohibido en CV, presentación, respuestas y outreach)

apasionado por, excelentes habilidades, me permito presentar, orientado a resultados, altamente motivado, destacado profesional, sinergias, robusto ecosistema, leveraged, spearheaded, I am thrilled to apply

Además en presentación/respuestas públicas: no abrir con «No tengo», «me falta», «carezco de».