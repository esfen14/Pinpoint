"""Module queues: disjoint ownership, immutable scope and conservative evidence reuse."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('queue', Path(__file__).with_name('qa_queue.py'))
queue = importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)

class QAQueueTests(unittest.TestCase):
    def catalog(self):
        c=queue.load_catalog()
        return {k:v for k,v in c.items() if k in ['TC-DI-01','TC-DI-05','TC-DI-06','TC-DI-07','TC-DI-08','TC-DI-09','TC-DI-11','TC-TOP-01','TC-SEQ-09','TC-DSC-01']}

    def test_default_pending_selection_and_exclusions(self):
        q=queue.prepare(['alice:Paeng:DI'], self.catalog(), 'a'*40)
        self.assertEqual(q['version'],2)
        self.assertEqual(q['sets'][0]['owner'],'Paeng')
        self.assertNotIn('TC-DI-01',[c['id'] for c in q['sets'][0]['cases']])
        self.assertTrue(q['sets'][0]['exclusions'])
        self.assertEqual(queue.check(q,self.catalog()),[])

    def test_explicit_nonpending_unknown_overlap_and_empty_rejected(self):
        for selections in [['one:A:TC-TOP-01'],['one:A:ZZ'],['one:A:DI','two:B:DI'],
                           ['one:A:DI','one:B:TC-SEQ-09'],['one:A:TC-DSC-01']]:
            with self.subTest(selections=selections),self.assertRaises(ValueError):
                queue.prepare(selections,self.catalog(),'a'*40)

    def test_recheck_is_explicit_and_still_excludes_conflicts(self):
        q=queue.prepare(['one:A:TC-TOP-01'],self.catalog(),'a'*40,purpose='recheck')
        self.assertEqual(q['sets'][0]['purpose'],'recheck')
        with self.assertRaises(ValueError):
            queue.prepare(['one:A:TC-DSC-01'],self.catalog(),'a'*40,purpose='recheck')

    def test_batches_isolate_risk_and_never_exceed_five(self):
        q=queue.prepare(['one:A:DI,TC-SEQ-09'],self.catalog(),'a'*40)
        for b in q['sets'][0]['batches']:
            self.assertLessEqual(len(b['ids']),5)
            if any(c['singleton'] for c in q['sets'][0]['cases'] if c['id'] in b['ids']):
                self.assertEqual(len(b['ids']),1)

    def test_freshness_detects_selected_change_and_does_not_expand(self):
        c=self.catalog();q=queue.prepare(['one:A:TC-DI-06'],c,'a'*40)
        changed=copy.deepcopy(c);changed['TC-DI-06']['steps']='changed'
        self.assertTrue(queue.check(q,changed))
        changed=copy.deepcopy(c);changed['TC-DI-01']['title']='unselected'
        self.assertEqual(queue.check(q,changed),[])
        self.assertEqual(len(q['sets'][0]['cases']),1)

    def test_tamper_and_legacy_rejected(self):
        q=queue.prepare(['one:A:DI'],self.catalog(),'a'*40)
        for mutate in [lambda v:v.update(version=1),lambda v:v['sets'][0].update(owner=''),
                       lambda v:v['sets'][0]['cases'].append(v['sets'][0]['cases'][0]),
                       lambda v:v['sets'][0]['batches'][0]['ids'].append('TC-BOGUS-99'),
                       lambda v:v['sets'][0]['cases'][0].update(steps='tampered')]:
            v=copy.deepcopy(q);mutate(v)
            with self.assertRaises(ValueError):queue.validate(v)

    def test_cli_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'q.json'
            args=[sys.executable,'-I',str(queue.ROOT/'scripts/qa_queue.py'),'prepare','--set','one:A:TC-DI-06','--target-revision','a'*40,'--output',str(out)]
            r=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('TC-DI-06',out.with_suffix('.md').read_text())
            self.assertNotEqual(subprocess.run(args,capture_output=True).returncode,0)

    def test_workflow_requires_explicit_start_and_fixed_scope(self):
        s=(queue.ROOT/'.agent/workflows/qa-run.md').read_text()
        for rule in ["Wait for the user's explicit start command",'Never select outside the saved case list','five-round limit']:
            self.assertIn(rule,s)

if __name__=='__main__':unittest.main()
