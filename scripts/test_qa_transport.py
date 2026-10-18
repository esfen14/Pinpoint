"""Transport preview contracts; all files synthetic, no Docker/browser/VM access."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('transport',Path(__file__).with_name('qa_transport.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class TransportTests(unittest.TestCase):
    def fixture(self,root):
        for name in ('state','bridge','evidence'):(root/name).mkdir(mode=0o700)
        for name in ('restricted-email','restricted-new-password'):
            path=root/'state'/name;path.write_text('synthetic-private-value');path.chmod(0o600)
        q=t.x.queue.prepare(['set:Reviewer:TC-SS-04'],t.x.queue.load_catalog(),'a'*40)
        case=q['sets'][0]['cases'][0];card=t.x.queue.coverage.card_template(case['coverage'])
        card.update(reviewed_by='Synthetic reviewer',timeout_seconds=60,step_timeout_seconds=10,
            human_required=False,prerequisites=['Synthetic Staff baseline'],
            evidence_dir=str(root/'evidence'),write_paths=[str(root/'evidence')])
        case['execution']=card;t.x.queue.seal(q)
        p=dict(owner='Reviewer',lab='synthetic',target_revision='a'*40,catalog_hash=case['source_hash'],
            observed_at=t.x.now(),exclusive=True,baseline_verified=True,recovery_verified=True,
            network_guard=True,live_authorized=False)
        s=t.x.start(q,'set','Reviewer','session',p,True)
        t.x.begin_batch(q,s,'set-001');t.x.begin_case(q,s,'TC-SS-04')
        s['journal_hash']=t.x.queue.cat.digest(s)
        return q,s

    def reseal(self,s):
        s.pop('journal_hash',None);s['journal_hash']=t.x.queue.cat.digest(s)

    def test_minimal_readonly_transport_and_no_secret_reads(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            plan=t.prepare(q,s,root/'state',root/'bridge')
            text=json.dumps(plan)
            self.assertFalse(plan['live_authorized'])
            self.assertIn('umask 077',t.BOOTSTRAP)
            self.assertIn('BLOCKED',plan['readiness'])
            self.assertNotIn('synthetic-private-value',text)
            self.assertNotIn('admin-password',text)
            self.assertNotIn('restricted-password',text)
            self.assertIn('--read-only',plan['docker_argv'])
            self.assertIn('none',plan['docker_argv'])
            self.assertIn('PINPOINT_QA_CASES=TC-SS-04',plan['docker_argv'])
            self.assertIn('PINPOINT_QA_RUN_DIR=/evidence',plan['docker_argv'])
            mounts=[plan['docker_argv'][i+1] for i,v in enumerate(plan['docker_argv']) if v=='--mount']
            self.assertTrue(any('dst=/work,readonly' in v for v in mounts))
            self.assertEqual(len([v for v in mounts if 'dst=/state/' in v]),2)
            self.assertTrue(all('readonly' in v for v in mounts if 'dst=/state/' in v))
            self.assertEqual(plan['case'],'TC-SS-04')

    def test_preview_never_opens_credential_values(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root);original=Path.open
            def guarded(path,*args,**kwargs):
                if path.parent==root/'state':raise AssertionError('Credential value read during preview')
                return original(path,*args,**kwargs)
            with patch.object(Path,'open',guarded):
                t.prepare(q,s,root/'state',root/'bridge')

    def test_draft_cards_and_offline_to_live_promotion_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            s['preflight']['live_authorized']=True;self.reseal(s)
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')
            s['preflight']['live_authorized']=False
            q['sets'][0]['cases'][0]['execution']['human_required']=True
            t.x.queue.seal(q);s['queue_hash']=q['scope_hash'];self.reseal(s)
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')

    def test_journal_identity_budget_action_and_freshness_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            for field,value in [('owner','Other'),('status','halted'),('queue_hash','changed'),
                                ('batches_started',['a']*6),('active_batch','unlisted')]:
                altered=copy.deepcopy(s);altered[field]=value;self.reseal(altered)
                with self.subTest(field=field),self.assertRaises(ValueError):t.prepare(q,altered,root/'state',root/'bridge')
            altered=copy.deepcopy(s);altered['active_case']['actions']=[{'argv':['used']}];self.reseal(altered)
            with self.assertRaises(ValueError):t.prepare(q,altered,root/'state',root/'bridge')
            altered=copy.deepcopy(s);altered['preflight']['observed_at']='2000-01-01T00:00:00+00:00';self.reseal(altered)
            with self.assertRaises(ValueError):t.prepare(q,altered,root/'state',root/'bridge')
            with patch.object(t.x.queue,'check',return_value=['source changed']):
                with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')
            altered=copy.deepcopy(s);altered['journal_hash']='modified'
            with self.assertRaises(ValueError):t.prepare(q,altered,root/'state',root/'bridge')

    def test_private_paths_credentials_and_no_evidence_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            for directory in ('state','bridge','evidence'):
                (root/directory).chmod(0o755)
                with self.subTest(directory=directory),self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')
                (root/directory).chmod(0o700)
            (root/'evidence'/'previous.json').write_text('retained')
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')
            (root/'evidence'/'previous.json').unlink()
            secret=root/'state'/'restricted-new-password';secret.chmod(0o644)
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')
            secret.unlink();secret.symlink_to(root/'state'/'restricted-email')
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')

    def test_case_result_prefix_cannot_skip_or_reorder_slots(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            s['results']=[dict(case='TC-HIS-01',result='PASS',restored=True)]
            self.reseal(s)
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')

    def test_existing_bridge_and_csv_mount_injection_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            (root/'bridge'/'web.sock').touch()
            with self.assertRaises(ValueError):t.prepare(q,s,root/'state',root/'bridge')
            injected=root/'state,readonly';injected.mkdir(mode=0o700)
            with self.assertRaises(ValueError):t.prepare(q,s,injected,root/'bridge')

    def test_legacy_runner_denies_current_config_before_any_external_command(self):
        script=Path(__file__).with_name('playwright-lab')
        for args in [['--config=playwright.qa.config.ts'],['--project=qa-permissions'],['-c','playwright.qa.config.ts'],
                     ['--config','./playwright.qa.config.ts'],
                     ['--config=playwright.modules.qa.config.ts'],['--project=qa-modules-2-9']]:
            result=subprocess.run(['bash',str(script),*args],capture_output=True,text=True,
                env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent'},timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('current-case',result.stderr)
        result=subprocess.run(['bash',str(script)],capture_output=True,text=True,
            env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','PINPOINT_QA_CASES':'TC-SS-04'},timeout=5)
        self.assertNotEqual(result.returncode,0);self.assertIn('current-case',result.stderr)

    def test_shell_preview_is_offline_and_does_not_read_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,s=self.fixture(root)
            qp=root/'queue.json';sp=root/'journal.json'
            qp.write_text(json.dumps(q));sp.write_text(json.dumps(s))
            result=subprocess.run(['bash',str(Path(__file__).with_name('playwright-lab')),
                '--qa-preview',str(qp),str(sp),str(root/'state'),str(root/'bridge')],
                capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            plan=json.loads(result.stdout);self.assertFalse(plan['live_authorized'])
            self.assertFalse((root/'bridge'/'web.sock').exists())
            self.assertFalse(list((root/'evidence').iterdir()))


if __name__=='__main__':unittest.main()
