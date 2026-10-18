"""Historical evidence must be attributable, current and complete before credit."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('ev',Path(__file__).with_name('qa_evidence.py'))
ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)

class EvidenceTests(unittest.TestCase):
    def fixture(self,root):
        p=root/'docs/test-runs/2026-10-17-example/REPORT.md';p.parent.mkdir(parents=True)
        p.write_text('Revision `abcdef1234`\nObserved real permission denied.\n')
        c={'TC-X-01':{'procedure_hash':'case','expectations':['permission denied']}}
        e=dict(case_id='TC-X-01',classification='accepted historical coverage',reviewed_by='Reviewer',
          impact_review='Relevant source and dependencies unchanged against target',reviewed_at='2026-10-18',
          case_hash='case',report=p.relative_to(root).as_posix(),report_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
          tested_revision='abcdef1234',execution_date='2026-10-17',covered_items={'E1':'Observed real permission denied.'},
          environment_compatible=True,requirements_unchanged=True)
        return c,dict(version=1,target_revision='a'*40,cutoff_approved=True,entries=[e])

    def test_complete_review_accepts_but_invalid_credit_does_not(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c,v=self.fixture(root);p=root/'review.json'
            p.write_text(json.dumps(v));self.assertIn('TC-X-01',ev.load_review(p,c,'a'*40,root))
            mutations=[lambda x:x.update(cutoff_approved=False),lambda x:x.update(target_revision='b'*40),
              lambda x:x['entries'][0].update(case_hash='old'),lambda x:x['entries'][0].update(covered_items={}),
              lambda x:x['entries'][0].update(report_sha256='old'),lambda x:x['entries'][0].update(tested_revision='bad'),
              lambda x:x['entries'][0].update(execution_date='2026-10-13'),lambda x:x['entries'][0].update(reviewed_by=''),
              lambda x:x['entries'][0].update(report='../outside/REPORT.md'),
              lambda x:x['entries'][0].update(environment_compatible=False)]
            for mutate in mutations:
                bad=copy.deepcopy(v);mutate(bad);p.write_text(json.dumps(bad))
                with self.subTest(bad=bad),self.assertRaises(ValueError):ev.load_review(p,c,'a'*40,root)

    def test_late_directory_date_does_not_override_actual_execution_date(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c,v=self.fixture(root);v['entries'][0]['execution_date']='2026-10-13'
            p=root/'review.json';p.write_text(json.dumps(v))
            self.assertEqual(len(ev.inventory(root)),1)
            with self.assertRaises(ValueError):ev.load_review(p,c,'a'*40,root)

    def test_partial_review_does_not_require_full_coverage_or_confer_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);c,v=self.fixture(root);v['entries'][0]['classification']='partial historical coverage'
            v['entries'][0]['covered_items']={};v['cutoff_approved']=False
            p=root/'review.json';p.write_text(json.dumps(v))
            self.assertEqual(ev.load_review(p,c,'a'*40,root)['TC-X-01']['classification'],'partial historical coverage')

if __name__=='__main__':unittest.main()
