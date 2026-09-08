from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_yaml
from familias import familia_ids
from paths import BASE, PLANTILLAS, ROOT
from validate_base import validate, vault_vacio


def _ok(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"OK   {label}{suffix}")


def _warn(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"WARN {label}{suffix}")


def _fail(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"FAIL {label}{suffix}")


def _origen_files() -> dict[str, Path]:
    origen = BASE / "origen"
    found = {}
    for name in ("curriculum.md", "curriculum.pdf", "presentacion.md"):
        path = origen / name
        if path.exists() and path.stat().st_size > 0:
            found[name] = path
    return found


def run_doctor() -> int:
    """Chequeo de salud. Exit 0 = usable; 1 = problema bloqueante."""
    print("cvtool doctor")
    hard_fail = False

    py = sys.version_info
    if py >= (3, 10):
        _ok("python", f"{py.major}.{py.minor}.{py.micro}")
    else:
        _fail("python", f"{py.major}.{py.minor} (hace falta 3.10+)")
        hard_fail = True

    for mod, label in (
        ("yaml", "pyyaml"),
        ("jinja2", "jinja2"),
        ("pypdf", "pypdf"),
        ("docx", "python-docx"),
    ):
        try:
            __import__(mod)
            _ok(label)
        except ImportError as exc:
            _fail(label, f"no instalado ({exc}). pip install -r requirements.txt")
            hard_fail = True

    try:
        import weasyprint  # noqa: F401

        _ok("weasyprint")
    except ImportError as exc:
        _fail("weasyprint", f"paquete ausente ({exc}). pip install -r requirements.txt")
        hard_fail = True
    except OSError as exc:
        _fail(
            "weasyprint",
            f"faltan libs del SO (Pango/cairo): {exc}. Ver README → Empezar",
        )
        hard_fail = True

    if (ROOT / ".venv").is_dir():
        _ok(".venv")
    else:
        _warn(".venv", "no hay .venv; puedes usar otro Python con deps instaladas")

    origen = _origen_files()
    if "curriculum.md" in origen or "curriculum.pdf" in origen:
        _ok("origen", ", ".join(origen))
    else:
        _warn("origen", "vacío — copia curriculum.md o .pdf a base/origen/")

    perfil = load_yaml(BASE / "perfil.yaml")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = validate()

    if code == 2 or vault_vacio(perfil):
        _warn("vault", "VACÍO — en Cursor: inicializa mi base")
        siguiente = "copia tu CV a base/origen/ y di «inicializa mi base»"
    elif code == 1:
        _fail("vault", "inconsistente — corrige ERROR de validate")
        hard_fail = True
        siguiente = "corrige base/ (cvtool validate) y repite doctor"
    else:
        _ok("vault", "OK")
        fams = familia_ids()
        if fams:
            _ok("familias", ", ".join(fams))
        else:
            _warn("familias", "ninguna — define base/familias.yaml")
        defaults = sorted(PLANTILLAS.glob("cv_default_*.yaml"))
        if defaults:
            _ok("plantillas", ", ".join(p.name for p in defaults))
        else:
            _warn("plantillas", "falta scaffold — cvtool scaffold")
        siguiente = "pega una oferta en oferta/ y di «genera candidatura»"

    print(f"siguiente: {siguiente}")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(run_doctor())
