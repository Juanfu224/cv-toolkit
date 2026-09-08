from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml

REQUIRED_TOP = ("titulo", "empresa", "must_have", "keywords")
MODALIDADES = {"remoto", "hibrido", "presencial", None, ""}
FORMATOS = {"pdf", "docx", "cualquiera", None, ""}
SENIORITIES = {"junior", "mid", "senior", None, ""}


def validate_jd(jd: dict) -> list[str]:
    """Devuelve lista de errores; vacía = OK."""
    errors: list[str] = []
    if not isinstance(jd, dict) or not jd:
        return ["jd vacío o no es un objeto YAML"]

    for key in REQUIRED_TOP:
        if key not in jd or jd.get(key) in (None, "", []):
            errors.append(f"falta o vacío: {key}")

    titulo = jd.get("titulo")
    if isinstance(titulo, str) and len(titulo.strip()) < 3:
        errors.append("titulo demasiado corto")

    empresa = jd.get("empresa")
    if isinstance(empresa, str) and len(empresa.strip()) < 2:
        errors.append("empresa demasiado corta")

    modalidad = jd.get("modalidad")
    if modalidad not in MODALIDADES and modalidad is not None:
        errors.append(f"modalidad inválida: {modalidad!r}")

    formato = jd.get("formato_pedido")
    if formato not in FORMATOS and formato is not None:
        errors.append(f"formato_pedido inválido: {formato!r}")

    seniority = jd.get("seniority")
    if seniority not in SENIORITIES and seniority is not None:
        # allow free text but warn as error only if empty string weird — soft: ok
        pass

    kw = jd.get("keywords")
    if not isinstance(kw, dict):
        errors.append("keywords debe ser un objeto con t1/t2/t3")
    else:
        t1 = kw.get("t1")
        if not isinstance(t1, list) or len(t1) < 5:
            errors.append("keywords.t1 debe tener al menos 5 términos literales")
        elif any(not isinstance(x, str) or not x.strip() for x in t1):
            errors.append("keywords.t1 contiene términos vacíos")
        for tier in ("t2", "t3"):
            val = kw.get(tier)
            if val is not None and not isinstance(val, list):
                errors.append(f"keywords.{tier} debe ser lista")

    must = jd.get("must_have")
    if must is not None and not isinstance(must, list):
        errors.append("must_have debe ser lista")
    elif isinstance(must, list) and any(not isinstance(x, str) or not x.strip() for x in must):
        errors.append("must_have contiene ítems vacíos")

    anios = jd.get("anios_experiencia_min")
    if anios is not None and not isinstance(anios, (int, float)):
        errors.append("anios_experiencia_min debe ser número o null")

    certs = jd.get("certificaciones_obligatorias")
    if certs is not None and not isinstance(certs, list):
        errors.append("certificaciones_obligatorias debe ser lista")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida jd.yaml antes del match")
    parser.add_argument("jd", type=Path, help="Ruta a jd.yaml")
    args = parser.parse_args()
    if not args.jd.exists():
        print(f"ERROR: no existe {args.jd}", file=sys.stderr)
        return 1
    jd = load_yaml(args.jd)
    errors = validate_jd(jd)
    if errors:
        print(f"jd INVÁLIDO ({args.jd}):")
        for e in errors:
            print(f"  - {e}")
        return 1
    t1_n = len((jd.get("keywords") or {}).get("t1") or [])
    print(f"jd OK — t1={t1_n} must_have={len(jd.get('must_have') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
