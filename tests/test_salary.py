from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import write_vault  # noqa: E402
from suggest_salary import suggest_salary  # noqa: E402

CONSTRAINTS = {
    "salario": {
        "alinear_a_rango_publicado": True,
        "dev": {"min": 22000, "max": 28000},
        "soporte": {"min": 20000, "max": 23000},
    }
}


class SuggestSalaryTests(unittest.TestCase):
    def test_sin_rango_usa_banda_familia(self) -> None:
        r = suggest_salary("dev", constraints=CONSTRAINTS)
        self.assertEqual(r["fuente"], "constraints")
        self.assertEqual(r["usar"], {"min": 22000, "max": 28000})
        self.assertFalse(r["necesita_confirmacion"])

    def test_oferta_por_encima_del_minimo_se_alinea(self) -> None:
        r = suggest_salary("dev", 30000, 33000, CONSTRAINTS)
        self.assertEqual(r["fuente"], "oferta")
        self.assertEqual(r["usar"], {"min": 30000, "max": 33000})
        self.assertFalse(r["necesita_confirmacion"])
        self.assertIn("30.000", r["texto"])

    def test_oferta_por_debajo_del_minimo_confirma(self) -> None:
        r = suggest_salary("dev", 16000, 18000, CONSTRAINTS)
        self.assertTrue(r["necesita_confirmacion"])
        self.assertEqual(r["texto"], "NECESITA_CONFIRMACION")
        self.assertEqual(r["fuente"], "constraints")

    def test_banda_desde_familias_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = write_vault(Path(tmp))
            r = suggest_salary("soporte", base=base)
            self.assertEqual(r["usar"], {"min": 20000, "max": 23000})


if __name__ == "__main__":
    unittest.main()
