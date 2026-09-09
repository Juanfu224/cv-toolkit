from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import dump_yaml, normalize_cert, normalize_certs  # noqa: E402
from helpers import write_vault  # noqa: E402
from render_cv import apply_perfil, certs_linea, to_markdown  # noqa: E402


class NormalizeCertsTests(unittest.TestCase):
    def test_titulo_a_nombre(self) -> None:
        self.assertEqual(
            normalize_cert({"titulo": "CCNA: Introduction to Networks"}),
            {"nombre": "CCNA: Introduction to Networks"},
        )

    def test_nombre_y_entidad(self) -> None:
        self.assertEqual(
            normalize_cert({"nombre": "CCNA", "entidad": "Cisco"}),
            {"nombre": "CCNA", "entidad": "Cisco"},
        )

    def test_placeholders_omitidos(self) -> None:
        self.assertIsNone(normalize_cert({"nombre": None}))
        self.assertIsNone(normalize_cert({"nombre": "none"}))
        self.assertIsNone(normalize_cert({"titulo": "PENDIENTE"}))
        self.assertEqual(normalize_certs([{"nombre": None}, "none", {}]), [])


class CertsLineaTests(unittest.TestCase):
    def test_titulo_no_imprime_none(self) -> None:
        cv = {
            "certificaciones": [
                {"titulo": "CCNA: Introduction to Networks"},
                {"titulo": "IT Essentials"},
            ]
        }
        linea = certs_linea(cv)
        self.assertEqual(
            linea,
            "CCNA: Introduction to Networks · IT Essentials",
        )
        self.assertNotIn("None", linea)

    def test_nombre_null_omitido(self) -> None:
        cv = {
            "certificaciones": [
                {"nombre": None},
                {"nombre": "none"},
                {"nombre": "AWS SAA", "entidad": "Amazon"},
            ]
        }
        self.assertEqual(certs_linea(cv), "AWS SAA (Amazon)")

    def test_markdown_omite_seccion_sin_certs_validas(self) -> None:
        cv = {
            "nombre": "Test",
            "headline": "Dev",
            "contacto": {
                "telefono": "1",
                "email": "a@b.c",
                "ciudad": "X",
                "pais": "Y",
            },
            "secciones": ["certificaciones"],
            "certificaciones": [{"nombre": None}, {"titulo": "none"}],
        }
        md = to_markdown(cv)
        self.assertNotIn("Certificaciones", md)
        self.assertNotIn("None", md)

    def test_apply_perfil_inyecta_certs_normalizadas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            perfil = {
                "nombre": "Nombre Prueba",
                "contacto": {
                    "telefono": "1",
                    "email": "a@b.c",
                    "ciudad": "X",
                    "pais": "Y",
                    "linkedin": "PENDIENTE",
                    "github": "PENDIENTE",
                },
                "certificaciones": [
                    {"titulo": "CCNA"},
                    {"nombre": None},
                ],
            }
            dump_yaml(base / "perfil.yaml", perfil)
            cv = apply_perfil({"secciones": ["perfil"]}, base=base)
            self.assertEqual(cv["certificaciones"], [{"nombre": "CCNA"}])
            self.assertIn("certificaciones", cv["secciones"])


if __name__ == "__main__":
    unittest.main()
