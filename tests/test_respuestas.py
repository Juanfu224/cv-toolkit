from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import dump_yaml  # noqa: E402
from render_respuestas import render_respuestas  # noqa: E402


class RenderRespuestasTests(unittest.TestCase):
    def test_plantilla_y_caracteres(self) -> None:
        text = render_respuestas(
            {
                "respuestas": [
                    {
                        "pregunta": "¿Preaviso?",
                        "respuesta": "15 días",
                        "limite": 200,
                        "fuente": "constraints.yaml",
                        "necesita_confirmacion": False,
                    },
                    {
                        "pregunta": "¿Salario?",
                        "respuesta": "NECESITA_CONFIRMACION",
                        "fuente": "salary",
                        "necesita_confirmacion": True,
                    },
                ]
            }
        )
        self.assertIn("## ¿Preaviso?", text)
        self.assertIn("Caracteres: 7 / 200", text)
        self.assertIn("Fuente: constraints.yaml", text)
        self.assertIn("NECESITA_CONFIRMACION", text)

    def test_cvtool_respuestas_escribe_archivo(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data.yaml"
            out = Path(tmp) / "respuestas.md"
            dump_yaml(
                data,
                {
                    "respuestas": [
                        {
                            "pregunta": "Hola",
                            "respuesta": "Mundo",
                            "fuente": "test",
                            "necesita_confirmacion": False,
                        }
                    ]
                },
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "cvtool.py"),
                    "respuestas",
                    "--data",
                    str(data),
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
                check=False,
                cwd=str(ROOT),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            body = out.read_text(encoding="utf-8")
            self.assertIn("## Hola", body)
            self.assertIn("Mundo", body)


if __name__ == "__main__":
    unittest.main()
