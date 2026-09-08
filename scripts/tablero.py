from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import dump_yaml, load_yaml
from paths import TABLERO

ESTADOS = (
    "borrador",
    "listo",
    "enviada",
    "entrevista",
    "oferta",
    "rechazada",
    "descartada",
)


def load_tablero(path: Path | None = None) -> dict:
    target = path or TABLERO
    if not target.exists():
        return {"candidaturas": []}
    return load_yaml(target)


def save_tablero(data: dict, path: Path | None = None) -> None:
    dump_yaml(path or TABLERO, data)


def upsert(
    slug: str,
    estado: str,
    *,
    empresa: str | None = None,
    puesto: str | None = None,
    enviada: str | None = None,
    seguimiento: str | None = None,
    notas: str | None = None,
    path: Path | None = None,
) -> dict:
    if estado not in ESTADOS:
        raise SystemExit(f"estado inválido {estado!r}: {', '.join(ESTADOS)}")
    data = load_tablero(path)
    rows = data.setdefault("candidaturas", [])
    row = next((r for r in rows if r.get("slug") == slug), None)
    if row is None:
        row = {"slug": slug}
        rows.append(row)
    row["estado"] = estado
    if empresa is not None:
        row["empresa"] = empresa
    if puesto is not None:
        row["puesto"] = puesto
    if enviada is not None:
        row["enviada"] = enviada
        if seguimiento is None and estado == "enviada":
            try:
                d = date.fromisoformat(enviada)
                row["seguimiento"] = (d + timedelta(days=7)).isoformat()
            except ValueError:
                row["seguimiento"] = seguimiento
    if seguimiento is not None:
        row["seguimiento"] = seguimiento
    if notas is not None:
        row["notas"] = notas
    save_tablero(data, path)
    return row


def list_rows(path: Path | None = None) -> list[dict]:
    return list(load_tablero(path).get("candidaturas") or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Tablero de candidaturas")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="Lista el tablero")
    p_up = sub.add_parser("set", help="Crea o actualiza una fila")
    p_up.add_argument("--slug", required=True)
    p_up.add_argument("--estado", required=True, choices=ESTADOS)
    p_up.add_argument("--empresa")
    p_up.add_argument("--puesto")
    p_up.add_argument("--enviada", help="YYYY-MM-DD")
    p_up.add_argument("--seguimiento", help="YYYY-MM-DD")
    p_up.add_argument("--notas")
    p_up.add_argument("--tablero", type=Path)
    args = parser.parse_args()

    if args.cmd == "list":
        rows = list_rows()
        if not rows:
            print("tablero vacío")
            return 0
        for r in rows:
            print(
                f"{r.get('slug')}\t{r.get('estado')}\t"
                f"enviada={r.get('enviada') or '-'}\t"
                f"seguimiento={r.get('seguimiento') or '-'}"
            )
        return 0

    row = upsert(
        args.slug,
        args.estado,
        empresa=args.empresa,
        puesto=args.puesto,
        enviada=args.enviada,
        seguimiento=args.seguimiento,
        notas=args.notas,
        path=args.tablero,
    )
    print(f"actualizado {row['slug']} → {row['estado']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
