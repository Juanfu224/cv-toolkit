---
name: inicializar-base
description: >-
  Inicializa el vault vacío en base/ a partir del CV y la presentación en
  base/origen/. Extrae hechos a YAML (perfil, evidencias STAR, skills,
  familias, constraints) sin inventar. Usar cuando el usuario dice
  inicializa mi base, rellena el vault, carga mi curriculum o es el
  primer uso del kit.
---

# Inicializar base

El kit llega vacío (`PENDIENTE`). No generes candidaturas aquí. No inventes empleadores, fechas, métricas, tecnologías ni certificaciones.

```bash
PY=".venv/bin/python"
[ -x "$PY" ] || PY=python3
```

## Checklist

```
- [ ] 1 Origen presente
- [ ] 2 Preguntar lo que el origen no dice
- [ ] 3 Escribir YAML del vault
- [ ] 4 Scaffold + validate
- [ ] 5 Render + verify de una familia
```

## 1. Origen

Ejecuta `$PY scripts/cvtool.py init`.

Si falta `base/origen/curriculum.md` y `curriculum.pdf`: **para** y pide esos archivos (y `presentacion.md` si la hay).

Lee todo el origen. Un PDF solo si el texto es extraíble (`pdftotext` de poppler, o el texto embebido del archivo). Si falta `pdftotext` en el SO y el PDF no se puede leer: pide `curriculum.md` o que instalen poppler. Si es un escaneo sin texto: para.

## 2. Preguntar (no adivinar)

Si el origen no lo deja claro, pregunta antes de escribir:

- Ciudad / disposición a remoto, híbrido, presencial y traslado
- Familias de puesto que persigue (ids cortos: `dev`, `soporte`, `datos`, …). Mínimo una.
- Banda salarial bruta anual por familia
- Preaviso en días
- Títulos que **sí** puede defender (nunca Senior / Arquitecto / Lead / Manager si no está en el origen)
- LinkedIn y GitHub opcionales; si existen, URL completa (nunca bit.ly)

Campos dudosos: lista `pendiente` o `NECESITA_CONFIRMACION`. No rellenes con un valor inventado.

## 3. Escribir `base/`

Parte de los YAML actuales. Conserva `base/aliases.yaml` (diccionario genérico) y añade solo sinónimos que salgan del origen.

- `perfil.yaml`: nombre, contacto, `headline_base`, `titulos_defendibles`, idiomas, educacion, experiencia (con `id` estable tipo `empresa-corta`), proyectos, certificaciones (`nombre` + `entidad` opcional; no uses `titulo` ni `null`). Roles con `familias: [id, …]`.
- `evidencias.yaml`: mínimo 8 STAR si el origen da para ello. Cada una: `id`, `rol` (id de experiencia o proyecto), `familias`, `keywords`, `situacion`, `accion`, `resultado`, `fuente: origen/curriculum.md`. `confianza` opcional (`alta` / `media` / `pendiente`). Sin `%` ni números que no estén en el origen.
- `skills.yaml`: nivel `diario` | `proyecto` | `formativo` y `familias`.
- `familias.yaml`: por cada familia, `id`, `nombre`, `incluye_proyectos` (junior: true en desarrollo, false en soporte salvo que el usuario diga lo contrario), `salario.min/max`, `titulos_tipicos`.
- `constraints.yaml`: ubicación, `traslado_confirmado`, preaviso, knockouts de seniority, `anios_experiencia_max_aceptados` si el usuario lo acota.
- Copia el origen a `base/origen/` si aún no está. **No reescribas** el CV original.

Verbos de evidencia: acción concreta + herramienta. Prohibido «responsable de», «colaboré en», «apasionado por».

## 4. Scaffold y validate

```bash
$PY scripts/cvtool.py scaffold
$PY scripts/cvtool.py validate
```

WARN de `pendiente`: continúa. ERROR: corrige el YAML y repite. No toques `plantillas/cv.html.j2` ni `cv.css`.

## 5. Humo ATS

```bash
$PY scripts/cvtool.py render --familia <primera-familia>
$PY scripts/cvtool.py verify
$PY scripts/cvtool.py doctor
$PY scripts/cvtool.py status
```

Si `cvtool verify` falla, arregla el default de esa familia y vuelve a renderizar.

En el chat: qué se extrajo, qué quedó `pendiente`, y que el siguiente paso es pegar una oferta y decir **genera candidatura**.
