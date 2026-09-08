from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml
from paths import PLANTILLAS


def render_respuestas(data: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(PLANTILLAS)),
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = env.get_template("respuestas.md.j2")
    items = data.get("respuestas") or []
    for item in items:
        if "caracteres" not in item and item.get("respuesta") is not None:
            item["caracteres"] = len(str(item["respuesta"]))
    return template.render(respuestas=items)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renderiza respuestas.md desde YAML + plantillas/respuestas.md.j2"
    )
    parser.add_argument("--data", required=True, type=Path, help="YAML con clave respuestas")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    data = load_yaml(args.data)
    text = render_respuestas(data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
