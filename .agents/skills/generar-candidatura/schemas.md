# Schemas de artefactos

No inventar campos. Si un dato no está en el vault, `null` o `NECESITA_CONFIRMACION`.

## jd.yaml

Validar siempre con `cvtool validate-jd` (titulo, empresa, must_have, keywords.t1 ≥ 5).
Ingesta opcional: `cvtool ingest-jd --url …` (hosts públicos) o `--from-file` (fixtures). Host no allowlist → pegar texto.

```yaml
titulo: string
empresa: string
ciudad: string | null
modalidad: remoto | hibrido | presencial | null
seniority: junior | mid | senior | null
url: string | null
formato_pedido: pdf | docx | cualquiera
must_have: [string]
nice_to_have: [string]
keywords:
  t1: [string]   # título + 5–8 términos del anuncio
  t2: [string]   # stack
  t3: [string]   # blandas
knockouts: [string]
riesgos: [string]
anios_experiencia_min: int | null
certificaciones_obligatorias: [string]
preguntas:
  - pregunta: string
    limite: int | null
```

## veredicto.yaml

```yaml
resultado: aplicar | aplicar_con_reservas | no_aplicar
motivos: [string]
score_t1: float
cobertura_doble: float | null
forzar: bool
```

## plan.yaml

```yaml
familia: string   # id de base/familias.yaml
headline: string
perfil: string
evidencias_usar: [id]      # ordenadas de mayor a menor impacto para la oferta
evidencias_ocultar: [id]
t1_en_resumen: [string]    # T1 en prosa del perfil (encaje narrativo; no catálogo de tools)
t1_en_skills: [string]
t1_en_bullets: [string]    # T1 en bullets de experiencia/proyectos (no perfil/headline)
orden_secciones: [string]
mitigacion_gaps: string    # solo entrevista.md / analisis.md / chat HITL; nunca CV ni lead de presentación/respuestas
```

## cv.yaml

Ver `plantillas/cv_default_<familia>.yaml`. Cada bullet: `{texto, evidencia_id}`.
Competencias: 8–15 términos de esta oferta que existan en `base/skills.yaml`.
Headline: título de la oferta solo si está en `perfil.titulos_defendibles` o es un sinónimo honesto (nunca Senior/Arquitecto).
`perfil`: 2–4 frases de encaje (qué haces + 1–2 pruebas), no catálogo de tools/skills.
Bullets: verbo + contexto + resultado distinto (o alcance); una idea; sin eco acción→resultado.
Draft: puede ser generoso (hasta ~5 bullets/rol reciente); `cvtool pack` deja ≤1 página.

Certificaciones (canónico; `titulo` se acepta en lectura y se normaliza a `nombre`):

```yaml
certificaciones:
  - nombre: string          # obligatorio (no null/none/pendiente)
    entidad: string | null  # opcional
```

En `render` / `refresh` / `pack` (con perfil): las certs del PDF salen del vault normalizado, no de un subset inventado en `cv.yaml`.

## pack_report.yaml

Salida de `cvtool pack` (sin PII de contacto):

```yaml
t1: [string]
pages: int
pages_core: int
included: [{key, reason, score?}]
excluded: [{key, reason, score?}]
forced: [{key, reason}]
warnings: [string]
t1_missing_skills: [string]
t1_missing_bullets: [string]
```

`key` usa prefijos `skill:` o `bullet:<evidencia_id>`.

## meta.yaml (candidatura)

```yaml
empresa: string
puesto: string
fecha: YYYY-MM-DD
familia: string
veredicto: aplicar | aplicar_con_reservas | no_aplicar
listo_para_enviar: false
pack_estado: pendiente | aprobado | editado | rechazado
formato_envio: pdf | docx
```

`pack_estado` arranca en `pendiente` tras generar el pack. `cvtool copy` exige `aprobado` (salvo `--force`). Tras **editar** → `editado` y re-aprobación a `aprobado`.

## meta.yaml (oferta/)

```yaml
empresa: string | null
puesto: string | null
url: string | null
ciudad: string | null
fuente: string | null          # greenhouse | ashby | lever | texto
fecha: YYYY-MM-DD | null
formato_pedido: pdf | docx | cualquiera
equipo_receptor: string | null # solo si el anuncio o el humano lo nombra
```

## familias.yaml (vault)

```yaml
familias:
  - id: string
    nombre: string
    incluye_proyectos: bool
    salario:
      min: int
      max: int
    titulos_tipicos: [string]
```

LinkedIn y GitHub en `perfil.contacto` son opcionales.

## evidencias.yaml (vault)

`confianza` es opcional (`alta` | `media` | `pendiente`). No inventar métricas.

```yaml
evidencias:
  - id: string
    rol: string
    familias: [string]
    keywords: [string]
    situacion: string
    accion: string
    resultado: string
    fuente: string
    confianza: alta | media | pendiente   # opcional
```

## respuestas.md

Escribe `respuestas_data.yaml` y renderiza con `cvtool respuestas`:

```yaml
respuestas:
  - pregunta: string
    respuesta: string
    limite: int | null
    fuente: string
    necesita_confirmacion: bool
```

El helper rellena `caracteres` y aplica `plantillas/respuestas.md.j2`.

Render de empresa: `cvtool empresa --data empresa.yaml --out empresa.md`.

## empresa.yaml

Máximo 3 hechos con fuente URL. Cultura, premios o nombre de hiring manager **prohibidos** sin cita en el JD o `oferta/meta.yaml`. Render: `plantillas/empresa.md.j2`.

```yaml
empresa: string
sin_hechos_verificables: bool
hechos:
  - hecho: string
    fuente: string   # URL http(s)
stack_publico: [string]          # solo si aparece en fuente
equipo_receptor: string | null   # literal del JD o meta humana
```

Si no hay fuente: `sin_hechos_verificables: true` y `hechos: []`.

## presentacion.md

Tres párrafos listos para pegar (sin títulos markdown), ≤250 palabras. Intención: P1 gancho diferenciador (encaje JD + ángulo único del vault), P2 proof distinto al `cv.perfil`, P3 CTA vivo. Guía: `plantillas/presentacion.md.j2`. Factcheck `tono` también cubre CTA muerto, gap/formativo en el cuerpo y skills-dump.

## outreach.md

Borrador ≤80 palabras, 1 CTA, 1 destinatario. El humano copia a LinkedIn/email. Guía: `plantillas/outreach.md.j2`.

## factcheck.yaml

Salida de `cvtool factcheck` (sin PII de contacto):

```yaml
ok: bool
confianza: float   # claims soportados / total; 1.0 si no hay claims
presentacion_palabras: int | null
outreach_palabras: int | null
violaciones:
  - tipo: metrica | tecnologia | empleador | longitud | empresa | cliche | huerfana | evidencia_id | certificacion | tono | eco | perfil
    dato: string
    detalle: string
```

`ok: false` (métrica huérfana, `confianza < 1.0`, carta >250, outreach >80, certs `None` en curriculum, presentación que abre con «No tengo», eco en bullets, perfil = lista de competencias, presentación con CTA muerto / gap-en-carta / skills-dump) → no `copy`.
