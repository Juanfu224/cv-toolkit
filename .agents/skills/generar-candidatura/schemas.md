# Schemas de artefactos

No inventar campos. Si un dato no está en el vault, `null` o `NECESITA_CONFIRMACION`.

## jd.yaml

Validar siempre con `cvtool validate-jd` (titulo, empresa, must_have, keywords.t1 ≥ 5).

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
evidencias_usar: [id]
evidencias_ocultar: [id]
t1_en_resumen: [string]
t1_en_skills: [string]
t1_en_bullets: [string]
orden_secciones: [string]
mitigacion_gaps: string
```

## cv.yaml

Ver `plantillas/cv_default_<familia>.yaml`. Cada bullet: `{texto, evidencia_id}`.
Competencias: 8–15 términos de esta oferta que existan en `base/skills.yaml`.
Headline: título de la oferta solo si está en `perfil.titulos_defendibles` o es un sinónimo honesto (nunca Senior/Arquitecto).

## meta.yaml (candidatura)

```yaml
empresa: string
puesto: string
fecha: YYYY-MM-DD
familia: string
veredicto: aplicar | aplicar_con_reservas | no_aplicar
listo_para_enviar: false
formato_envio: pdf | docx
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

## empresa.md

Máximo 3 hechos con fuente URL. Si no hay fuente, el archivo dice `sin_hechos_verificables: true`.
