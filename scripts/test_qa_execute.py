"""Offline executor boundaries; no subprocess, browser, SSH or lab is executed."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('execution',Path(__file__).with_name('qa_execute.py'))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)

class ExecutorTests(unittest.TestCase):
    def fixture(self,root):
        catalog=x.queue.load_catalog();q=x.queue.prepare(['set:Paeng:TC-DI-06'],catalog,'a'*40)
        adapter=root/'adapter.ts';adapter.write_text('// synthetic fixture; never launched')
        evidence=root/'evidence';evidence.mkdir();(evidence/'observed.txt').write_text('sanitized observation')
        case=q['sets'][0]['cases'][0]
        case['execution']=dict(reviewed_by='Reviewer',mode='scripted automation',
            adapter=str(adapter),adapter_hash=x.queue.cat.digest(adapter.read_text()),
            actions=[['scripts/playwright-lab','--project','fixture','--grep','TC-DI-06','--retries=0']],
            timeout_seconds=60,step_timeout_seconds=10,prerequisites=['verified fixture'],
            recovery=['restore original fixture state'],human_required=False,
            evidence_dir=str(evidence),write_paths=[str(evidence)])
        # Synthetic source-reviewed mapping: no real adapter is launched.
        mapping=dict(status='implemented',mode='scripted automation',adapter=dict(
            path=str(adapter),title='TC-DI-06: synthetic fixture',project='qa-permissions',
            config='client/playwright.qa.config.ts'))
        case['coverage']=mapping
        case['execution'].update(coverage_hash=x.queue.cat.digest(mapping),selection=mapping['adapter'],
            actions=[x.queue.coverage.action_for(mapping)])
        x.queue.seal(q)
        preflight=dict(owner='Paeng',lab='synthetic-only',target_revision='a'*40,
            catalog_hash=case['source_hash'],exclusive=True,baseline_verified=True,
            recovery_verified=True,network_guard=True,live_authorized=False,observed_at=x.now())
        return q,preflight

    def test_investigation_queue_cannot_be_executed_as_a_product_case(self):
        with tempfile.TemporaryDirectory() as d:
            _,p=self.fixture(Path(d));catalog=x.queue.load_catalog()
            q=x.queue.prepare(['set:Paeng:TC-ACK-05'],catalog,'a'*40,purpose='investigate')
            s=x.start(q,'set','Paeng','session',p,True)
            x.begin_batch(q,s,q['sets'][0]['batches'][0]['id'])
            with self.assertRaisesRegex(ValueError,'investigation'):
                x.begin_case(q,s,'TC-ACK-05')

    def test_source_mapping_and_draft_card_do_not_establish_execution_readiness(self):
        catalog=x.queue.load_catalog()
        q=x.queue.prepare(['set:Paeng:TC-SS-04'],catalog,'a'*40)
        case=q['sets'][0]['cases'][0]
        case['execution']=x.queue.coverage.card_template(case['coverage'])
        with self.assertRaises(ValueError):x.validate_card(case)
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));case=q['sets'][0]['cases'][0]
            case['coverage']['status']='unmapped'
            with self.assertRaisesRegex(ValueError,'adapter'):x.validate_card(case)

    def test_no_start_wrong_owner_or_preflight_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d))
            for owner,start in [('Other',True),('Paeng',False)]:
                with self.assertRaises(ValueError):x.start(q,'set',owner,'session',p,start)
            p['exclusive']=False
            with self.assertRaises(ValueError):x.start(q,'set','Paeng','session',p,True)

    def test_missing_adapter_changed_source_and_extra_action_block(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));s=x.start(q,'set','Paeng','session',p,True)
            x.begin_batch(q,s,q['sets'][0]['batches'][0]['id'])
            card=q['sets'][0]['cases'][0]['execution'];card['adapter_hash']='bad';x.queue.seal(q)
            with self.assertRaises(ValueError):x.begin_case(q,s,'TC-DI-06')
            with self.assertRaises(ValueError):x.authorize_action(q,s,['bash','-c','anything'])

    def test_complete_evidence_and_cleanup_required(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));s=x.start(q,'set','Paeng','session',p,True)
            x.begin_batch(q,s,q['sets'][0]['batches'][0]['id']);x.begin_case(q,s,'TC-DI-06')
            evidence={f'E{i}':dict(verdict='PASS',observed='Observed fixture',reference='observed.txt')
                for i,_ in enumerate(q['sets'][0]['cases'][0]['expectations'],1)}
            with self.assertRaises(ValueError):x.record_result(q,s,'PASS',{},True)
            with self.assertRaisesRegex(ValueError,'action'):
                x.record_result(q,s,'PASS',evidence,True)
            x.authorize_action(q,s,q['sets'][0]['cases'][0]['execution']['actions'][0])
            x.record_result(q,s,'PASS',evidence,True)
            self.assertEqual(s['results'][0]['result'],'PASS')
            self.assertIsNone(s['active_case'])

    def test_cleanup_failure_halts_and_no_unlisted_case(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));s=x.start(q,'set','Paeng','session',p,True)
            x.begin_batch(q,s,q['sets'][0]['batches'][0]['id'])
            with self.assertRaises(ValueError):x.begin_case(q,s,'TC-TOP-01')
            x.begin_case(q,s,'TC-DI-06');x.record_result(q,s,'BLOCKED',{},False,reason='cleanup failed')
            self.assertEqual(s['status'],'halted')
            with self.assertRaises(ValueError):x.begin_batch(q,s,q['sets'][0]['batches'][0]['id'])

    def test_sixth_batch_and_reordered_batch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));s=x.start(q,'set','Paeng','session',p,True)
            s['batches_started']=['one','two','three','four','five']
            with self.assertRaises(ValueError):x.begin_batch(q,s,q['sets'][0]['batches'][0]['id'])

    def test_action_order_and_hidden_retries_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));s=x.start(q,'set','Paeng','session',p,True)
            x.begin_batch(q,s,q['sets'][0]['batches'][0]['id']);x.begin_case(q,s,'TC-DI-06')
            argv=q['sets'][0]['cases'][0]['execution']['actions'][0]
            x.authorize_action(q,s,argv)
            with self.assertRaises(ValueError):x.authorize_action(q,s,argv)

    def test_missing_adapter_can_be_recorded_blocked_without_execution(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));q['sets'][0]['cases'][0]['execution']={};x.queue.seal(q)
            s=x.start(q,'set','Paeng','session',p,True);x.begin_batch(q,s,q['sets'][0]['batches'][0]['id'])
            with self.assertRaises(ValueError):x.begin_case(q,s,'TC-DI-06')
            x.block_case(q,s,'TC-DI-06','No complete adapter; no attempt made')
            self.assertEqual(s['results'][0]['attempt'],0)
            self.assertEqual(s['results'][0]['result'],'BLOCKED')
            self.assertIsNone(s['active_batch'])

    def test_actual_five_blocked_batches_exhaust_the_session(self):
        with tempfile.TemporaryDirectory() as d:
            _,p=self.fixture(Path(d));catalog=x.queue.load_catalog()
            q=x.queue.prepare(['set:Paeng:SEQ'],catalog,'a'*40)
            s=x.start(q,'set','Paeng','session',p,True)
            for batch in q['sets'][0]['batches'][:5]:
                x.begin_batch(q,s,batch['id'])
                x.block_case(q,s,batch['ids'][0],'Unmapped fixture; no execution')
            self.assertEqual(len(s['batches_started']),5)
            with self.assertRaises(ValueError):x.begin_batch(q,s,q['sets'][0]['batches'][5]['id'])

    def test_no_pass_on_failure_missing_or_outside_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            q,p=self.fixture(Path(d));s=x.start(q,'set','Paeng','session',p,True)
            x.begin_batch(q,s,q['sets'][0]['batches'][0]['id']);x.begin_case(q,s,'TC-DI-06')
            evidence={f'E{i}':dict(verdict='FAIL',observed='failure',reference='../escape')
                for i,_ in enumerate(q['sets'][0]['cases'][0]['expectations'],1)}
            with self.assertRaises(ValueError):x.record_result(q,s,'PASS',evidence,True)

if __name__=='__main__':unittest.main()
