---
name: generar-candidatura
description: >-
  Genera una candidatura 2026 desde oferta/ y el vault inmutable en base/:
  parse de la oferta, match determinista, go/no-go, CV ATS (PDF+DOCX),
  presentación, respuestas y briefing de entrevista. Usar cuando el usuario
  dice genera candidatura, aplica a esta oferta, adapta el CV, rellena
  oferta/ o pide curriculum.pdf y presentacion.md para un puesto.
---

# Generar candidatura

No reescribas el CV en un solo prompt. Ejecuta el pipeline en orden. Hechos solo de `base/`. Scripts, no improvisar renders.

Si el vault está vacío (`cvtool validate` sale VACÍO), para y pide **inicializa mi base**.

## Checklist

```
- [ ] 0 Vault válido
- [ ] 1 jd.yaml
- [ ] 2 empresa.md
- [ ] 3 match → gaps.yaml + veredicto.yaml
- [ ] 4 Go/no-go
- [ ] 5 plan.yaml
- [ ] 6 cv.yaml atómico
- [ ] 7 Revisor adversario
- [ ] 8 PDF + DOCX + verify
- [ ] 9 presentacion, respuestas, entrevista
- [ ] 10 Copiar a cv/ y tablero
```

Raíz del repo: carpeta que contiene `base/` y `oferta/`.

```bash
PY=".venv/bin/python"
[ -x "$PY" ] || PY=python3
CVTOOL="$PY scripts/cvtool.py"
```

Usa `$CVTOOL` para validate, match, scaffold, basename, render, verify, salary, copy y tablero. Ignora líneas placeholder de `oferta/` al parsear (`Pega aquí…`, `Luego escribe…`, `Si no hay preguntas…`).

## 0. Vault

```bash
$CVTOOL validate
```

Si hay ERROR, para. Si sale VACÍO, para y ejecuta el skill `inicializar-base`. Si solo WARN de `pendiente`, continúa y no inventes esos campos.

## 1. Parse → carpeta de candidatura

Lee `oferta/descripcion.md`, `oferta/preguntas.md`, `oferta/meta.yaml`.

Slug: `YYYY-MM-DD_empresa_puesto` (minúsculas, guiones, sin acentos). Hoy = fecha del sistema. Misma empresa+puesto el mismo día → reutiliza la carpeta. Otra fecha → carpeta nueva. No pises `candidaturas/` de otra fecha.

Escribe `candidaturas/<slug>/oferta/` (copia de descripcion, preguntas, meta) y `candidaturas/<slug>/jd.yaml` según [schemas.md](schemas.md).

T1 = título exacto + 5–8 términos literales del anuncio. Completa `oferta/meta.yaml` si puedes extraer empresa/puesto/url.

Headline: copia el título de la oferta solo si describe al candidato (`base/perfil.yaml` → `titulos_defendibles`). Nunca Senior, Arquitecto, Lead, Manager.

## 2. Empresa → `empresa.md`

Si hay empresa o URL, busca 3 hechos reales (producto, stack público, noticia) con fuente. Sin fuente: `sin_hechos_verificables: true`. No inventes cultura ni premios.

## 3. Match (sin LLM)

```bash
$CVTOOL match --jd candidaturas/<slug>/jd.yaml \
  --out candidaturas/<slug>/gaps.yaml \
  --veredicto candidaturas/<slug>/veredicto.yaml
```

## 4. Go / no-go

Si `resultado: no_aplicar` y el usuario no ha dicho que fuerce: **para**, enseña `motivos`, no generes CV. Si fuerza: `forzar: true` y sigue.

Familia: elige un `id` de `base/familias.yaml` según título y T1 (`titulos_tipicos`). Si ninguna encaja, pregunta. No asumas familias que no estén en el vault.

## 5. Plan → `plan.yaml`

Toca resumen, 8–15 skills y 3–4 bullets de máximo impacto. No reescribas el CV entero.

- Primer bullet de cada rol = el más alineado a esta oferta
- T1 honestos (`have` o `rephrase`) en perfil + competencias + al menos un bullet
- Gaps `missing`: presentación o respuestas, nunca el CV
- Sección Proyectos solo si esa familia tiene `incluye_proyectos: true` (o el JD es híbrido y el vault tiene proyectos)

