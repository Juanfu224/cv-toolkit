from __future__ import annotations

from pathlib import Path

from common import load_yaml
from paths import BASE


def load_familias(base: Path | None = None) -> dict[str, dict]:
    root = base or BASE
    path = root / "familias.yaml"
    if not path.exists():
        return {}
    doc = load_yaml(path)
    out: dict[str, dict] = {}
    for item in doc.get("familias") or []:
        fid = item.get("id")
        if fid:
            out[str(fid)] = item
    return out


def familia_ids(base: Path | None = None) -> list[str]:
    return list(load_familias(base).keys())


def default_cv_path(plantillas: Path, familia: str) -> Path:
    return plantillas / f"cv_default_{familia}.yaml"
