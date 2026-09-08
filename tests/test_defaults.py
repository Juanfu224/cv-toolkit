from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import write_vault  # noqa: E402
from paths import BASE, PLANTILLAS  # noqa: E402
from scaffold_defaults import scaffold  # noqa: E402
from validate_base import validate  # noqa: E402


class DefaultCvTests(unittest.TestCase):
    def test_vault_vacio_del_kit(self) -> None:
        self.assertEqual(validate(BASE, PLANTILLAS), 2)

    def test_vault_temporal_ok_tras_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            plantillas = root / "plantillas"
            written = scaffold(base, plantillas)
            self.assertTrue(any(p.name == "cv_default_dev.yaml" for p in written))
            self.assertEqual(validate(base, plantillas), 0)

    def test_puesto_actual_primero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            plantillas = root / "plantillas"
            scaffold(base, plantillas)
            from common import load_yaml

            cv = load_yaml(plantillas / "cv_default_dev.yaml")
            exp = cv.get("experiencia") or []
            self.assertTrue(exp[0].get("actual"))


if __name__ == "__main__":
    unittest.main()
