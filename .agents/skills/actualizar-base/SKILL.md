---
name: actualizar-base
description: >-
  Actualiza el vault inmutable en base/ con hechos nuevos (fecha, métrica
  real, proyecto, skill, constraint). Usar cuando el usuario dice
  actualizar base, nueva evidencia, cambió mi salario, añadí un proyecto
  o corrige un pendiente del vault. No genera candidaturas.
---

# Actualizar base

Único camino para editar `base/` después del init. No inventes. Si el hecho no está en un documento o en lo que el usuario acaba de afirmar, `pendiente` o `NECESITA_CONFIRMACION`.

```bash
PY=".venv/bin/python"
[ -x "$PY" ] || PY=python3
```

## Qué tocar

Cambia **solo** los archivos necesarios:

- Nueva fecha / tipo de contrato / centro → `perfil.yaml` y quita esa clave de `pendiente`
- Nueva métrica o historia → `evidencias.yaml` (nuevo `id`, `fuente` explícita)
- Nueva herramienta → `skills.yaml` + alias en `aliases.yaml` si el anuncio la nombra de otra forma
- Ciudad, remoto, preaviso, banda, knockouts → `constraints.yaml` y/o `familias.yaml`
- Nuevo rol o proyecto → `id` nuevo en `perfil.yaml` y evidencias ligadas a ese `id`

No reescribas `base/origen/` salvo que el usuario sustituya el CV original a propósito.

## Después

```bash
$PY scripts/cvtool.py scaffold
$PY scripts/cvtool.py validate
```

WARN de `pendiente` está bien. ERROR: corrige y repite.

Di qué ids cambiaste. No regeneres candidaturas antiguas salvo que el usuario lo pida.
