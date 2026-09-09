from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from common import dump_yaml, load_yaml  # noqa: E402
from helpers import write_vault  # noqa: E402
from match import run_match  # noqa: E402
from refresh_pack import main as refresh_main  # noqa: E402
from refresh_pack import refresh_pack  # noqa: E402
from scaffold_defaults import scaffold  # noqa: E402


DEMO_JD = {
    "titulo": "Desarrollador web junior",
    "empresa": "Acme Demo SL",
    "ciudad": None,
    "modalidad": "remoto",
    "seniority": "junior",
    "url": None,
    "formato_pedido": "pdf",
    "must_have": ["HTML", "CSS", "JavaScript"],
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

PRES_OK = (
    "Desarrollador web con Angular y TypeScript en Empresa A. "
    "He construido interfaces y APIs REST con HTML, CSS y SQL. "
    "Puedo avanzar el stack del puesto esta misma semana."
)


def _seed_pack(root: Path, *, presentacion: str = PRES_OK) -> tuple[Path, Path]:
    base = write_vault(root)
    plantillas = root / "plantillas"
    scaffold(base, plantillas)
    cv = load_yaml(plantillas / "cv_default_dev.yaml")
    pack = root / "candidatura"
    pack.mkdir()
    dump_yaml(pack / "cv.yaml", cv)
    dump_yaml(pack / "jd.yaml", DEMO_JD)
    dump_yaml(
        pack / "meta.yaml",
        {
            "empresa": "Acme Demo SL",
            "puesto": "Desarrollador web junior",
            "fecha": "2026-09-09",
            "familia": "dev",
            "veredicto": "aplicar",
            "listo_para_enviar": False,
            "pack_estado": "pendiente",
            "formato_envio": "pdf",
        },
    )
    gaps, veredicto = run_match(DEMO_JD, cv=cv, base_dir=base)
    dump_yaml(pack / "gaps.yaml", gaps)
    dump_yaml(pack / "veredicto.yaml", veredicto)
    (pack / "presentacion.md").write_text(presentacion, encoding="utf-8")
    (pack / "outreach.md").write_text(
        "Vi el anuncio de Acme. Trabajo HTML y TypeScript. ¿15 minutos esta semana?",
        encoding="utf-8",
    )
    dump_yaml(
        pack / "respuestas_data.yaml",
        {
            "respuestas": [
                {
                    "pregunta": "¿Disponibilidad?",
                    "respuesta": "Incorporación según preaviso del contrato actual.",
                    "fuente": "constraints",
                    "necesita_confirmacion": False,
                }
            ]
        },
    )
    return pack, base


class RefreshPackTests(unittest.TestCase):
    def test_refresh_deja_editado_y_regenera_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack, base = _seed_pack(Path(tmp))
            (pack / "curriculum.pdf").write_bytes(b"%PDF-1.4 stale")
            (pack / "curriculum.md").write_text("STALE\n", encoding="utf-8")

            result = refresh_pack(pack, base)
            self.assertEqual(result["pack_estado"], "editado")
            meta = load_yaml(pack / "meta.yaml")
            self.assertEqual(meta["pack_estado"], "editado")
            self.assertFalse(meta["listo_para_enviar"])
            self.assertTrue((pack / "curriculum.pdf").exists())
            self.assertGreater((pack / "curriculum.pdf").stat().st_size, 1000)
            md = (pack / "curriculum.md").read_text(encoding="utf-8")
            self.assertNotIn("STALE", md)
            self.assertNotIn("None ·", md)
            self.assertTrue((pack / "factcheck.yaml").exists())
            self.assertTrue((pack / "respuestas.md").exists())
            self.assertTrue((pack / "pack_report.yaml").exists())
            self.assertTrue(list(pack.glob("CV_*.pdf")))

    def test_refresh_preserva_presentacion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            custom = (
                "MARKER_CANDIDATO_2026 con Angular en Empresa A. "
                "Evidencia de APIs REST y SQL. CTA breve sin clichés."
            )
            pack, base = _seed_pack(Path(tmp), presentacion=custom)
            refresh_pack(pack, base)
            self.assertEqual(
                (pack / "presentacion.md").read_text(encoding="utf-8"), custom
            )

    def test_refresh_factcheck_fail_deja_editado_y_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack, base = _seed_pack(
                Path(tmp),
                presentacion=(
                    "No tengo DOORS. Sí Angular en Empresa A. CTA breve."
                ),
            )
            result = refresh_pack(pack, base)
            self.assertFalse(result["factcheck_ok"])
            self.assertEqual(load_yaml(pack / "meta.yaml")["pack_estado"], "editado")

            buf = io.StringIO()
            with mock.patch.object(sys, "argv", ["refresh_pack", "--dir", str(pack)]):
                with mock.patch("refresh_pack.refresh_pack", return_value=result):
                    with mock.patch("sys.stdout", buf):
                        code = refresh_main()
            out = buf.getvalue()
            self.assertEqual(code, 1)
            self.assertIn("refresh: DONE", out)
            self.assertIn("factcheck=FAIL", out)
            self.assertNotIn("refresh: OK", out)

    def test_refresh_verify_fail_marca_editado(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack, base = _seed_pack(Path(tmp))
            with mock.patch(
                "refresh_pack.verify_ats", return_value=["más de 1 página (2)"]
            ):
                with self.assertRaises(SystemExit) as ctx:
                    refresh_pack(pack, base)
            self.assertIn("verify falló", str(ctx.exception))
            meta = load_yaml(pack / "meta.yaml")
            self.assertEqual(meta["pack_estado"], "editado")
            self.assertFalse(meta["listo_para_enviar"])


if __name__ == "__main__":
    unittest.main()
