from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import load_yaml  # noqa: E402
from helpers import write_vault  # noqa: E402
from match import run_match  # noqa: E402
from pack_cv import (  # noqa: E402
    LONG_BULLET_CHARS,
    SKILL_CAP,
    _force_t1,
    build_units,
    pack,
    score_text,
    t1_terms_from_gaps,
)
from render_cv import to_pdf  # noqa: E402
from scaffold_defaults import scaffold  # noqa: E402


class PackRankingTests(unittest.TestCase):
    def test_t1_outweighs_weak_bullet(self) -> None:
        t1 = ["TypeScript", "Angular"]
        sc_t1, cov = score_text(
            "Desarrollar pantallas con TypeScript y Angular",
            t1=t1,
            recency=50,
        )
        sc_weak, _ = score_text(
            "Colaboré en tareas varias del equipo",
            t1=t1,
            recency=200,
        )
        self.assertTrue(cov)
        self.assertGreater(sc_t1, sc_weak)

    def test_metric_bonus_only_quantitative(self) -> None:
        t1: list[str] = []
        sc_m, _ = score_text("Reducir tiempo de build un 30%", t1=t1)
        sc_plain, _ = score_text("Mejorar entrega de procesos del equipo", t1=t1)
        self.assertGreater(sc_m, sc_plain)

    def test_long_bullet_penalized_vs_short_t1(self) -> None:
        t1 = ["TypeScript"]
        short, _ = score_text("TypeScript en frontend", t1=t1)
        long_pad = "x" * (LONG_BULLET_CHARS + 80)
        long_sc, _ = score_text(f"TypeScript {long_pad}", t1=t1)
        self.assertGreater(short, long_sc)

    def test_alias_boosts_coverage(self) -> None:
        t1 = ["AD"]
        aliases = {"aliases": {"ad": ["Active Directory"]}}
        sc, cov = score_text(
            "Resetear cuentas en Active Directory",
            t1=t1,
            aliases=aliases,
        )
        self.assertIn("AD", cov)
        self.assertGreaterEqual(sc, 1000.0)

    def test_t1_from_gaps(self) -> None:
        gaps = {
            "t1": [
                {"term": "HTML", "status": "have"},
                {"term": "Kubernetes", "status": "missing"},
                {"term": "CSS", "status": "rephrase"},
            ]
        }
        self.assertEqual(t1_terms_from_gaps(gaps), ["HTML", "CSS"])

    def test_build_units_orders_t1_skills_first(self) -> None:
        draft = {
            "headline": "Dev",
            "perfil": "Perfil corto",
            "secciones": ["perfil", "competencias", "experiencia"],
            "competencias": [
                "SoftSkill",
                "TypeScript",
                "HTML",
                "CSS",
                "Git",
                "SQL",
                "PHP",
                "Angular",
                "Extra",
            ],
            "experiencia": [
                {
                    "titulo": "Dev",
                    "empresa": "A",
                    "fechas": "2025 — Actualidad",
                    "actual": True,
                    "bullets": [
                        {"texto": "Soft tasks only", "evidencia_id": "ev-soft"},
                        {
                            "texto": "Interfaces con TypeScript y Angular",
                            "evidencia_id": "ev-ts",
                        },
                        {"texto": "Maquetar HTML y CSS", "evidencia_id": "ev-html"},
                    ],
                }
            ],
            "proyectos": [],
            "formacion": [],
            "idiomas": [],
        }
        core, units, _forced, warnings = build_units(
            draft, t1=["TypeScript", "Angular", "HTML"]
        )
        self.assertEqual(warnings, [])
        self.assertIn("TypeScript", core["competencias"])
        self.assertIn("Angular", core["competencias"])
        self.assertLessEqual(len(core["competencias"]), 8)
        packable_skills = [u.key for u in units if u.kind == "skill"]
        self.assertTrue(packable_skills)
        self.assertTrue(
            all(
                k.replace("skill:", "") not in core["competencias"]
                for k in packable_skills
            )
        )
        unit_scores = {u.key: -u.score for u in units}
        if "bullet:ev-ts" in unit_scores and "bullet:ev-soft" in unit_scores:
            self.assertGreater(unit_scores["bullet:ev-ts"], unit_scores["bullet:ev-soft"])

    def test_build_units_warns_when_few_bullets(self) -> None:
        draft = {
            "headline": "Dev",
            "perfil": "Perfil",
            "secciones": ["perfil", "competencias", "experiencia"],
            "competencias": ["HTML", "CSS"],
            "experiencia": [
                {
                    "titulo": "Dev",
                    "empresa": "A",
                    "fechas": "2025 — Actualidad",
                    "actual": True,
                    "bullets": [{"texto": "Solo uno", "evidencia_id": "ev-1"}],
                }
            ],
            "proyectos": [],
            "formacion": [],
            "idiomas": [],
        }
        _core, _units, _forced, warnings = build_units(draft, t1=[])
        self.assertTrue(any("bullet" in w for w in warnings))

    def test_force_t1_does_not_drop_t1_skill(self) -> None:
        t1 = [f"T{i}" for i in range(SKILL_CAP)] + ["NewT1"]
        packed = {
            "competencias": [f"T{i}" for i in range(SKILL_CAP)],
            "experiencia": [],
            "perfil": "",
            "headline": "",
        }
        draft = {
            "competencias": packed["competencias"] + ["NewT1"],
            "experiencia": [
                {
                    "titulo": "Dev",
                    "empresa": "A",
                    "fechas": "2025",
                    "bullets": [
                        {"texto": "Uso NewT1 a diario", "evidencia_id": "ev-new"}
                    ],
                }
            ],
        }
        # All skills cover T1 — force should WARN and keep existing T*
        report: dict = {"forced": [], "warnings": []}
        _force_t1(packed, draft, t1, {}, report)
        for i in range(SKILL_CAP):
            self.assertIn(f"T{i}", packed["competencias"])
        self.assertTrue(report.get("warnings"))


