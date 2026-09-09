# Guía de uso (candidato)

Manual para aplicar a trabajos con este kit. Camino feliz y frases canónicas: [README raíz](../README.md).

## Instalación

Python **3.10+**.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/cvtool.py doctor
```

WeasyPrint (si `doctor` falla en weasyprint):

```bash
# Fedora
sudo dnf install pango cairo gdk-pixbuf2 gcc python3-devel
# Debian / Ubuntu
sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 gcc python3-dev
# macOS
brew install pango cairo gdk-pixbuf
```

PDF como origen del CV: instala `pdftotext` (poppler) si usas `curriculum.pdf` en lugar de `.md`.

## Primer uso

1. CV en [`base/origen/`](../base/origen/) (`curriculum.md` preferido). Si tienes presentación (carta o bio), `presentacion.md` en el mismo sitio.
2. **inicializa mi base** (agente).
3. Oferta en [`oferta/descripcion.md`](../oferta/descripcion.md) → **genera candidatura**.
4. Revisa `cv/` y el pack en `candidaturas/YYYY-MM-DD_…/`.
5. Envías tú al portal → **registrar envío**.

Sin CV propio: [`ejemplos/`](../ejemplos/README.md) o `sh scripts/demo_smoke.sh`.

## Bucle diario

1. Pega la oferta nueva en `oferta/` (pisar el buzón está bien) o da una URL pública de Greenhouse/Ashby/Lever.
2. **genera candidatura**.
3. Revisa veredicto, factcheck, PDF/DOCX y presentación. **Aprueba, edita o rechaza** antes de que se copie a `cv/`. Si editas, el agente debe correr `cvtool refresh --dir candidaturas/<slug>/` para regenerar PDF y artefactos (no dejar el pack viejo).
4. Envía al portal (InfoJobs, LinkedIn, email…). El outreach es un borrador: lo envías tú.
5. **registrar envío**.

La presentación va centrada en ti (encaje + evidencia + CTA), no en una intro de la empresa ni en lo que te falta.
Si cambió un hecho real (salario, proyecto, skill): **actualizar base** antes de la siguiente oferta.

## Veredicto y `--forzar`

Tras el match, lee `candidaturas/<slug>/veredicto.yaml`. Umbrales T1 del match:

| Cobertura T1 | `resultado` típico |
|---|---|
| &lt; 40% | `no_aplicar` |
| &lt; 70% o algún T1 faltante | `aplicar_con_reservas` |
| ≥ 70% y T1 cubiertos | `aplicar` (si no hay knockouts) |

También `no_aplicar` si falta un `must_have`, seniority en knockouts, presencial fuera de zona sin traslado, o certs ausentes.

| `resultado` | Qué hacer |
|---|---|
| `aplicar` | Sigue el pipeline; revisa y envía |
| `aplicar_con_reservas` | Revisa gaps; decide tú |
| `no_aplicar` | El agente para |

Si tú fuerzas pese a `no_aplicar`:

```bash
.venv/bin/python scripts/cvtool.py match --jd candidaturas/<slug>/jd.yaml --base base --forzar
```

`--forzar` solo pone `forzar: true` (HITL); **no cambia** `resultado`. El agente puede seguir el pipeline si tú lo pediste.

`cvtool copy` exige `factcheck.yaml` con `ok: true` y `meta.pack_estado: aprobado`. Sin eso, no copia a `cv/` (salvo `--force` que tú pidas explícitamente).

## Qué enviar al portal

- PDF/DOCX de `cv/` (última generación) o del pack en `candidaturas/<slug>/`.
- Carta: `cv/presentacion.md` (≤250 palabras) o la del pack.
- Outreach (opcional): `cv/outreach.md` — lo envías tú; el agente no publica.
- El PDF **no** sustituye el perfil de InfoJobs u otros portales: rellena el formulario del portal aparte.

## ATS y límites

- Una columna, texto seleccionable, contacto en el cuerpo, PDF + DOCX.
- Hechos solo del vault. `no_aplicar` si falta un `must_have`, T1 &lt;40%, seniority en knockouts, presencial fuera de zona sin traslado, o certs ausentes. T1 entre 40% y 70% (o T1 faltante) → `aplicar_con_reservas`.

## Carpetas

`base/` hechos · `oferta/` buzón · `cv/` última generación · `candidaturas/` historial · `plantillas/` ATS · `ejemplos/` demo · `scripts/cvtool.py` CLI.

## Con cualquier agente

Abre este repo en Cursor, Claude Code, Codex u otro runtime que lea [`AGENTS.md`](../AGENTS.md) y skills. El contrato no depende de un IDE:

| Artefacto | Rol |
|---|---|
| [`AGENTS.md`](../AGENTS.md) | Router (qué skill cargar) |
| [`.agents/skills/`](../.agents/skills/) | Recetas de producto |
| [`SPEC.md`](../SPEC.md) | Contrato de dominio |
| [`SHIELD.md`](../SHIELD.md) | Hard stops / PII / no autoenviar |
| [`CLAUDE.md`](../CLAUDE.md) | Puntero `@AGENTS.md` |

**Sin Cursor / Claude (Codex, ChatGPT, otro):** abre `AGENTS.md`, elige la frase de la tabla del README y **lee/pega** el archivo `.agents/skills/<nombre>/SKILL.md` en el chat. No esperes que el IDE cargue skills solo.

Cursor y Claude descubren las mismas skills vía symlink a `.agents/skills/`. En Windows: `git config core.symlinks true` + Developer Mode, o clona donde Git respete symlinks.

Skills `epic-workflow` y `shield-security-gate` son para **desarrollar el kit**, no para candidaturas diarias. Ver [desarrollar.md](desarrollar.md).

## CLI útil

```bash
.venv/bin/python scripts/cvtool.py doctor
.venv/bin/python scripts/cvtool.py status
.venv/bin/python scripts/cvtool.py verify
.venv/bin/python scripts/cvtool.py tablero list
```

Resto: `cvtool -h` (`scaffold`, `match`, `pack`, `ingest-jd` solo HTTPS público, `factcheck`, `validate-jd`, `render`, `copy`, `salary`, `respuestas`, `basename`, `init`, `test`, …).

Antes del match: `cvtool validate-jd path/jd.yaml`. Tras HITL: `cvtool match … --forzar`.

`render --familia` pisa `cv/` con el default. El PDF de una oferta vive en `candidaturas/<slug>/`.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| WeasyPrint / Pango | Libs del SO en [Instalación](#instalación) + `cvtool doctor` |
| PDF origen sin texto | Instala `pdftotext` o usa `curriculum.md` |
| Vault vacío | CV en `base/origen/` → **inicializa mi base** |
| `no_aplicar` | Lee `veredicto.yaml`; fuerza solo si aceptas el gap (`--forzar`) |
| PDF > 1 página | `cvtool pack --cv … --out … --gaps …` y vuelve a `render`/`verify` |
| `factcheck` no ok | Corrige métrica/tech/cliché/`evidencia_id`/`huerfanas`; no copies a `cv/` |
| `copy` bloquea | Falta factcheck ok o `pack_estado: aprobado` en `meta.yaml` (HITL) |

## FAQ

**¿Puedo usarlo sin Cursor?** Sí: pega el `SKILL.md` de la frase en el chat de otro agente ([AGENTS.md](../AGENTS.md)).

**¿Vault vacío / VACÍO en validate?** Pon el CV en `base/origen/` y di **inicializa mi base**.

**¿PDF origen sin texto?** Usa `curriculum.md` o un PDF con texto seleccionable + `pdftotext`.

**¿`no_aplicar`?** Lee gaps en `veredicto.yaml`. Solo `--forzar` si aceptas el riesgo.

**¿PDF de más de una página?** Ejecuta `cvtool pack` sobre el `cv.yaml` de la candidatura (con `--gaps`) y luego `cvtool render` + `verify`. Solo acorta a mano si el núcleo ya no cabe.

**¿Dónde está el historial?** `candidaturas/` + `tablero.yaml`.
