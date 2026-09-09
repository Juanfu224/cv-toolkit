# Revisor adversario

Busca un motivo para descartar. Si hay objeción grave, corrige solo ese bloque de `cv.yaml` y vuelve a `cvtool match` + `cvtool verify`. Si el score T1 no sube, descarta el cambio.

## Objeciones

- Afirmación sin `evidencia_id` del vault
- Número, %, o métrica que no está en `base/evidencias.yaml`
- Tecnología, empresa o fecha que no está en `base/`
- Verbo débil: responsable de, colaboré en, ayudé a, me encargué de
- Cliché de IA: apasionado por, excelentes habilidades, me permito presentar, orientado a resultados, dinámico entorno, altamente motivado, I am thrilled to apply
- Keyword stuffing (el mismo T1 más de 3 veces fuera de contexto)
- Eco acción→resultado (la 2ª frase parafrasea la 1ª; fusionar o cortar)
- Perfil = lista de tools/skills que duplica Competencias (debe ser 2–4 frases de encaje)
- Bullet tool-only («uso Jira/IDE…» sin resultado ni alcance); integrar la tool en un bullet de resultado o dejarla en Competencias
- Proyectos: bullet que solo repite `stack`/`url` de la cabecera (aportar alcance o decisión)
- Ritmo idéntico en todas las viñetas (mismo molde de longitud/foco)
- Headline que no está en `titulos_defendibles` ni es el título de la oferta de forma honesta
- Presentación que abre con descripción de la empresa
- Presentación con gaps en **cualquier** parte del cuerpo («No tengo…», «me falta», «carezco», «nivel formativo» / «estoy formándome») — no solo al abrir; idiomáticos («no tengo duda») OK
- Presentación que ecoa el `cv.perfil` o pega el mismo bullet en P1/P2 — solo revisor (no factcheck)
- Presentación P1 = dump de competencias/tools
- Presentación con CTA genérico («quedo a disposición», «quedo a su disposición», «adjunto CV», «espero sus noticias»)
- Presentación con motivación solo egocéntrica («quiero crecer», «me interesa el reto») sin valor para el puesto — solo revisor (no factcheck)
- Presentación sin diferenciador (serviría para cualquier candidato con el mismo stack) — solo revisor (no factcheck)
- Presentación >250 palabras u outreach >80 palabras
- Outreach que nombra un hiring manager no presente en el JD o `oferta/meta.yaml`
- Skill formativa en el CV si la oferta no la nombra
- Inconsistencia de fechas con el vault
- Certificaciones con `nombre` null/`none` o literal `None` en el PDF/MD

## Lista negra (prohibido en CV, presentación, respuestas y outreach)

apasionado por, excelentes habilidades, me permito presentar, orientado a resultados, altamente motivado, destacado profesional, sinergias, robusto ecosistema, leveraged, spearheaded, I am thrilled to apply

Además en presentación: prohibido en el cuerpo «No tengo» / «me falta» / «carezco» / «nivel formativo» (salvo idiomáticos); CTA comodín («quedo a (su) disposición», «adjunto CV», «me pongo a disposición»). Eco perfil / egocéntrico / sin diferenciador = solo revisor. En respuestas públicas: no abrir con ausencias.