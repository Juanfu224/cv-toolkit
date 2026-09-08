from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FILES = [
    "cv.yaml",
    "curriculum.md",
    "curriculum.pdf",
    "curriculum.docx",
    "presentacion.md",
    "respuestas.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Copia la candidatura a cv/")
    parser.add_argument("--from-dir", required=True, type=Path)
    parser.add_argument("--to-dir", required=True, type=Path)
    args = parser.parse_args()
    src = args.from_dir
    dest = args.to_dir
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
