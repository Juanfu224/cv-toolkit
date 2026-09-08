# Ejemplos

Datos **ficticios** para probar el kit sin meter tu CV.

## Smoke automático (recomendado)

No toca tu `base/`. Corre match + render + verify en un directorio temporal:

```bash
sh scripts/demo_smoke.sh
```

## Vault mínimo (manual, pisa `base/`)

Solo si quieres dejar el vault de demo en el kit (luego restaura con `git checkout -- base/`):

```bash
cp -r ejemplos/vault-minimo/. base/
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py doctor
.venv/bin/python scripts/cvtool.py render --familia dev
.venv/bin/python scripts/cvtool.py verify
```

## Oferta demo → agente

Copia solo el buzón (no copies `jd.yaml` a `oferta/`; el skill lo genera en `candidaturas/`):

```bash
cp ejemplos/oferta-demo/descripcion.md oferta/descripcion.md
cp ejemplos/oferta-demo/preguntas.md oferta/preguntas.md
cp ejemplos/oferta-demo/meta.yaml oferta/meta.yaml
```

Con el vault cargado (demo o el tuyo), di **genera candidatura**.

Match manual con el `jd.yaml` de ejemplo (sin agente):

```bash
.venv/bin/python scripts/cvtool.py validate-jd ejemplos/oferta-demo/jd.yaml
.venv/bin/python scripts/cvtool.py match --jd ejemplos/oferta-demo/jd.yaml --base base
```
