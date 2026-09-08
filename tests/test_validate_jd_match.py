from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import dump_yaml, load_yaml  # noqa: E402
from helpers import write_vault  # noqa: E402
from match import run_match  # noqa: E402
from validate_jd import validate_jd  # noqa: E402


def _jd(*, t1: list[str], must_have: list[str] | None = None, **extra) -> dict:
    data = {
        "titulo": "Desarrollador web",
        "empresa": "Acme",
        "ciudad": "Valencia",
        "modalidad": "remoto",
        "seniority": "junior",
        "must_have": must_have or ["TypeScript"],
        "keywords": {"t1": t1, "t2": [], "t3": []},
        "anios_experiencia_min": 0,
        "certificaciones_obligatorias": [],
    }
    data.update(extra)
    return data


class ValidateJdTests(unittest.TestCase):
    def test_ok_minimo(self) -> None:
        jd = _jd(
            t1=["Desarrollador web", "TypeScript", "Angular", "SQL", "Git", "HTML"]
        )
        self.assertEqual(validate_jd(jd), [])

    def test_t1_corto(self) -> None:
        jd = _jd(t1=["a", "b", "c", "d"])
        errs = validate_jd(jd)
        self.assertTrue(any("t1" in e for e in errs))

    def test_falta_empresa(self) -> None:
        jd = _jd(t1=["Desarrollador web", "TypeScript", "Angular", "SQL", "Git"])
        del jd["empresa"]
        errs = validate_jd(jd)
        self.assertTrue(any("empresa" in e for e in errs))


class VeredictoUmbralesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = write_vault(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_seniority_senior_no_aplicar(self) -> None:
        jd = _jd(
            t1=["TypeScript", "Angular", "SQL", "PHP", "APIs REST", "HTML"],
            seniority="senior",
        )
        _g, v = run_match(jd, base_dir=self.base)
        self.assertEqual(v["resultado"], "no_aplicar")
        self.assertTrue(any("seniority" in m for m in v["motivos"]))

    def test_t1_bajo_40_no_aplicar(self) -> None:
        # 5 términos todos missing → cov 0
        jd = _jd(
            t1=["Kubernetes", "Go", "Rust", "Scala", "Elixir"],
            must_have=[],
        )
        _g, v = run_match(jd, base_dir=self.base)
        self.assertEqual(v["resultado"], "no_aplicar")
        self.assertTrue(any("40%" in m for m in v["motivos"]))

    def test_t1_parcial_aplicar_con_reservas(self) -> None:
        # 3/5 have → 60% → reservas
        jd = _jd(
            t1=["TypeScript", "Angular", "SQL", "Kubernetes", "Go"],
            must_have=["TypeScript"],
        )
        _g, v = run_match(jd, base_dir=self.base)
        self.assertEqual(v["resultado"], "aplicar_con_reservas")

    def test_certs_obligatorias_no_aplicar(self) -> None:
        jd = _jd(
            t1=["TypeScript", "Angular", "SQL", "PHP", "HTML", "CSS"],
            certificaciones_obligatorias=["AWS Solutions Architect"],
        )
        _g, v = run_match(jd, base_dir=self.base)
        self.assertEqual(v["resultado"], "no_aplicar")
        self.assertTrue(any("certificaciones" in m for m in v["motivos"]))

    def test_forzar_flag(self) -> None:
        jd = _jd(
            t1=["Kubernetes", "Go", "Rust", "Scala", "Elixir"],
            must_have=[],
        )
        _g, v = run_match(jd, base_dir=self.base, forzar=True)
        self.assertEqual(v["resultado"], "no_aplicar")
        self.assertTrue(v["forzar"])

    def test_cobertura_alta_aplicar(self) -> None:
        jd = _jd(
            t1=["TypeScript", "Angular", "SQL", "PHP", "APIs REST", "HTML"],
            must_have=["TypeScript", "Angular"],
        )
        _g, v = run_match(jd, base_dir=self.base)
        self.assertEqual(v["resultado"], "aplicar")
        self.assertFalse(v["forzar"])


class TableroMetaTests(unittest.TestCase):
    def test_sync_meta_listo(self) -> None:
        from tablero import sync_meta_listo

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cand = root / "candidaturas" / "2026-09-08_acme_dev"
            cand.mkdir(parents=True)
            meta = {"empresa": "Acme", "puesto": "Dev", "listo_para_enviar": False}
            dump_yaml(cand / "meta.yaml", meta)
            sync_meta_listo(
                "2026-09-08_acme_dev", "listo", candidaturas_dir=root / "candidaturas"
            )
            loaded = load_yaml(cand / "meta.yaml")
            self.assertTrue(loaded["listo_para_enviar"])
            sync_meta_listo(
                "2026-09-08_acme_dev", "borrador", candidaturas_dir=root / "candidaturas"
            )
            loaded = load_yaml(cand / "meta.yaml")
            self.assertFalse(loaded["listo_para_enviar"])


if __name__ == "__main__":
    unittest.main()
