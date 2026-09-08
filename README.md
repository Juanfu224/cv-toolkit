# CV Toolkit

Adapta un CV **ATS de una columna** a cada oferta, con hechos en un vault YAML y un agente de Cursor que ejecuta el pipeline. **Tú envías** al portal. El sistema no autoaplica ni inventa experiencia.

Mantén **tu copia privada**: `base/` acaba conteniendo teléfono, email e historial laboral. Licencia del código: [MIT](LICENSE).


## Cómo se usa

Cuatro frases en Cursor, en este orden:

| Cuándo | Escribe |
|---|---|
| Primera vez, con tu CV en `base/origen/` | **inicializa mi base** |
| Oferta pegada en `oferta/` | **genera candidatura** |
| Ya enviaste al portal | **registrar envío** |
| Cambió un hecho (fecha, métrica, proyecto) | **actualizar base** |

El generador no toca el vault. Si el veredicto es `no_aplicar`, para; puedes forzar.


## Qué obtienes

| Archivo | Uso |
|---|---|
| `cv/curriculum.pdf` | Último CV ATS (una columna, texto seleccionable) |
| `cv/curriculum.docx` | Mismo contenido para portales que piden Word |
| `cv/CV_Nombre_Puesto_Empresa.pdf` | Nombre de envío (también `.docx`) |
| `cv/presentacion.md` | Carta lista para pegar |
| `cv/respuestas.md` | Respuestas del formulario, si las hubo |
| `candidaturas/YYYY-MM-DD_empresa_puesto/` | Copia congelada + análisis + briefing |
| `candidaturas/tablero.yaml` | Estados: borrador, listo, enviada, entrevista, … |

InfoJobs y similares: el PDF no sustituye rellenar el perfil de la plataforma.


## Empezar

Python **3.10+**. Cursor para las frases de arriba.

1. Clona el repo (cópialo a un remoto **privado**).
2. Dependencias:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

WeasyPrint necesita bibliotecas del sistema:

```bash
# Fedora
sudo dnf install pango cairo gdk-pixbuf2 gcc python3-devel

# Debian / Ubuntu
sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 gcc python3-dev

# macOS (Homebrew)
brew install pango cairo gdk-pixbuf
```

3. Copia tu CV a [`base/origen/curriculum.md`](base/origen/curriculum.md) (preferible) o un PDF con texto seleccionable. Opcional: [`base/origen/presentacion.md`](base/origen/presentacion.md).
4. En Cursor: **inicializa mi base**. Revisa `pendiente` / `NECESITA_CONFIRMACION`.
5. Comprueba:

```bash
.venv/bin/python scripts/cvtool.py status
.venv/bin/python scripts/cvtool.py validate
```

`cvtool.py init` solo mira si hay CV en `base/origen/`; no rellena el vault. `cvtool.py test` comprueba el motor y no usa tus datos.

Luego pega la oferta en [`oferta/descripcion.md`](oferta/descripcion.md) (preguntas en [`oferta/preguntas.md`](oferta/preguntas.md)) y di **genera candidatura**. Revisa `veredicto.yaml`, `revision.md`, el PDF y `entrevista.md`. Envía **tú** el archivo. Di **registrar envío**.


## ATS 2026

- Una columna, sin tablas ni iconos. Contacto en el cuerpo, no en cabecera.
- PDF con texto seleccionable y DOCX. `cvtool verify` comprueba orden de lectura y una página.
- Competencias 8–15 alineadas a la oferta; keywords del anuncio solo si están en el vault.
- Si el portal pide Word, envía el `.docx`. Si no indica formato, PDF.


## Cuándo no aplicar

El match es por **tokens** (`java` no cuenta como `javascript`). Marca `no_aplicar` si:

- falta un `must_have`
- cobertura T1 por debajo del 40 %
- el anuncio pide un seniority de `constraints.yaml` (por defecto: senior, lead, architect, manager)
- es presencial fuera de tu zona y no hay traslado confirmado
- pide certificaciones que no están en el vault

Esos knockouts se ajustan al inicializar la base. Un `must_have` ausente no se finge en el CV.


## Carpetas

- `base/` — hechos inmutables. Origen archivado en `base/origen/`.
- `oferta/` — buzón; se pisa en cada oferta.
- `cv/` — última generación (no commitees PDFs).
- `plantillas/` — HTML/CSS ATS. Tras el scaffold: `cv_default_<familia>.yaml`.
- `scripts/` — CLI unificada: `cvtool.py`.


## CLI

Tras inicializar, el humo de una familia es:

```bash
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py render --familia <id>
.venv/bin/python scripts/cvtool.py verify
```

Eso pisa `cv/` con el default de esa familia. El PDF de una oferta concreta vive en `candidaturas/<slug>/` (y otra vez en `cv/` al terminar **genera candidatura**). No vuelvas a `render --familia` si quieres conservar el último envío.

```bash
.venv/bin/python scripts/cvtool.py init
.venv/bin/python scripts/cvtool.py status
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py validate
.venv/bin/python scripts/cvtool.py render --familia <id>
.venv/bin/python scripts/cvtool.py render --cv candidaturas/<slug>/cv.yaml --out-dir candidaturas/<slug>
.venv/bin/python scripts/cvtool.py verify
.venv/bin/python scripts/cvtool.py match --jd candidaturas/<slug>/jd.yaml --out gaps.yaml --veredicto veredicto.yaml
.venv/bin/python scripts/cvtool.py copy --from-dir candidaturas/<slug>
.venv/bin/python scripts/cvtool.py basename --puesto "Puesto" --empresa "Empresa"
.venv/bin/python scripts/cvtool.py salary --familia <id>
.venv/bin/python scripts/cvtool.py salary --familia <id> --oferta-min 30000 --oferta-max 33000
.venv/bin/python scripts/cvtool.py tablero list
.venv/bin/python scripts/cvtool.py test
```

Las familias las declara `base/familias.yaml` (ids, banda salarial, si el CV incluye Proyectos). El init las pregunta. No hay familias fijas.


## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| WeasyPrint / Pango / cairo | Instala las bibliotecas del SO de arriba y reintenta el render |
| `validate_base: VACÍO` | Copia el CV a `base/origen/` y di **inicializa mi base** |
| `no_aplicar` | Lee `motivos` en `veredicto.yaml`. Fuerza solo si aceptas el gap |
| PDF de más de 1 página | Recorta bullets/skills en `cv.yaml` y vuelve a renderizar |
| PDF sin texto seleccionable | No uses un escaneo. El origen y el render deben ser texto real |

El mapa del agente está en [`AGENTS.md`](AGENTS.md).
