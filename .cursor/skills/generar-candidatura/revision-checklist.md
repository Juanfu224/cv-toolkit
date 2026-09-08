# Revisor adversario

Busca un motivo para descartar. Si hay objeción grave, corrige solo ese bloque de `cv.yaml` y vuelve a `cvtool match` + `cvtool verify`. Si el score T1 no sube, descarta el cambio.

## Objeciones

- Afirmación sin `evidencia_id` del vault
- Número, %, o métrica que no está en `base/evidencias.yaml`
- Tecnología, empresa o fecha que no está en `base/`
- Verbo débil: responsable de, colaboré en, ayudé a, me encargué de
- Cliché de IA: apasionado por, excelentes habilidades, me permito presentar, orientado a resultados, dinámico entorno, altamente motivado
- Keyword stuffing (el mismo T1 más de 3 veces fuera de contexto)
- Headline que no está en `titulos_defendibles` ni es el título de la oferta de forma honesta
- Presentación sin un hecho de `empresa.md` cuando ese archivo sí tiene hechos
- Skill formativa en el CV si la oferta no la nombra
- Inconsistencia de fechas con el vault

## Lista negra (prohibido en CV, presentación y respuestas)

apasionado por, excelentes habilidades, me permito presentar, orientado a resultados, altamente motivado, destacado profesional, sinergias, robusto ecosistema, leveraged, spearheaded
