"""Current catalog/source and derived-view migration contracts, isolated from the lab."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
checker=module('check_traceability');renderer=module('render_qa_case_tables')

class TraceabilityTests(unittest.TestCase):
    def test_real_catalog_and_derived_conflicts(self):
        text=checker.cat.PLAN.read_text()
        self.assertEqual(checker.validate(checker.ROOT,text),[])
        out=renderer.render(text)
        self.assertIn('231 TC plus 8 E2E',out)
        self.assertIn('needs-decision',out)
        self.assertIn('human manual',out)
        self.assertNotEqual(out,renderer.render(text.replace('FAIL - the administrator','FAIL - changed observation')))

    def test_unknown_case_mapping_rejected(self):
        text=checker.cat.PLAN.read_text().replace('| TC-AUTH-01 |\n','| TC-AUTH-99 |\n',1)
        self.assertTrue(checker.validate(checker.ROOT,text))

    def test_missing_spec_heading_and_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'spec files').mkdir();(root/'spec files/spec.md').write_text('# Spec\n## Login\n')
            self.assertEqual(checker.validate_source('spec.md#Login',root),[])
            for source in ['spec.md#Missing','missing.md','../spec.md#Login']:
                self.assertTrue(checker.validate_source(source,root),source)

    def test_duplicate_case_and_malformed_matrix_rejected(self):
        text=checker.cat.PLAN.read_text()
        for bad in [text.replace('#### TC-AUTH-02','#### TC-AUTH-01',1),
                    text.replace('| REQ-AUTH-01 | Valid credentials','| REQ-AUTH-99 | Valid credentials',1)]:
            self.assertTrue(checker.validate(checker.ROOT,bad))

if __name__=='__main__':unittest.main()
