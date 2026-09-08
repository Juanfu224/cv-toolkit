# Agentes

Raíz: carpeta con `base/` y `oferta/`. Python: `.venv/bin/python` si existe.
Usuario primero: `cvtool doctor`. El agente ejecuta skills; no improvisa PDFs.

## Skills

| Frase del usuario | Skill |
|---|---|
| inicializa mi base | `.cursor/skills/inicializar-base/SKILL.md` |
| genera candidatura | `.cursor/skills/generar-candidatura/SKILL.md` |
| actualizar base | `.cursor/skills/actualizar-base/SKILL.md` |
| registrar envío | `.cursor/skills/registrar-envio/SKILL.md` |

## Reglas

- Hechos solo en `base/`. Cero invención de métricas, empresas, fechas o tecnologías.
- No editar `base/` salvo los dos skills de vault.
- No enviar a portales.
- `no_aplicar` → parar salvo que el usuario fuerce.
- Basename: `scripts/cvtool.py basename`. Familias: `base/familias.yaml`.
- CLI: `scripts/cvtool.py` (doctor, match, render, verify, salary, tablero, copy, respuestas).

Detalle de artefactos: `.cursor/skills/generar-candidatura/schemas.md`.
