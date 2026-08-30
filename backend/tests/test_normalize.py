import os
import tempfile
import unittest

# Point the DB at a temp file BEFORE importing app modules.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["KABILAI_DB_PATH"] = _tmp.name
os.environ["GUPSHUP_MOCK"] = "true"
os.environ["AGENT_MODEL"] = "test"

import sqlmodel  # noqa: E402

from app.core.database import engine, init_db  # noqa: E402
from app.core.normalize import normalize_phone  # noqa: E402


class NormalizeTests(unittest.TestCase):
    def test_10_digit(self) -> None:
        self.assertEqual(normalize_phone("9876543210"), "919876543210")

    def test_91_prefix(self) -> None:
        self.assertEqual(normalize_phone("919876543210"), "919876543210")

    def test_plus_91(self) -> None:
        self.assertEqual(normalize_phone("+919876543210"), "919876543210")

    def test_whitespace_and_dashes(self) -> None:
        self.assertEqual(normalize_phone("+91 98765-43210"), "919876543210")

    def test_drop_non_digits(self) -> None:
        self.assertEqual(normalize_phone("phone 98765 43210"), "919876543210")


class SeedTests(unittest.TestCase):
    def test_seed_runs_and_is_idempotent(self) -> None:
        init_db()
        from app.seed import seed

        seed()
        seed()  # second run must not raise (no duplicates)


if __name__ == "__main__":
    unittest.main()
