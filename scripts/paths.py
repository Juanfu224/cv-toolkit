from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "base"
OFERTA = ROOT / "oferta"
CV_DIR = ROOT / "cv"
CANDIDATURAS = ROOT / "candidaturas"
PLANTILLAS = ROOT / "plantillas"
TABLERO = CANDIDATURAS / "tablero.yaml"


def is_allowed_output(path: Path) -> bool:
    """Escritura solo bajo el repo o el tmp del sistema (tests). SHIELD §1.2."""
    resolved = path.resolve()
    roots = (ROOT.resolve(), Path(tempfile.gettempdir()).resolve())
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False
