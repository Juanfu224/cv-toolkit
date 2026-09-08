# CV Toolkit

Adapta un CV **ATS de una columna** a cada oferta, con hechos en un vault YAML y un agente de Cursor. **Tú envías** al portal. No autoaplica ni inventa experiencia.

Mantén **tu copia privada**: `base/` acaba con teléfono, email e historial. Licencia: [MIT](LICENSE).


## Empezar

Python **3.10+** y Cursor.

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

1. Copia tu CV a [`base/origen/curriculum.md`](base/origen/curriculum.md) (o PDF con texto seleccionable).
2. En Cursor: **inicializa mi base**.
3. Pega la oferta en [`oferta/descripcion.md`](oferta/descripcion.md) → **genera candidatura**.
4. Envía tú el PDF/DOCX de `cv/` o `candidaturas/…`.
5. Di **registrar envío**.

¿Sin CV a mano? Prueba con datos ficticios: [`ejemplos/`](ejemplos/README.md).


## Frases en Cursor

| Cuándo | Escribe |
|---|---|
| Primera vez | **inicializa mi base** |
| Oferta en `oferta/` | **genera candidatura** |
| Ya enviaste | **registrar envío** |
| Cambió un hecho | **actualizar base** |

Si el veredicto es `no_aplicar`, para; puedes forzar.


## Qué obtienes

| Archivo | Uso |
|---|---|
| `cv/curriculum.pdf` / `.docx` | Último CV ATS |
| `cv/CV_Nombre_Puesto_Empresa.*` | Nombre de envío |
| `cv/presentacion.md` | Carta |
| `candidaturas/YYYY-MM-DD_…/` | Pack congelado + briefing |
| `candidaturas/tablero.yaml` | Seguimiento |

El PDF no sustituye el perfil de InfoJobs u otros portales.


## ATS y límites

- Una columna, texto seleccionable, contacto en el cuerpo, PDF + DOCX.
- Hechos solo del vault. `no_aplicar` si falta un `must_have`, T1 bajo, seniority en knockouts, presencial fuera de zona sin traslado, o certs ausentes.


## Carpetas

`base/` hechos · `oferta/` buzón · `cv/` última generación · `candidaturas/` historial · `plantillas/` ATS · `ejemplos/` demo · `scripts/cvtool.py` CLI.


## CLI avanzada

```bash
.venv/bin/python scripts/cvtool.py doctor
.venv/bin/python scripts/cvtool.py status
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py render --familia <id>
.venv/bin/python scripts/cvtool.py verify
.venv/bin/python scripts/cvtool.py tablero list
.venv/bin/python scripts/cvtool.py test
```

Resto: `cvtool -h` (`match`, `copy`, `salary`, `respuestas`, `basename`, …).

`render --familia` pisa `cv/` con el default. El PDF de una oferta vive en `candidaturas/<slug>/`.


## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| WeasyPrint / Pango | Libs del SO arriba + `cvtool doctor` |
| Vault vacío | CV en `base/origen/` → **inicializa mi base** |
| `no_aplicar` | Lee `veredicto.yaml`; fuerza solo si aceptas el gap |
| PDF > 1 página | Recorta `cv.yaml` y vuelve a renderizar |

Agente: [`AGENTS.md`](AGENTS.md).
