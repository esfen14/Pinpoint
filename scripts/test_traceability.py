"""Isolated traceability contract tests; no application or lab required."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("checker", Path(__file__).with_name("check_traceability.py"))
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TraceabilityTests(unittest.TestCase):
    def check(self, rows, plan="#### J1-01 Login\n#### BB-01\n| BB-01 | Acceptance |"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "spec files").mkdir()
            (root / "spec files" / "spec.md").write_text("# Spec\n## Login\n")
            trac = "# Traceability\n\n| ID | Source Spec/Journey | ISO Characteristic | Env | Verification | Status | Notes |\n" + rows
            return checker.validate(root, plan, trac)

    def row(self, case="J1-01", source="spec.md#Login", iso="SE", env="VM",
            ver="agent", status="untested", notes=""):
        return (f"| {case} | {source} | {iso} | {env} | {ver} | {status} | {notes} |")

    def test_valid(self):
        self.assertEqual(self.check(self.row() + "\n" + self.row("BB-01")), [])

    def test_bad_case_and_heading(self):
        errors = self.check(self.row("J1-010", "spec.md#Missing"))
        self.assertTrue(any("unknown case" in e for e in errors))
        self.assertTrue(any("heading" in e for e in errors))

    def test_missing_and_duplicate(self):
        errors = self.check(self.row() + "\n" + self.row())
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_pass_needs_evidence(self):
        self.assertTrue(any("evidence" in e for e in self.check(self.row(status="pass", notes=""))))

    def test_bad_status(self):
        self.assertTrue(any("invalid status" in e for e in self.check(self.row(status="green"))))

    def test_malformed_row_not_ignored(self):
        self.assertTrue(any("malformed" in e for e in self.check("| J1-01 | x |")))

    def test_outside_spec_rejected(self):
        self.assertTrue(any("spec file not found" in e for e in self.check(self.row(source="../spec.md#Login"))))


if __name__ == "__main__":
    unittest.main()
