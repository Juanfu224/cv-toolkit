#!/usr/bin/env sh
# Smoke sin LLM: vault-minimo + oferta-demo → validate-jd → match → scaffold → render → verify.
# No modifica base/ del repo. Salida en un directorio temporal.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
else
  PY=python3
fi

export CV_TOOLKIT_ROOT="$ROOT"
"$PY" - <<'PY'
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ["CV_TOOLKIT_ROOT"])
sys.path.insert(0, str(ROOT / "scripts"))

from common import dump_yaml, load_yaml
from match import run_match
from render_cv import to_docx, to_markdown, to_pdf
from scaffold_defaults import scaffold
from validate_jd import validate_jd
from verify_pdf import extract
from pypdf import PdfReader

ej_vault = ROOT / "ejemplos" / "vault-minimo"
ej_jd = ROOT / "ejemplos" / "oferta-demo" / "jd.yaml"
if not ej_vault.is_dir() or not ej_jd.is_file():
    print("Faltan ejemplos/vault-minimo o ejemplos/oferta-demo/jd.yaml", file=sys.stderr)
    raise SystemExit(2)

jd = load_yaml(ej_jd)
errs = validate_jd(jd)
if errs:
    print("jd INVÁLIDO:", *errs, sep="\n  - ", file=sys.stderr)
    raise SystemExit(1)

tmpdir = Path(tempfile.mkdtemp(prefix="cvtoolkit-demo-"))
base = tmpdir / "base"
plantillas = tmpdir / "plantillas"
out = tmpdir / "out"
base.mkdir()
plantillas.mkdir()
out.mkdir()

for name in (
    "perfil.yaml",
    "evidencias.yaml",
    "skills.yaml",
    "familias.yaml",
    "constraints.yaml",
    "aliases.yaml",
):
    shutil.copy2(ej_vault / name, base / name)

print(f"tmpdir: {tmpdir}")
print("validate-jd: OK")

gaps, veredicto = run_match(jd, base_dir=base)
gaps_path = out / "gaps.yaml"
ver_path = out / "veredicto.yaml"
dump_yaml(gaps_path, gaps)
dump_yaml(ver_path, veredicto)
print(f"match: {veredicto['resultado']}  score_t1={veredicto['score_t1']}")
for m in veredicto.get("motivos") or []:
    print(f"  - {m}")

written = scaffold(base, plantillas)
cv_path = plantillas / "cv_default_dev.yaml"
if not cv_path.exists():
    print("scaffold no generó cv_default_dev.yaml", file=sys.stderr)
    raise SystemExit(1)
print(f"scaffold: {', '.join(p.name for p in written)}")

cv = load_yaml(cv_path)
perfil = load_yaml(base / "perfil.yaml")
cv["nombre"] = perfil["nombre"]
cv["contacto"] = perfil["contacto"]

(out / "curriculum.md").write_text(to_markdown(cv), encoding="utf-8")
pdf = out / "curriculum.pdf"
to_pdf(cv, pdf)
to_docx(cv, out / "curriculum.docx")
print(f"render: {pdf} ({pdf.stat().st_size} bytes)")

reader = PdfReader(str(pdf))
text = extract(pdf)
blob = text.lower()
errors = []
if len(reader.pages) > 1:
    errors.append(f"más de 1 página ({len(reader.pages)})")
if "@" not in blob:
    errors.append("sin email")
ciudad = str((perfil.get("contacto") or {}).get("ciudad") or "").lower()
if ciudad and ciudad not in blob:
    errors.append("sin ciudad")
if "perfil profesional" not in blob:
    errors.append("sin sección perfil")
if errors:
    print("verify: FAIL", *errors, sep="\n  - ", file=sys.stderr)
    raise SystemExit(1)
print(f"verify: OK  páginas={len(reader.pages)}")

print()
print("Demo OK. Artefactos:")
print(f"  {gaps_path}")
print(f"  {ver_path}")
print(f"  {pdf}")
print(f"  {out / 'curriculum.docx'}")
print()
print("Siguiente paso (tu CV real):")
print("  1. Copia curriculum.md o .pdf a base/origen/")
print("  2. Di «inicializa mi base» en tu agente")
print("  3. Pega una oferta en oferta/ y di «genera candidatura»")
print("  (Este tmpdir se puede borrar; no se tocó base/ del repo.)")
PY
