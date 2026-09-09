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
from scaffold_defaults import _texto_evidencia, scaffold  # noqa: E402
from validate_base import validate  # noqa: E402
from common import is_echo_text  # noqa: E402


class DefaultCvTests(unittest.TestCase):
    def test_vault_vacio_del_kit(self) -> None:
        self.assertEqual(validate(BASE, PLANTILLAS), 2)

    def test_texto_evidencia_omite_eco(self) -> None:
        texto = _texto_evidencia(
            {
                "accion": "Implementé X en Y",
                "resultado": "Implementé X en Y",
            }
        )
        self.assertEqual(texto, "Implementé X en Y")
        self.assertNotIn(". ", texto)

    def test_texto_evidencia_concatena_resultado_distinto(self) -> None:
        texto = _texto_evidencia(
            {
                "accion": "Implementé interfaces con Angular",
                "resultado": "Reduje el tiempo de carga percibido",
            }
        )
        self.assertEqual(
            texto,
            "Implementé interfaces con Angular. Reduje el tiempo de carga percibido",
        )

    def test_texto_evidencia_conserva_elaboracion_star(self) -> None:
        """Contención corta⊂larga no es eco: no tirar el resultado útil."""
        texto = _texto_evidencia(
            {
                "accion": "Implementé X",
                "resultado": "Implementé X en producción con monitoreo",
            }
        )
        self.assertIn("producción", texto)
        self.assertIn("monitoreo", texto)
        self.assertFalse(
            is_echo_text("Implementé X", "Implementé X en producción con monitoreo")
        )

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

    def test_fechas_iso_a_yyyy_mm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            from common import dump_yaml, load_yaml

            perfil = load_yaml(base / "perfil.yaml")
            perfil["experiencia"][0]["inicio"] = "2025-03-15"
            perfil["experiencia"][0]["fin"] = "actualidad"
            perfil["educacion"][0]["fin"] = "2024-06-30"
            dump_yaml(base / "perfil.yaml", perfil)
            plantillas = root / "plantillas"
            scaffold(base, plantillas)
            cv = load_yaml(plantillas / "cv_default_dev.yaml")
            self.assertEqual(cv["experiencia"][0]["fechas"], "2025-03 — Actualidad")
            self.assertEqual(cv["formacion"][0]["fecha"], "2024-06")

    def test_github_opcional_no_es_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from common import load_yaml

            base = write_vault(root)
            perfil = load_yaml(base / "perfil.yaml")
            perfil["contacto"]["github"] = "PENDIENTE"
            from common import dump_yaml

            dump_yaml(base / "perfil.yaml", perfil)
            plantillas = root / "plantillas"
            scaffold(base, plantillas)
            self.assertEqual(validate(base, plantillas), 0)


if __name__ == "__main__":
    unittest.main()
