"""Isolated checks for QA scope selection and saved queue validation."""

import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("qa_queue.py")
spec = importlib.util.spec_from_file_location("qa_queue", SCRIPT)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class QAQueueTests(unittest.TestCase):
    def catalog(self):
        return {
            "J1-01": {"iso": "FS", "status": "pass"},
            "J1-02": {"iso": "FS", "status": "untested"},
            "J1-03": {"iso": "FS", "status": "retest"},
            "J1-04": {"iso": "FS", "status": "fail-filed"},
            "J1-05": {"iso": "FS", "status": "needs-decision"},
            "J1-06": {"iso": "FS", "status": "won't-do"},
            "J2-01": {"iso": "SE", "status": "untested"},
        }

    def test_default_selection_is_pending_and_iso_scoped(self):
        result = queue.prepare(["alice-fs:FS:alice", "bob-se:SE:bob"], self.catalog())
        self.assertEqual([case["id"] for case in result["sets"][0]["cases"]],
                         ["J1-02", "J1-03"])
        self.assertEqual([case["id"] for case in result["sets"][1]["cases"]], ["J2-01"])
        self.assertEqual(result["sets"][1]["owner"], "bob")

    def test_explicit_subsets_allow_same_iso_with_distinct_owners(self):
        result = queue.prepare(["one:FS:alice:J1-02", "two:FS:bob:J1-03"], self.catalog())
        self.assertEqual([item["name"] for item in result["sets"]], ["one", "two"])

    def test_rejects_overlap_duplicate_names_and_nonpending_cases(self):
        for sets in (
            ["one:FS:alice", "two:FS:bob"],
            ["one:FS:alice:J1-02", "one:SE:bob"],
            ["one:FS:alice:J1-01"],
            ["one:FS:alice:J1-02,J1-02"],
        ):
            with self.subTest(sets=sets), self.assertRaises(ValueError):
                queue.prepare(sets, self.catalog())

    def test_rejects_wrong_iso_unknown_cases_and_empty_selections(self):
        for selection in ("one:FS:alice:J2-01", "one:FS:alice:J9-99",
                          "one:PE:alice", "one:XX:alice", "one:FS:"):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                queue.prepare([selection], self.catalog())

    def test_checks_only_selected_set_and_detects_scope_drift(self):
        catalog = self.catalog()
        result = queue.prepare(["one:FS:alice", "two:SE:bob"], catalog)
        catalog["J1-02"]["status"] = "pass"
        self.assertTrue(queue.check(result, catalog, "one"))
        self.assertEqual(queue.check(result, catalog, "two"), [])
        catalog["J2-01"]["expect"] = "changed requirement"
        self.assertTrue(queue.check(result, catalog, "two"))
        with self.assertRaises(ValueError):
            queue.check(result, catalog, "missing")

    def test_new_pending_cases_do_not_silently_expand_saved_scope(self):
        catalog = self.catalog()
        result = queue.prepare(["one:FS:alice"], catalog)
        catalog["J1-07"] = {"iso": "FS", "status": "untested"}
        self.assertEqual(queue.check(result, catalog), [])
        self.assertEqual(len(result["sets"][0]["cases"]), 2)

    def test_tampered_queue_is_rejected(self):
        result = queue.prepare(["one:FS:alice"], self.catalog())
        for mutate in (
            lambda value: value.update(version=99),
            lambda value: value["sets"][0].update(owner=""),
            lambda value: value["sets"][0]["cases"].append(value["sets"][0]["cases"][0]),
            lambda value: value["sets"][0]["cases"][0].update(iso="SE"),
        ):
            value = copy.deepcopy(result)
            mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                queue.check(value, self.catalog())

    def test_real_catalog_preview_contains_coordination_details(self):
        catalog = queue.load_catalog()
        result = queue.prepare(["one:FS:alice:J2-03,J5-11"], catalog)
        preview = queue.preview(result)
        for value in ("Module under test", "Device Inventory", "HUMAN",
                      "Prerequisites", "explicit start", "alice", "J2-03", "J5-11"):
            self.assertIn(value, preview)
        changed = copy.deepcopy(catalog)
        changed["J2-03"]["procedure_hash"] = "changed full procedure"
        self.assertTrue(queue.check(result, changed))

    def test_cli_prepares_checks_and_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = str(Path(temp) / "queue.json")
            command = [sys.executable, "-I", str(SCRIPT), "prepare", "--set",
                       "one:FS:alice:J2-03", "--output", output]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(Path(output).with_suffix(".md").exists())
            self.assertIn("J2-03", result.stdout)
            before = Path(output).read_bytes()
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(Path(output).read_bytes(), before)
            result = subprocess.run([sys.executable, "-I", str(SCRIPT), "check",
                                     "--queue", output, "--run", "one"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_preview_rebases_relative_evidence_links(self):
        directory = queue.ROOT / "docs" / "qa" / "queues"
        value = "See [run](../test-runs/example/REPORT.md#results) and [issue](https://example.test/1)."
        result = queue.preview_cell(value, directory)
        self.assertIn("[run](../../test-runs/example/REPORT.md#results)", result)
        self.assertIn("[issue](https://example.test/1)", result)

    def test_workflow_requires_explicit_start_and_fixed_scope(self):
        workflow = (queue.ROOT / ".agent/workflows/qa-run.md").read_text()
        for rule in ("Wait for the user's explicit start command", "never automatically",
                     "Never select outside the saved case list", "local",
                     "compare remaining cases", "five-round limit"):
            with self.subTest(rule=rule):
                self.assertIn(rule, workflow)


if __name__ == "__main__":
    unittest.main()
