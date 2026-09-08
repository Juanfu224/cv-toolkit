---
name: registrar-envio
description: >-
  Marca una candidatura como enviada (u otro estado) en el tablero de
  seguimiento. Usar cuando el usuario dice registrar envío, ya lo envié,
  el pack está listo, pasé a entrevista, me rechazaron, o actualiza el
  estado de una oferta.
---

# Registrar envío

El sistema no envía a portales. Esto solo actualiza `candidaturas/tablero.yaml` y `meta.yaml` de la carpeta.

```bash
PY=".venv/bin/python"
[ -x "$PY" ] || PY=python3
CVTOOL="$PY scripts/cvtool.py"
```

## 1. Identificar la candidatura

- Si el usuario nombra empresa/puesto: usa esa carpeta `candidaturas/YYYY-MM-DD_empresa_puesto/`.
- Si no: la más reciente, confirmando en el chat.

Estados válidos: `borrador`, `listo`, `enviada`, `entrevista`, `oferta`, `rechazada`, `descartada`.

- Pack revisado, aún no enviado → `listo` y `listo_para_enviar: true` en `meta.yaml`.
- Tras un envío humano → `enviada`. Fecha de envío = hoy (sistema) salvo que indiquen otra.

No reescribas el CV.

## 2. Actualizar archivos

Pack listo (PDF/DOCX confirmados, sin enviar):

```bash
$CVTOOL tablero set --slug "<slug>" --estado listo \
  --empresa "<Empresa>" --puesto "<Puesto>"
```

Ya enviado:

```bash
$CVTOOL tablero set --slug "<slug>" --estado enviada \
  --empresa "<Empresa>" --puesto "<Puesto>" --enviada YYYY-MM-DD
```

El script calcula seguimiento a +7 días. Si el usuario pide otra fecha, pásala con `--seguimiento`.

Otros estados: mismo comando con `--estado entrevista|oferta|rechazada|descartada`.

Si existe `candidaturas/<slug>/meta.yaml`, `tablero set` con estado `listo` o `enviada` pone solo `listo_para_enviar: true`. No hace falta editar `meta.yaml` a mano.

## 3. Chat

Confirma slug, estado, fecha de envío y fecha de seguimiento. Lista otras filas con seguimiento vencido si las hay (`$CVTOOL tablero list`).
