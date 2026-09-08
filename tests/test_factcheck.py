from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import dump_yaml  # noqa: E402
from factcheck import run_factcheck  # noqa: E402
from helpers import write_vault  # noqa: E402
from render_empresa import render_empresa  # noqa: E402


def _cv() -> dict:
    return {
        "headline": "Desarrollador web",
        "perfil": "Interfaces con Angular y TypeScript",
        "competencias": ["HTML", "CSS", "TypeScript"],
        "experiencia": [
            {
                "empresa": "Empresa A",
                "titulo": "Desarrollador full stack",
                "bullets": [
                    {
                        "texto": "Desarrollar interfaces con Angular y TypeScript",
                        "evidencia_id": "ev-01",
                    }
                ],
            }
        ],
    }


class EmpresaRenderTests(unittest.TestCase):
    def test_hechos_y_equipo(self) -> None:
        md = render_empresa(
            {
                "empresa": "Acme Demo SL",
                "sin_hechos_verificables": False,
                "hechos": [
                    {
                        "hecho": "Producto de facturación",
                        "fuente": "https://example.com/acme",
                    }
                ],
                "stack_publico": ["Angular"],
                "equipo_receptor": "Reports to Head of Engineering",
            }
        )
        self.assertIn("Producto de facturación", md)
        self.assertIn("https://example.com/acme", md)
        self.assertIn("Angular", md)
        self.assertIn("Head of Engineering", md)
        self.assertIn("false", md.lower())


class FactcheckTests(unittest.TestCase):
    def test_ok_sin_invencion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "Acme publica un producto de facturación. "
                "En Empresa A desarrollé interfaces con Angular y TypeScript. "
                "Puedo hablar del stack el jueves.",
                encoding="utf-8",
            )
            (pack / "outreach.md").write_text(
                "Vi el anuncio. He trabajado HTML y TypeScript en Empresa A. "
                "¿15 minutos esta semana?",
                encoding="utf-8",
            )
            dump_yaml(
                pack / "empresa.yaml",
                {
                    "empresa": "Acme Demo SL",
                    "sin_hechos_verificables": False,
                    "hechos": [
                        {
                            "hecho": "Producto de facturación",
                            "fuente": "https://example.com/acme",
                        }
                    ],
                    "stack_publico": [],
                    "equipo_receptor": None,
                },
            )
            report = run_factcheck(pack, base)
            self.assertTrue(report["ok"], report)
            self.assertEqual(report["confianza"], 1.0)
            self.assertLessEqual(report["presentacion_palabras"], 250)
            self.assertLessEqual(report["outreach_palabras"], 80)

    def test_metrica_inventada_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["experiencia"][0]["bullets"][0]["texto"] = (
                "Aumenté un 47% el rendimiento con Angular"
            )
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            tipos = [v["tipo"] for v in report["violaciones"]]
            self.assertIn("metrica", tipos)
            self.assertLess(report["confianza"], 1.0)

    def test_porcentaje_no_cuela_con_el_mismo_numero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            evid = (base / "evidencias.yaml").read_text(encoding="utf-8")
            (base / "evidencias.yaml").write_text(
                evid + "\n# 47 usuarios en prueba\n", encoding="utf-8"
            )
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["experiencia"][0]["bullets"][0]["texto"] = (
                "Aumenté un 47% el rendimiento con Angular"
            )
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(any(v["tipo"] == "metrica" for v in report["violaciones"]))

    def test_tech_y_empleador_huerfanos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["competencias"] = ["HTML", "Kubernetes"]
            cv["experiencia"][0]["empresa"] = "Empresa Inventada SL"
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            tipos = {v["tipo"] for v in report["violaciones"]}
            self.assertIn("tecnologia", tipos)
            self.assertIn("empleador", tipos)

    def test_presentacion_larga_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text("palabra " * 251, encoding="utf-8")
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(v["tipo"] == "longitud" for v in report["violaciones"])
            )


if __name__ == "__main__":
    unittest.main()
