from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml, norm
from paths import BASE


def extract(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprueba el orden de lectura del PDF")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, help="Guarda el texto extraído")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"no existe {args.pdf}")

    perfil = load_yaml(BASE / "perfil.yaml")
    nombre = norm(perfil.get("nombre") or "")
    ciudad = norm((perfil.get("contacto") or {}).get("ciudad") or "")

    reader = PdfReader(str(args.pdf))
    text = extract(args.pdf)
    blob = " ".join(text.lower().split())
    if args.out:
        args.out.write_text(text, encoding="utf-8")

    errors: list[str] = []
    if len(reader.pages) > 1:
        errors.append(f"más de 1 página ({len(reader.pages)})")

    expected = [nombre, "perfil profesional", "competencias", "experiencia"]
    cursor = 0
    for needle in expected:
        idx = blob.find(needle, cursor)
        if idx < 0:
            errors.append(f"no aparece en orden {needle!r}")
        else:
            cursor = idx + len(needle)

    if ciudad and ciudad not in blob:
        errors.append("no aparece la ciudad en el cuerpo")
    elif ciudad and blob.find(ciudad) > blob.find("perfil profesional"):
        errors.append("la ciudad no está en el bloque de contacto")

    if "@" not in blob:
        errors.append("no aparece email")

    if errors:
        print("verify_pdf: FAIL")
        for e in errors:
            print(f"  - {e}")
        preview = text[:500].replace("\n", " | ")
        print(f"extracto: {preview}")
        return 1

    print("verify_pdf: OK")
    print(f"páginas: {len(reader.pages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
