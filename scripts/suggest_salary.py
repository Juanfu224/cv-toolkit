from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml
from familias import load_familias
from paths import BASE


def _band(familia: str, constraints: dict | None, base: Path | None) -> tuple[dict, str]:
    familias = load_familias(base)
    if familia in familias:
        salario = (familias[familia].get("salario") or {})
        if "min" in salario and "max" in salario:
            return {"min": int(salario["min"]), "max": int(salario["max"])}, "familias"
    constraints = constraints or load_yaml((base or BASE) / "constraints.yaml")
    salario = constraints.get("salario") or {}
    band = salario.get(familia)
    if not isinstance(band, dict) or "min" not in band or "max" not in band:
        raise SystemExit(f"falta salario para familia {familia!r} (familias.yaml o constraints.yaml)")
    return {"min": int(band["min"]), "max": int(band["max"])}, "constraints"


def _fmt(min_eur: int, max_eur: int) -> str:
    return f"{min_eur:,}–{max_eur:,} € brutos anuales".replace(",", ".")


def suggest_salary(
    familia: str,
    oferta_min: int | None = None,
    oferta_max: int | None = None,
    constraints: dict | None = None,
    base: Path | None = None,
) -> dict:
    root = base or BASE
    constraints = constraints or load_yaml(root / "constraints.yaml")
    salario = constraints.get("salario") or {}
    band, fuente_banda = _band(familia, constraints, root)
    alinear = bool(salario.get("alinear_a_rango_publicado"))

    result: dict = {
        "familia": familia,
        "banda_propia": band,
        "usar": dict(band),
        "fuente": fuente_banda,
        "necesita_confirmacion": False,
        "motivo": "",
        "texto": _fmt(band["min"], band["max"]),
    }

    if oferta_min is None and oferta_max is None:
        result["motivo"] = "sin rango publicado; banda de familia"
        return result

    o_min = oferta_min if oferta_min is not None else oferta_max
    o_max = oferta_max if oferta_max is not None else oferta_min
    assert o_min is not None and o_max is not None

    if o_max < band["min"]:
        result["necesita_confirmacion"] = True
        result["motivo"] = f"oferta.max {o_max} < min_familia {band['min']}"
        result["texto"] = "NECESITA_CONFIRMACION"
        return result

    if alinear:
        result["usar"] = {"min": int(o_min), "max": int(o_max)}
        result["fuente"] = "oferta"
        result["texto"] = _fmt(int(o_min), int(o_max))
        result["motivo"] = "rango publicado alineado (oferta.max >= min_familia)"
    else:
        result["motivo"] = "alinear_a_rango_publicado desactivado; banda de familia"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sugiere rango salarial para respuestas de formulario"
    )
    parser.add_argument("--familia", required=True)
    parser.add_argument("--oferta-min", type=int)
    parser.add_argument("--oferta-max", type=int)
    parser.add_argument("--base", type=Path)
    args = parser.parse_args()

    result = suggest_salary(
        args.familia, args.oferta_min, args.oferta_max, base=args.base
    )
    print(f"fuente: {result['fuente']}")
    print(f"usar: {result['usar']['min']}-{result['usar']['max']}")
    print(f"texto: {result['texto']}")
    if result["motivo"]:
        print(f"motivo: {result['motivo']}")
    if result["necesita_confirmacion"]:
        print("NECESITA_CONFIRMACION")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
