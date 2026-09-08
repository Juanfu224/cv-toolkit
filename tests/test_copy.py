from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from copy_to_cv import main as copy_main  # noqa: E402


def _write_gates(
    src: Path,
    *,
    factcheck_ok: bool = True,
    pack_estado: str = "aprobado",
    write_meta: bool = True,
    write_factcheck: bool = True,
) -> None:
    if write_factcheck:
        ok = "true" if factcheck_ok else "false"
        (src / "factcheck.yaml").write_text(
            f"ok: {ok}\nconfianza: 1.0\nviolaciones: []\n",
            encoding="utf-8",
        )
    if write_meta:
        (src / "meta.yaml").write_text(
            f"empresa: Acme\npuesto: Dev\npack_estado: {pack_estado}\n",
            encoding="utf-8",
        )


class CopyToCvTests(unittest.TestCase):
    def test_borra_pdf_nombrados_viejos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            (src / "CV_NombrePrueba_Nuevo_Empresa.pdf").write_bytes(b"%PDF-named")
            (src / "CV_NombrePrueba_Nuevo_Empresa.md").write_text("# cv", encoding="utf-8")
            _write_gates(src)
            stale = dest / "CV_NombrePrueba_Viejo_Empresa.pdf"
            stale.write_bytes(b"%PDF-old")
            stale_md = dest / "CV_NombrePrueba_Viejo_Empresa.md"
            stale_md.write_text("old", encoding="utf-8")
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            self.assertEqual(copy_main(), 0)
            self.assertFalse(stale.exists())
            self.assertFalse(stale_md.exists())
            self.assertTrue((dest / "curriculum.pdf").exists())
            self.assertTrue((dest / "CV_NombrePrueba_Nuevo_Empresa.pdf").exists())
            self.assertTrue((dest / "CV_NombrePrueba_Nuevo_Empresa.md").exists())

    def test_bloquea_si_factcheck_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            _write_gates(src, factcheck_ok=False)
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            with self.assertRaises(SystemExit) as ctx:
                copy_main()
            self.assertIn("factcheck", str(ctx.exception).lower())
            self.assertFalse((dest / "curriculum.pdf").exists())

    def test_ok_string_no_cuenta_como_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            (src / "factcheck.yaml").write_text(
                'ok: "false"\nconfianza: 1.0\n', encoding="utf-8"
            )
            (src / "meta.yaml").write_text(
                "pack_estado: aprobado\n", encoding="utf-8"
            )
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            with self.assertRaises(SystemExit) as ctx:
                copy_main()
            self.assertIn("factcheck", str(ctx.exception).lower())
            self.assertFalse((dest / "curriculum.pdf").exists())

    def test_sin_factcheck_bloquea(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            _write_gates(src, write_factcheck=False)
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            with self.assertRaises(SystemExit) as ctx:
                copy_main()
            self.assertIn("factcheck.yaml", str(ctx.exception))

    def test_pack_estado_pendiente_bloquea(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            _write_gates(src, pack_estado="pendiente")
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            with self.assertRaises(SystemExit) as ctx:
                copy_main()
            self.assertIn("pack_estado", str(ctx.exception))
            self.assertFalse((dest / "curriculum.pdf").exists())

    def test_sin_meta_bloquea(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            _write_gates(src, write_meta=False)
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            with self.assertRaises(SystemExit) as ctx:
                copy_main()
            self.assertIn("meta.yaml", str(ctx.exception))

    def test_gates_ok_copia(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            (src / "outreach.md").write_text("Hola", encoding="utf-8")
            _write_gates(src)
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            self.assertEqual(copy_main(), 0)
            self.assertTrue((dest / "curriculum.pdf").exists())
            self.assertTrue((dest / "outreach.md").exists())

    def test_force_omite_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            sys.argv = [
                "copy_to_cv.py",
                "--from-dir",
                str(src),
                "--to-dir",
                str(dest),
                "--force",
            ]
            self.assertEqual(copy_main(), 0)
            self.assertTrue((dest / "curriculum.pdf").exists())


if __name__ == "__main__":
    unittest.main()
