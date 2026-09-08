from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import dump_yaml, load_yaml  # noqa: E402
from copy_to_cv import main as copy_main  # noqa: E402
from factcheck import run_factcheck  # noqa: E402
from helpers import write_vault  # noqa: E402
from match import run_match  # noqa: E402
from render_cv import to_docx, to_markdown, to_pdf  # noqa: E402
from scaffold_defaults import scaffold  # noqa: E402
from validate_jd import validate_jd  # noqa: E402
from verify_pdf import extract  # noqa: E402


DEMO_JD = {
    "titulo": "Desarrollador web junior",
    "empresa": "Acme Demo SL",
    "ciudad": None,
    "modalidad": "remoto",
    "seniority": "junior",
    "url": None,
    "formato_pedido": "pdf",
    "must_have": ["HTML", "CSS", "JavaScript", "TypeScript", "Git"],
    "nice_to_have": ["PHP"],
    "keywords": {
        "t1": [
            "Desarrollador web junior",
            "HTML",
            "CSS",
            "JavaScript",
            "TypeScript",
            "Angular",
            "APIs REST",
            "SQL",
        ],
        "t2": ["PostgreSQL", "Git"],
        "t3": [],
    },
    "knockouts": [],
    "riesgos": [],
    "anios_experiencia_min": 0,
    "certificaciones_obligatorias": [],
    "preguntas": [],
}


class E2EEjemplosTests(unittest.TestCase):
    """Smoke: vault demo → validate-jd → match → scaffold → render → checks PDF."""

    def test_pipeline_con_vault_temporal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = write_vault(root)
            ej = ROOT / "ejemplos" / "vault-minimo"
            if ej.is_dir():
                for name in (
                    "perfil.yaml",
                    "evidencias.yaml",
                    "skills.yaml",
                    "familias.yaml",
                    "constraints.yaml",
                    "aliases.yaml",
                ):
                    src = ej / name
                    if src.exists():
                        shutil.copy2(src, base / name)

            plantillas = root / "plantillas"
            self.assertEqual(validate_jd(DEMO_JD), [])
            gaps, veredicto = run_match(DEMO_JD, base_dir=base)
            self.assertIn(veredicto["resultado"], {"aplicar", "aplicar_con_reservas"})
            self.assertGreaterEqual(gaps["score_t1"], 0.4)

            written = scaffold(base, plantillas)
            self.assertTrue(written)
            cv_path = plantillas / "cv_default_dev.yaml"
            self.assertTrue(cv_path.exists())

            cv = load_yaml(cv_path)
            perfil = load_yaml(base / "perfil.yaml")
            cv["nombre"] = perfil["nombre"]
            cv["contacto"] = perfil["contacto"]

            out = root / "out"
            out.mkdir()
            (out / "curriculum.md").write_text(to_markdown(cv), encoding="utf-8")
            pdf = out / "curriculum.pdf"
            to_pdf(cv, pdf)
            to_docx(cv, out / "curriculum.docx")
            self.assertTrue(pdf.exists() and pdf.stat().st_size > 1000)

            from pypdf import PdfReader

            reader = PdfReader(str(pdf))
            self.assertEqual(len(reader.pages), 1)
            text = extract(pdf).lower()
            self.assertIn("@", text)
            self.assertIn(str(perfil["contacto"]["ciudad"]).lower(), text)
            self.assertIn("perfil profesional", text)

            _g2, v2 = run_match(DEMO_JD, cv=cv, base_dir=base)
            self.assertIn(v2["resultado"], {"aplicar", "aplicar_con_reservas"})

            # Gate copy: factcheck + pack_estado aprobado
            pack = root / "candidatura"
            pack.mkdir()
            # Bullets con evidencia_id para pasar factcheck de calidad
            for bloque in (cv.get("experiencia") or []) + (cv.get("proyectos") or []):
                new_bullets = []
                for i, b in enumerate(bloque.get("bullets") or []):
                    if isinstance(b, str):
                        new_bullets.append({"texto": b, "evidencia_id": f"e2e-{i}"})
                    elif isinstance(b, dict) and not b.get("evidencia_id"):
                        b = dict(b)
                        b["evidencia_id"] = f"e2e-{i}"
                        new_bullets.append(b)
                    else:
                        new_bullets.append(b)
                bloque["bullets"] = new_bullets
            dump_yaml(pack / "cv.yaml", cv)
            dump_yaml(pack / "gaps.yaml", {"huerfanas": [], "score_t1": gaps["score_t1"]})
            dump_yaml(
                pack / "meta.yaml",
                {
                    "empresa": "Acme Demo SL",
                    "puesto": "Desarrollador web junior",
                    "pack_estado": "aprobado",
                    "listo_para_enviar": False,
                },
            )
            (pack / "presentacion.md").write_text(
                "En Empresa A trabajé HTML CSS TypeScript. "
                "Acme publica producto de facturación. Puedo hablar el jueves.",
                encoding="utf-8",
            )
            (pack / "outreach.md").write_text(
                "Vi el anuncio. HTML y TypeScript en Empresa A. ¿15 minutos?",
                encoding="utf-8",
            )
            report = run_factcheck(pack, base)
            self.assertTrue(report["ok"], report)
            dump_yaml(pack / "factcheck.yaml", report)
            dest = root / "cv"
            dest.mkdir()
            sys.argv = [
                "copy_to_cv.py",
                "--from-dir",
                str(pack),
                "--to-dir",
                str(dest),
            ]
            self.assertEqual(copy_main(), 0)
            self.assertTrue((dest / "cv.yaml").exists())


if __name__ == "__main__":
    unittest.main()
