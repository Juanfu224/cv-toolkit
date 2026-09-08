from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml
from paths import is_allowed_output

FILES = [
    "cv.yaml",
    "curriculum.md",
    "curriculum.pdf",
    "curriculum.docx",
    "presentacion.md",
    "respuestas.md",
    "outreach.md",
]


def factcheck_blocks(src: Path) -> str | None:
    fc = src / "factcheck.yaml"
    if not fc.exists():
        return "falta factcheck.yaml; corre cvtool factcheck antes de copy"
    data = load_yaml(fc)
    if data.get("ok") is not True:
        return "factcheck no ok; no copiar a cv/"
    return None


def pack_estado_blocks(src: Path) -> str | None:
    meta_path = src / "meta.yaml"
    if not meta_path.exists():
        return "falta meta.yaml con pack_estado: aprobado; aprueba el pack antes de copy"
    meta = load_yaml(meta_path)
    if not isinstance(meta, dict):
        return "meta.yaml inválido; pack_estado debe ser aprobado"
    estado = meta.get("pack_estado")
    if estado != "aprobado":
        return (
            f"pack_estado={estado!r}; copy solo con pack_estado: aprobado "
            "(HITL: aprobar / editar / rechazar)"
        )
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Copia la candidatura a cv/")
    parser.add_argument("--from-dir", required=True, type=Path)
    parser.add_argument("--to-dir", required=True, type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Omite factcheck y pack_estado (HITL explícito)",
    )
    parser.add_argument(
        "--require-factcheck",
        action="store_true",
        help=argparse.SUPPRESS,  # compat: ya es el comportamiento por defecto
    )
    args = parser.parse_args()
    src = args.from_dir
    dest = args.to_dir
    if not args.force:
        block = factcheck_blocks(src)
        if block:
            raise SystemExit(block)
        block = pack_estado_blocks(src)
        if block:
            raise SystemExit(block)
    if not is_allowed_output(src) or not is_allowed_output(dest):
        raise SystemExit("from-dir/to-dir fuera del repo o tmp")
    dest.mkdir(parents=True, exist_ok=True)
    for stale in (
        list(dest.glob("CV_*.pdf"))
        + list(dest.glob("CV_*.docx"))
        + list(dest.glob("CV_*.md"))
    ):
        stale.unlink()
        print(f"eliminado {stale.name}")
    copied = 0
    for name in FILES:
        f = src / name
        if f.exists():
            shutil.copy2(f, dest / name)
            print(f"copiado {name}")
            copied += 1
    named = list(src.glob("CV_*.pdf")) + list(src.glob("CV_*.docx")) + list(src.glob("CV_*.md"))
    for f in named:
        shutil.copy2(f, dest / f.name)
        print(f"copiado {f.name}")
        copied += 1
    if copied == 0:
        raise SystemExit("no había archivos para copiar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
