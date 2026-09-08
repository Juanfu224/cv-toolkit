from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from basename import pascal_nombre, send_basename  # noqa: E402
from common import contact_links  # noqa: E402
from paths import ROOT, is_allowed_output  # noqa: E402
from tablero import ESTADOS, list_rows, upsert  # noqa: E402


class BasenameTests(unittest.TestCase):
    def test_tres_palabras(self) -> None:
        self.assertEqual(pascal_nombre("Ana Pérez López García"), "AnaPerezLopez")

    def test_send_basename(self) -> None:
        name = send_basename("Ana Pérez", "Desarrollador web", "Acme Corp")
        self.assertEqual(name, "CV_AnaPerez_Desarrollador_web_Acme_Corp")


class ContactLinksTests(unittest.TestCase):
    def test_omite_pendiente_y_vacios(self) -> None:
        self.assertEqual(
            contact_links({"linkedin": "PENDIENTE", "github": ""}),
            [],
        )
        self.assertEqual(
            contact_links({"linkedin": "https://linkedin.com/in/a", "github": None}),
            ["https://linkedin.com/in/a"],
        )


class PathGuardTests(unittest.TestCase):
    def test_allowed_output_repo_y_tmp(self) -> None:
        self.assertTrue(is_allowed_output(ROOT / "oferta"))
        self.assertTrue(is_allowed_output(Path(tempfile.gettempdir()) / "x"))
        self.assertFalse(is_allowed_output(Path("/etc/passwd")))


class TableroTests(unittest.TestCase):
    def test_upsert_y_seguimiento(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tablero.yaml"
            row = upsert(
                "2026-09-08_acme_dev",
                "enviada",
                empresa="Acme",
                puesto="Dev",
                enviada="2026-09-08",
                path=path,
            )
            self.assertEqual(row["estado"], "enviada")
            self.assertEqual(row["seguimiento"], "2026-09-15")
            self.assertEqual(len(list_rows(path)), 1)
            self.assertIn("enviada", ESTADOS)
            self.assertIn("listo", ESTADOS)

    def test_upsert_custom_tablero_sync_meta(self) -> None:
        from common import dump_yaml, load_yaml

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slug = "2026-09-08_acme_dev"
            cand = root / slug
            cand.mkdir()
            dump_yaml(
                cand / "meta.yaml",
                {
                    "empresa": "Acme",
                    "puesto": "Dev",
                    "listo_para_enviar": False,
                    "pack_estado": "aprobado",
                },
            )
            tablero = root / "tablero.yaml"
            upsert(slug, "listo", empresa="Acme", puesto="Dev", path=tablero)
            meta = load_yaml(cand / "meta.yaml")
            self.assertTrue(meta["listo_para_enviar"])



class CvtoolHelpTests(unittest.TestCase):
    def test_help_incluye_match_copy_doctor_respuestas(self) -> None:
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "cvtool.py"), "-h"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("match", proc.stdout)
        self.assertIn("copy", proc.stdout)
        self.assertIn("doctor", proc.stdout)
        self.assertIn("respuestas", proc.stdout)
        self.assertIn("pack", proc.stdout)
        self.assertIn("ingest-jd", proc.stdout)
        self.assertIn("factcheck", proc.stdout)
        self.assertIn("empresa", proc.stdout)


class SkillContractTests(unittest.TestCase):
    def test_generar_candidatura_hitl_factcheck_outreach(self) -> None:
        skill = (
            ROOT / ".agents" / "skills" / "generar-candidatura" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("factcheck", skill)
        self.assertIn("pack_estado", skill)
        self.assertIn("aprobar", skill)
        self.assertIn("rechazar", skill)
        self.assertIn("outreach.md", skill)
        self.assertIn("≤250", skill)
        self.assertIn("ingest-jd", skill)
        self.assertIn("Silencio ≠ sí", skill)
        self.assertNotIn("--require-factcheck", skill)


class DoctorTests(unittest.TestCase):
    def test_doctor_en_kit_vacio_sale_cero(self) -> None:
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "cvtool.py"), "doctor"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("cvtool doctor", proc.stdout)
        self.assertIn("siguiente:", proc.stdout)
        self.assertIn("inicializa mi base", proc.stdout)


if __name__ == "__main__":
    unittest.main()
