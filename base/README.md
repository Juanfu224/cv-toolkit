# Vault (`base/`)

Hechos inmutables del candidato. El generador **no inventa** métricas, empleadores, fechas ni tecnologías.

| Archivo | Qué contiene |
|---|---|
| `perfil.yaml` | Identidad, contacto, educación, roles, proyectos |
| `evidencias.yaml` | Historias STAR (`id`, `rol`, `accion`, `keywords`) |
| `skills.yaml` | Inventario con nivel `diario` / `proyecto` / `formativo` |
| `familias.yaml` | Familias de puesto (ids, salario, si hay Proyectos) |
| `constraints.yaml` | Ubicación, preaviso, knockouts |
| `aliases.yaml` | Sinónimos oferta → término del vault |
| `origen/` | CV y presentación originales. No editar tras el init. |

## Cómo rellenar

1. Copia tu `curriculum.md` (o un PDF extraíble) y `presentacion.md` a `origen/`.
2. En Cursor: **inicializa mi base**.
3. Revisa campos `pendiente` y `NECESITA_CONFIRMACION`.
4. `.venv/bin/python scripts/cvtool.py scaffold && .venv/bin/python scripts/cvtool.py validate`.