## 6. `cv.yaml`

Parte de `plantillas/cv_default_<familia>.yaml`. Si no existe: `$CVTOOL scaffold`. Cada bullet `{texto, evidencia_id}` de `base/evidencias.yaml`.

Reglas:

- Verbo + herramienta + resultado. Presente en el puesto actual; pasado en el resto
- Sin métrica en el vault → alcance/contexto, nunca un %
- Skills: nivel `diario` o `proyecto`, salvo que la oferta nombre una `formativa`
- 8–15 competencias; blandas solo si un bullet las demuestra
- Prohibido `IA` genérico; nombra la herramienta del vault (n8n, etc.)
- 1 página; ciudad sin código postal; URLs completas (no bit.ly)

Luego, con el cv ya escrito:

```bash
$CVTOOL match --jd candidaturas/<slug>/jd.yaml \
  --cv candidaturas/<slug>/cv.yaml \
  --out candidaturas/<slug>/gaps.yaml \
  --veredicto candidaturas/<slug>/veredicto.yaml
```

Si hay `huerfanas` en T1, mete el término en competencias y en un bullet honesto.

## 7. Revisor

Sigue [revision-checklist.md](revision-checklist.md). Escribe `revision.md` (objeciones y si se aceptó el cambio).

## 8. Render

Basename de envío (sin espacios, derivado del nombre del vault):

```bash
SEND=$($CVTOOL basename --puesto "<Puesto>" --empresa "<Empresa>")
$CVTOOL render --cv candidaturas/<slug>/cv.yaml \
  --out-dir candidaturas/<slug> --basename curriculum
cp candidaturas/<slug>/curriculum.pdf candidaturas/<slug>/${SEND}.pdf
cp candidaturas/<slug>/curriculum.docx candidaturas/<slug>/${SEND}.docx
cp candidaturas/<slug>/curriculum.md candidaturas/<slug>/${SEND}.md
$CVTOOL verify candidaturas/<slug>/curriculum.pdf \
  --out candidaturas/<slug>/_extract.txt
```

Si `verify` falla, no copies a `cv/`. Si la oferta pide docx, el archivo de envío es el `.docx`.

## 9. Presentación, respuestas, entrevista

- `presentacion.md`: 3 párrafos, 250–400 palabras, listo para pegar (sin títulos markdown). 1) por qué esta empresa (hecho de `empresa.md`), 2) un ejemplo del CV adaptado, 3) CTA. Cero clichés de la lista negra.
- `respuestas.md`: solo si `oferta/preguntas.md` tiene preguntas reales. Escribe `candidaturas/<slug>/respuestas_data.yaml` con clave `respuestas` (cada ítem: `pregunta`, `respuesta`, `limite` opcional, `fuente`, `necesita_confirmacion`) y renderiza:

```bash
$CVTOOL respuestas --data candidaturas/<slug>/respuestas_data.yaml \
  --out candidaturas/<slug>/respuestas.md
```

Knockouts primero. Preaviso desde `base/constraints.yaml`. Salario: `$CVTOOL salary --familia <id> [--oferta-min N] [--oferta-max N]` y usa el `texto` (si imprime `NECESITA_CONFIRMACION`, no inventes cifra). Si falta otro hecho: `NECESITA_CONFIRMACION`.
- `entrevista.md`: headline enviado, evidencias STAR usadas (ids), 5 talking points, gaps que no debe fingir.
- `analisis.md`: familia, score T1, T1 missing, riesgos.
- `meta.yaml` de la candidatura: `listo_para_enviar: false`.

## 10. Copiar última versión y tablero

```bash
$CVTOOL copy --from-dir candidaturas/<slug>
$CVTOOL tablero set --slug "<slug>" --estado borrador \
  --empresa "<Empresa>" --puesto "<Puesto>"
```

En el chat: veredicto, ruta de la carpeta, PDF/DOCX a enviar, y avisos `NECESITA_CONFIRMACION`. Recuerda: el envío al portal lo hace la persona; después, **registrar envío**.

## Prohibido

- Editar `base/` salvo que el usuario pida actualizar la base
- Editar `base/origen/`
- Inventar empleadores, fechas, métricas, tecnologías o certificaciones
- Enviar a portales
- Texto blanco o keyword stuffing
