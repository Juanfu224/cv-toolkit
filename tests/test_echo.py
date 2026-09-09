from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from common import is_echo_bullet, is_echo_text  # noqa: E402


class EchoHeuristicTests(unittest.TestCase):
    def test_exact_dup_is_echo(self) -> None:
        self.assertTrue(is_echo_text("Implementé X en Y", "Implementé X en Y"))

    def test_star_elaboration_is_not_echo(self) -> None:
        self.assertFalse(
            is_echo_text("Implementé X", "Implementé X en producción con monitoreo")
        )

    def test_near_identical_length_containment_is_echo(self) -> None:
        # Longitudes similares + contención → eco (ratio ≥ 0.85)
        self.assertTrue(
            is_echo_text(
                "Desarrollé APIs REST con PHP",
                "Desarrollé APIs REST con PHP.",
            )
        )

    def test_distinct_clauses_bullet_ok(self) -> None:
        self.assertFalse(
            is_echo_bullet(
                "Implementé interfaces con Angular. Reduje el tiempo de carga percibido"
            )
        )

    def test_echo_bullet_fails(self) -> None:
        self.assertTrue(is_echo_bullet("Implementé X en Y. Implementé X en Y"))


if __name__ == "__main__":
    unittest.main()
