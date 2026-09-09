from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml, norm
from paths import BASE, is_allowed_output


def extract(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def verify_ats(pdf: Path, perfil: dict | None = None) -> list[str]:
    """Devuelve lista de errores ATS (vacía = OK)."""
    if perfil is None:
        perfil = load_yaml(BASE / "perfil.yaml")
    nombre = norm(perfil.get("nombre") or "")
    ciudad = norm((perfil.get("contacto") or {}).get("ciudad") or "")

    reader = PdfReader(str(pdf))
    text = extract(pdf)
    blob = " ".join(text.lower().split())

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
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprueba el orden de lectura del PDF")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, help="Guarda el texto extraído")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"no existe {args.pdf}")

    if args.out:
        if not is_allowed_output(args.out):
            raise SystemExit("--out fuera del repo o tmp")
        args.out.write_text(extract(args.pdf), encoding="utf-8")

    errors = verify_ats(args.pdf)
    reader = PdfReader(str(args.pdf))

    if errors:
        print("verify_pdf: FAIL")
        for e in errors:
            print(f"  - {e}")
        print(f"páginas: {len(reader.pages)}  (extracto omitido: PII)")
        return 1

    print("verify_pdf: OK")
    print(f"páginas: {len(reader.pages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
