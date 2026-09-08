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

1. CV en [`base/origen/`](../base/origen/) (`curriculum.md` preferido).
2. **inicializa mi base** (agente).
3. Oferta en [`oferta/descripcion.md`](../oferta/descripcion.md) → **genera candidatura**.
4. Revisa `cv/` y el pack en `candidaturas/YYYY-MM-DD_…/`.
5. Envías tú al portal → **registrar envío**.

Sin CV propio: [`ejemplos/`](../ejemplos/README.md) o `sh scripts/demo_smoke.sh`.

## Bucle diario

1. Pega la oferta nueva en `oferta/` (pisar el buzón está bien).
2. **genera candidatura**.
3. Revisa veredicto, PDF/DOCX y presentación.
4. Envía al portal (InfoJobs, LinkedIn, email…).
5. **registrar envío**.

Si cambió un hecho real (salario, proyecto, skill): **actualizar base** antes de la siguiente oferta.

## Veredicto y `--forzar`

Tras el match, lee `candidaturas/<slug>/veredicto.yaml`:

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

## Qué enviar al portal

- PDF/DOCX de `cv/` (última generación) o del pack en `candidaturas/<slug>/`.
- Carta: `cv/presentacion.md` (o la del pack).
- El PDF **no** sustituye el perfil de InfoJobs u otros portales: rellena el formulario del portal aparte.

## ATS y límites

- Una columna, texto seleccionable, contacto en el cuerpo, PDF + DOCX.
- Hechos solo del vault. `no_aplicar` si falta un `must_have`, T1 bajo, seniority en knockouts, presencial fuera de zona sin traslado, o certs ausentes.

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

Resto: `cvtool -h` (`scaffold`, `match`, `validate-jd`, `render`, `copy`, `salary`, `respuestas`, `basename`, `init`, `test`, …).

Antes del match: `cvtool validate-jd path/jd.yaml`. Tras HITL: `cvtool match … --forzar`.

`render --familia` pisa `cv/` con el default. El PDF de una oferta vive en `candidaturas/<slug>/`.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| WeasyPrint / Pango | Libs del SO en [Instalación](#instalación) + `cvtool doctor` |
| PDF origen sin texto | Instala `pdftotext` o usa `curriculum.md` |
| Vault vacío | CV en `base/origen/` → **inicializa mi base** |
| `no_aplicar` | Lee `veredicto.yaml`; fuerza solo si aceptas el gap (`--forzar`) |
| PDF > 1 página | Recorta `cv.yaml` y vuelve a renderizar |

## FAQ

**¿Puedo usarlo sin Cursor?** Sí: pega el `SKILL.md` de la frase en el chat de otro agente ([AGENTS.md](../AGENTS.md)).

**¿Vault vacío / VACÍO en validate?** Pon el CV en `base/origen/` y di **inicializa mi base**.

**¿PDF origen sin texto?** Usa `curriculum.md` o un PDF con texto seleccionable + `pdftotext`.

**¿`no_aplicar`?** Lee gaps en `veredicto.yaml`. Solo `--forzar` si aceptas el riesgo.

**¿PDF de más de una página?** Recorta bullets en `cv.yaml` y `cvtool render` de nuevo.

**¿Dónde está el historial?** `candidaturas/` + `tablero.yaml`.
