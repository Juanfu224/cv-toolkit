# Ejemplos

Datos **ficticios** para probar el kit sin meter tu CV.

## Vault mínimo

```bash
cp -r ejemplos/vault-minimo/* base/
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py doctor
.venv/bin/python scripts/cvtool.py render --familia dev
.venv/bin/python scripts/cvtool.py verify
```

Para volver al kit vacío: restaura `base/*.yaml` a `PENDIENTE` / listas vacías (o `git checkout -- base/`).

## Oferta demo

```bash
cp ejemplos/oferta-demo/descripcion.md oferta/descripcion.md
cp ejemplos/oferta-demo/preguntas.md oferta/preguntas.md
cp ejemplos/oferta-demo/meta.yaml oferta/meta.yaml
```

Luego en Cursor: **genera candidatura** (con el vault de ejemplo ya cargado).
