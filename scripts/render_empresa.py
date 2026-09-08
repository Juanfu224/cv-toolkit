from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml
from paths import PLANTILLAS, is_allowed_output


def render_empresa(data: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(PLANTILLAS)),
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = env.get_template("empresa.md.j2")
    hechos = list(data.get("hechos") or [])[:3]
    return template.render(
        empresa=data.get("empresa") or "Empresa",
        sin_hechos_verificables=bool(data.get("sin_hechos_verificables", not hechos)),
        hechos=hechos,
        stack_publico=data.get("stack_publico") or [],
        equipo_receptor=data.get("equipo_receptor"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renderiza empresa.md desde empresa.yaml + plantillas/empresa.md.j2"
    )
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not is_allowed_output(args.out):
        print("empresa: --out fuera del repo o tmp", file=sys.stderr)
        return 1
    text = render_empresa(load_yaml(args.data))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
