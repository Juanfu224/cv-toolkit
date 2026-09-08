# Sistema de candidaturas 2026

Kit vacío para adaptar un CV ATS a cada oferta, con hechos en un vault YAML y un agente de Cursor que ejecuta el pipeline. **Tú envías** al portal. El sistema no autoaplica.

Mantén **este repositorio privado**: `base/` acaba conteniendo teléfono, email e historial laboral.

El match es por **tokens** (no subcadenas: `java` no cuenta como `javascript`). Un `must_have` ausente marca `no_aplicar`.


## Empezar

1. Crea tu copia (GitHub → **Use this template**) o clona el repo.
2. Dependencias:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

En Fedora, WeasyPrint necesita bibliotecas del sistema, por ejemplo:

```bash
sudo dnf install pango cairo gdk-pixbuf2 gcc python3-devel
```

3. Copia tu CV a [`base/origen/curriculum.md`](base/origen/curriculum.md) (preferible) o un PDF con texto seleccionable, y opcionalmente [`base/origen/presentacion.md`](base/origen/presentacion.md).
4. En Cursor: **inicializa mi base**.
5. Revisa `pendiente` / `NECESITA_CONFIRMACION`, luego:

```bash
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py validate
.venv/bin/python scripts/cvtool.py render --familia <id>
.venv/bin/python scripts/cvtool.py verify
```

`cvtool.py test` comprueba el motor; no usa tu vault.


## Cómo aplicar

1. Pega la oferta en [`oferta/descripcion.md`](oferta/descripcion.md) y las preguntas (si las hay) en [`oferta/preguntas.md`](oferta/preguntas.md).
2. En Cursor: **genera candidatura**.
3. Si el veredicto es `no_aplicar`, lee los motivos. Puedes forzar.
4. Revisa `veredicto.yaml`, `revision.md`, el PDF (texto seleccionable, orden correcto) y `entrevista.md`.
5. Envía **tú** el PDF o el DOCX de `cv/` o de `candidaturas/...` según pida el portal.
6. Di **registrar envío** para anotar fecha y seguimiento (+7 días) en `candidaturas/tablero.yaml`.

InfoJobs y similares: el PDF no sustituye rellenar el perfil de la plataforma. Conviene un perfil por familia alineado al vault.


## Qué genera

| Archivo | Uso |
|---|---|
| `cv/curriculum.pdf` | Último CV ATS (una columna) |
| `cv/curriculum.docx` | Mismo contenido para portales que piden Word |
| `cv/presentacion.md` | Carta lista para pegar |
| `cv/respuestas.md` | Respuestas del formulario |
| `candidaturas/YYYY-MM-DD_empresa_puesto/` | Copia congelada + análisis + briefing |
| `candidaturas/tablero.yaml` | Estados: borrador, enviada, entrevista, … |


## Carpetas

- `base/` — hechos inmutables. Origen archivado en `base/origen/`.
- `oferta/` — buzón; se pisa en cada oferta.
- `cv/` — última generación.
- `plantillas/` — HTML/CSS y, tras el scaffold, un `cv_default_<familia>.yaml` por familia.
- `scripts/` — match, render, verificación, salario, tablero, CLI (`cvtool.py`).

Para actualizar hechos (nueva fecha, métrica real, proyecto): **actualizar base**. El generador no toca el vault.


## CLI

```bash
.venv/bin/python scripts/cvtool.py init
.venv/bin/python scripts/cvtool.py status
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py validate
.venv/bin/python scripts/cvtool.py render --familia <id>
.venv/bin/python scripts/cvtool.py verify
.venv/bin/python scripts/cvtool.py basename --puesto "Puesto" --empresa "Empresa"
.venv/bin/python scripts/cvtool.py salary --familia <id>
.venv/bin/python scripts/cvtool.py salary --familia <id> --oferta-min 30000 --oferta-max 33000
.venv/bin/python scripts/cvtool.py tablero list
.venv/bin/python scripts/cvtool.py test
```


## Familias

Las declara `base/familias.yaml` (ids, banda salarial, si el CV junior incluye Proyectos). El init las pregunta. No hay familias fijas: desarrollo, soporte, datos u otras caben si el vault las define.
