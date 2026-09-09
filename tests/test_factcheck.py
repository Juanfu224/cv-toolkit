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
                "Desarrollador web con Angular y TypeScript en Empresa A. "
                "He construido interfaces ATS con HTML, CSS y SQL. "
                "¿15 minutos para contrastar el stack del anuncio?",
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

    def test_cliche_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "Soy apasionado por el desarrollo web y tengo excelentes habilidades.",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(any(v["tipo"] == "cliche" for v in report["violaciones"]))

    def test_eco_accion_resultado_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["experiencia"][0]["bullets"] = [
                {
                    "texto": "Implementé X en Y. Implementé X en Y",
                    "evidencia_id": "ev-01",
                }
            ]
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(any(v["tipo"] == "eco" for v in report["violaciones"]))

    def test_elaboracion_star_no_es_eco(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["experiencia"][0]["bullets"] = [
                {
                    "texto": "Implementé X. Implementé X en producción con monitoreo",
                    "evidencia_id": "ev-01",
                }
            ]
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(any(v["tipo"] == "eco" for v in report["violaciones"]))

    def test_perfil_lista_skills_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["perfil"] = " · ".join(cv["competencias"])
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(any(v["tipo"] == "perfil" for v in report["violaciones"]))

    def test_bullet_sin_evidencia_id_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            cv["experiencia"][0]["bullets"] = ["Texto sin evidencia"]
            dump_yaml(pack / "cv.yaml", cv)
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(v["tipo"] == "evidencia_id" for v in report["violaciones"])
            )

    def test_huerfanas_en_gaps_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            dump_yaml(pack / "gaps.yaml", {"huerfanas": ["Angular"], "score_t1": 0.8})
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(v["tipo"] == "huerfana" for v in report["violaciones"])
            )

    def test_certs_none_en_curriculum_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "curriculum.md").write_text(
                "# Test\n\n## Certificaciones\n\nNone · None · None\n",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(v["tipo"] == "certificacion" for v in report["violaciones"])
            )

    def test_presentacion_abre_con_no_tengo_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "No tengo experiencia en DOORS ni sector aeronáutico. "
                "Sí Angular y TypeScript en Empresa A.",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(any(v["tipo"] == "tono" for v in report["violaciones"]))

    def test_presentacion_abre_con_me_falta_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "Me falta experiencia formal en Kubernetes. "
                "Sí Angular y TypeScript en Empresa A.",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(any(v["tipo"] == "tono" for v in report["violaciones"]))

    def test_respuesta_abre_con_no_tengo_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "respuestas.md").write_text(
                "## ¿Conoces DOORS?\n\n"
                "No tengo experiencia con DOORS; sí Angular en Empresa A.\n\n"
                "Caracteres: 55\n"
                "Fuente: vault\n",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    v["tipo"] == "tono" and "respuestas.md" in v["dato"]
                    for v in report["violaciones"]
                )
            )

    def test_presentacion_cta_muerto_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "Desarrollo interfaces con Angular en Empresa A. "
                "Adjunto mi CV y quedo a disposición.",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    v["tipo"] == "tono" and "cta_muerto" in v["detalle"]
                    for v in report["violaciones"]
                )
            )

    def test_presentacion_formativo_en_cuerpo_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "He entregado interfaces ATS con Angular. "
                "Mi nivel formativo en Kubernetes no es el foco de esta carta. "
                "¿15 minutos esta semana?",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    v["tipo"] == "tono" and "gap_en_carta" in v["detalle"]
                    for v in report["violaciones"]
                )
            )

    def test_presentacion_skills_dump_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            cv = _cv()
            dump_yaml(pack / "cv.yaml", cv)
            (pack / "presentacion.md").write_text(
                " · ".join(cv["competencias"]),
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    v["tipo"] == "tono" and "skills_dump" in v["detalle"]
                    for v in report["violaciones"]
                )
            )

    def test_presentacion_formacion_academica_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "Mi formación en Ingeniería me dio base analítica. "
                "En Empresa A entregué interfaces ATS con Angular. "
                "¿15 minutos para contrastar el stack del anuncio?",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(
                any("gap_en_carta" in v["detalle"] for v in report["violaciones"]),
                report["violaciones"],
            )

    def test_presentacion_mentoring_en_formacion_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "En Empresa A trabajo en formación de juniors con Angular. "
                "He entregado interfaces ATS usables a diario. "
                "¿15 minutos esta semana?",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(
                any("gap_en_carta" in v["detalle"] for v in report["violaciones"]),
                report["violaciones"],
            )

    def test_presentacion_no_tengo_duda_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "No tengo duda de que encajo en el rol de interfaces ATS. "
                "En Empresa A entregué flujos con Angular. "
                "¿15 minutos para contrastar el stack del anuncio?",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(
                any(v["tipo"] == "tono" for v in report["violaciones"]),
                report["violaciones"],
            )

    def test_presentacion_adjunto_cv_su_disposicion_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            pack = root / "pack"
            pack.mkdir()
            dump_yaml(pack / "cv.yaml", _cv())
            (pack / "presentacion.md").write_text(
                "Desarrollo interfaces con Angular en Empresa A. "
                "Adjunto CV y quedo a su disposición.",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertFalse(report["ok"])
            self.assertTrue(
                any(
                    v["tipo"] == "tono" and "cta_muerto" in v["detalle"]
                    for v in report["violaciones"]
                )
            )


if __name__ == "__main__":
    unittest.main()
