from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import phrase_in_terms  # noqa: E402
from helpers import write_vault  # noqa: E402
from match import classify, run_match  # noqa: E402


def _jd(*, t1: list[str], must_have: list[str] | None = None, **extra) -> dict:
    data = {
        "titulo": "Desarrollador web",
        "ciudad": "Valencia",
        "modalidad": "remoto",
        "seniority": "junior",
        "must_have": must_have or [],
        "keywords": {"t1": t1, "t2": [], "t3": []},
        "anios_experiencia_min": 0,
        "certificaciones_obligatorias": [],
    }
    data.update(extra)
    return data


class TokenMatchTests(unittest.TestCase):
    def test_java_does_not_match_javascript(self) -> None:
        terms = {"javascript", "active directory", "graduado"}
        aliases = {"aliases": {"ad": ["Active Directory"]}}
        self.assertEqual(classify("java", aliases, terms), "missing")
        self.assertEqual(classify("javascript", aliases, terms), "have")

    def test_ad_does_not_match_graduado(self) -> None:
        terms = {"javascript", "graduado"}
        aliases = {"aliases": {"ad": ["Active Directory"]}}
        self.assertEqual(classify("ad", aliases, terms), "missing")
        self.assertEqual(classify("ui", aliases, terms), "missing")

    def test_ad_rephrase_via_alias(self) -> None:
        terms = {"active directory"}
        aliases = {"aliases": {"ad": ["Active Directory"]}}
        self.assertEqual(classify("ad", aliases, terms), "rephrase")

    def test_angular_matches_angular_ssr(self) -> None:
        terms = {"angular ssr"}
        self.assertTrue(phrase_in_terms("angular", terms))

    def test_empty_alias_is_missing(self) -> None:
        terms = {"javascript"}
        aliases = {"aliases": {"itil": []}}
        self.assertEqual(classify("itil", aliases, terms), "missing")


class VeredictoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = write_vault(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_star_prose_is_not_a_term(self) -> None:
        jd = _jd(t1=["entorno"])
        gaps, _veredicto = run_match(jd, base_dir=self.base)
        self.assertEqual(gaps["t1"][0]["status"], "missing")

    def test_typescript_sql_php_have(self) -> None:
        jd = _jd(t1=["TypeScript", "SQL", "PHP"])
        gaps, _veredicto = run_match(jd, base_dir=self.base)
        statuses = {r["term"]: r["status"] for r in gaps["t1"]}
        self.assertEqual(statuses["TypeScript"], "have")
        self.assertEqual(statuses["SQL"], "have")
        self.assertEqual(statuses["PHP"], "have")

    def test_english_aliases(self) -> None:
        jd = _jd(t1=["REST APIs", "help desk"])
        gaps, _veredicto = run_match(jd, base_dir=self.base)
        statuses = {r["term"]: r["status"] for r in gaps["t1"]}
        self.assertIn(statuses["REST APIs"], {"have", "rephrase"})
        self.assertIn(statuses["help desk"], {"have", "rephrase"})

    def test_kubernetes_empty_alias_missing(self) -> None:
        jd = _jd(t1=["Kubernetes"])
        gaps, _veredicto = run_match(jd, base_dir=self.base)
        self.assertEqual(gaps["t1"][0]["status"], "missing")

    def test_presencial_otra_ciudad_no_aplicar(self) -> None:
        jd = {
            "titulo": "Técnico N1",
            "empresa": "Acme",
            "ciudad": "Gijón",
            "modalidad": "presencial",
            "seniority": "junior",
            "must_have": ["Soporte técnico"],
            "keywords": {
                "t1": ["Soporte técnico", "Ticketing", "Active Directory"],
                "t2": [],
                "t3": [],
            },
            "anios_experiencia_min": 0,
            "certificaciones_obligatorias": [],
        }
        _gaps, veredicto = run_match(jd, base_dir=self.base)
        self.assertEqual(veredicto["resultado"], "no_aplicar")
        self.assertTrue(any("traslado" in m for m in veredicto["motivos"]))

    def test_must_have_missing_no_aplicar(self) -> None:
        jd = _jd(t1=["Angular"], must_have=["Kubernetes"])
        _gaps, veredicto = run_match(jd, base_dir=self.base)
        self.assertEqual(veredicto["resultado"], "no_aplicar")
        self.assertTrue(any("must_have" in m for m in veredicto["motivos"]))


if __name__ == "__main__":
    unittest.main()
