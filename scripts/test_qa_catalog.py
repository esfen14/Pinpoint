"""Catalog migration regressions, using real procedures without touching a lab."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('catalog', Path(__file__).with_name('qa_catalog.py'))
cat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cat)

class CatalogTests(unittest.TestCase):
    def test_real_counts_order_and_full_procedures(self):
        cases = cat.load_catalog()
        self.assertEqual(len(cases), 239)
        self.assertEqual(len({r for c in cases.values() for r in c['requirements']}),193)
        self.assertIn(cases['TC-DI-05']['priority'],('H','M','L'))
        self.assertEqual(sum(k.startswith('E2E-') for k in cases), 8)
        self.assertEqual(cases['TC-AUTH-01']['status'], 'pass')
        self.assertEqual(cases['TC-DI-05']['module'], 'DI')
        self.assertTrue(cases['TC-DI-05']['dependencies'])
        self.assertTrue(cases['E2E-04']['expectations'])
        self.assertLess(cases['TC-AUTH-05']['order'], cases['TC-AUTH-01']['order'])
        self.assertEqual(cases['TC-SEQ-09']['phase'], 15)

    def test_conflicts_and_absent_summary_columns(self):
        c = cat.load_catalog()
        self.assertEqual(c['TC-DSC-01']['status'], 'needs-decision')
        self.assertEqual(c['TC-ACK-06']['status'], 'needs-decision')
        self.assertEqual(c['TC-EDG-01']['status'], 'untested')
        self.assertIsNone(c['TC-EDG-01']['summary_result'])
        self.assertEqual(c['TC-DX-01']['status'], 'needs-decision')
        self.assertEqual(c['TC-NFR-07']['status'], 'fail')
        self.assertEqual(c['TC-ACC-06']['status'], 'fail')

    def test_unknown_prerequisite_is_not_silently_ignored(self):
        text=cat.PLAN.read_text().replace('| TC-AUTH-06 | TC-AUTH-05 |','| TC-AUTH-06 | TC-AUTH-99 |',1)
        with self.assertRaisesRegex(ValueError,'unknown prerequisite'):
            cat.parse_catalog(text)

    def test_shorthand_and_ranges(self):
        self.assertEqual(cat.expand_ids('TC-AUTH-05, 06, TC-ACC-01 to 03'),
                         ['TC-AUTH-05','TC-AUTH-06','TC-ACC-01','TC-ACC-02','TC-ACC-03'])

    def test_duplicate_missing_and_unknown_mapping_rejected(self):
        text = cat.PLAN.read_text()
        for bad in [text.replace('#### TC-AUTH-02', '#### TC-AUTH-01', 1),
                    text.replace('\n**Expected result**\n', '\n**Missing result**\n', 1),
                    text.replace('| TC-AUTH-01 | Valid sign-in', '| TC-AUTH-99 | Valid sign-in', 1),
                    text.replace('| TC-AUTH-01 |\n', '| TC-AUTH-99 |\n', 1)]:
            with self.subTest(change=bad[:40]), self.assertRaises(ValueError):
                cat.parse_catalog(bad)

if __name__ == '__main__': unittest.main()