class PackE2ETests(unittest.TestCase):
    def test_pack_keeps_one_page_and_t1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            plantillas = root / "plantillas"
            scaffold(base, plantillas)
            cv = load_yaml(plantillas / "cv_default_dev.yaml")
            perfil = load_yaml(base / "perfil.yaml")
            cv["nombre"] = perfil["nombre"]
            cv["contacto"] = perfil["contacto"]

            pad = (
                "Detalle operativo adicional sobre integración, despliegue, "
                "revisión de código, documentación de contratos, pruebas manuales "
                "y coordinación con producto en entorno de prueba. "
            ) * 4
            for rol in cv.get("experiencia") or []:
                extras = []
                for i in range(12):
                    extras.append(
                        {
                            "texto": f"Tarea auxiliar {i}: {pad}",
                            "evidencia_id": f"pad-{i}",
                        }
                    )
                rol["bullets"] = list(rol.get("bullets") or []) + extras

            from pypdf import PdfReader

            probe = root / "fat.pdf"
            to_pdf(cv, probe)
            self.assertGreater(len(PdfReader(str(probe)).pages), 1)

            jd = load_yaml(ROOT / "ejemplos" / "oferta-demo" / "jd.yaml")
            gaps, _ver = run_match(jd, base_dir=base)
            packed, report = pack(
                copy.deepcopy(cv),
                gaps=gaps,
                aliases=load_yaml(base / "aliases.yaml"),
                work_dir=root / "packwork",
            )
            out_pdf = root / "packed.pdf"
            to_pdf(packed, out_pdf)
            self.assertEqual(len(PdfReader(str(out_pdf)).pages), 1)
            self.assertEqual(report.get("pages"), 1)
            self.assertGreaterEqual(len(packed.get("competencias") or []), 1)
            self.assertTrue(packed.get("experiencia"))
            self.assertGreaterEqual(
                len(packed["experiencia"][0].get("bullets") or []), 2
            )
            blob = " ".join(packed.get("competencias") or [])
            for rol in packed.get("experiencia") or []:
                for b in rol.get("bullets") or []:
                    blob += " " + (b.get("texto") if isinstance(b, dict) else str(b))
            self.assertTrue(
                any(
                    t.lower() in blob.lower()
                    for t in ("HTML", "TypeScript", "Angular", "CSS")
                ),
                msg="packed CV lost primary T1 signals",
            )

    def test_pack_cleans_temp_when_no_work_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            plantillas = root / "plantillas"
            scaffold(base, plantillas)
            cv = load_yaml(plantillas / "cv_default_dev.yaml")
            perfil = load_yaml(base / "perfil.yaml")
            cv["nombre"] = perfil["nombre"]
            cv["contacto"] = perfil["contacto"]

            created: list[str] = []

            class TrackingTmp(tempfile.TemporaryDirectory):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    created.append(self.name)

            with mock.patch("pack_cv.tempfile.TemporaryDirectory", TrackingTmp):
                packed, report = pack(
                    cv,
                    gaps={"t1": [{"term": "HTML", "status": "have"}]},
                    aliases=load_yaml(base / "aliases.yaml"),
                )
            self.assertEqual(report.get("pages"), 1)
            self.assertTrue(packed.get("experiencia"))
            self.assertTrue(created)
            for name in created:
                self.assertFalse(
                    Path(name).exists(),
                    msg=f"temp dir leaked: {name}",
                )


if __name__ == "__main__":
    unittest.main()
