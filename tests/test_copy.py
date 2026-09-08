from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from copy_to_cv import main as copy_main  # noqa: E402


class CopyToCvTests(unittest.TestCase):
    def test_borra_pdf_nombrados_viejos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "curriculum.pdf").write_bytes(b"%PDF-new")
            (src / "CV_NombrePrueba_Nuevo_Empresa.pdf").write_bytes(b"%PDF-named")
            stale = dest / "CV_NombrePrueba_Viejo_Empresa.pdf"
            stale.write_bytes(b"%PDF-old")
            sys.argv = ["copy_to_cv.py", "--from-dir", str(src), "--to-dir", str(dest)]
            self.assertEqual(copy_main(), 0)
            self.assertFalse(stale.exists())
            self.assertTrue((dest / "curriculum.pdf").exists())
            self.assertTrue((dest / "CV_NombrePrueba_Nuevo_Empresa.pdf").exists())


if __name__ == "__main__":
    unittest.main()
