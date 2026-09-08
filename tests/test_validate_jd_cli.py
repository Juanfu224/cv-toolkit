from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import dump_yaml  # noqa: E402
from validate_jd import main as validate_jd_main  # noqa: E402


class ValidateJdCliTests(unittest.TestCase):
    def test_cli_ok_and_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.yaml"
            bad = Path(tmp) / "bad.yaml"
            dump_yaml(
                good,
                {
                    "titulo": "Desarrollador web",
                    "empresa": "Acme",
                    "must_have": ["TypeScript"],
                    "keywords": {
                        "t1": ["a", "b", "c", "d", "e"],
                        "t2": [],
                        "t3": [],
                    },
                },
            )
            dump_yaml(bad, {"titulo": "x"})
            sys.argv = ["validate_jd.py", str(good)]
            self.assertEqual(validate_jd_main(), 0)
            sys.argv = ["validate_jd.py", str(bad)]
            self.assertEqual(validate_jd_main(), 1)


if __name__ == "__main__":
    unittest.main()
