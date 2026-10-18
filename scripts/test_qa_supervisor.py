"""Lifecycle tests use a fake runtime driver only; never access labs or Docker."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('supervisor',Path(__file__).with_name('qa_supervisor.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
fixture_spec=importlib.util.spec_from_file_location('fixtures',Path(__file__).with_name('test_qa_transport.py'))
f=importlib.util.module_from_spec(fixture_spec);fixture_spec.loader.exec_module(f)

UUID='12345678-1234-1234-1234-123456789abc'


class FakeDriver:
    def __init__(self,root,q,grant,ledger):
        self.root=root;self.q=q;self.grant=grant;self.ledger=ledger
        self.events=[];self.bad_proof=False;self.fail=False;self.timeout=False
        self.cleanup_ok=True;self.crash=False;self.empty=False

    def verify(self,plan):
        self.events.append('verify')
        return dict(lab_uuid=UUID,target_revision=('b'*40 if self.bad_proof else 'a'*40),
            origin='http://127.0.0.1:18080',observed_at=s.t.x.now(),exclusive=True,
            runtime_identity_verified=True,baseline_verified=True,recovery_verified=True,
            deployment_clean=True)

    def run(self,plan,timeout):
        self.events.append('run')
        state=self.ledger.snapshot(UUID)
        assert state['attempts'][0]['status']=='running', 'Must persist consumption before invocation'
        if self.crash:raise KeyboardInterrupt()
        if self.timeout:raise TimeoutError('synthetic secret must never be persisted')
        if self.fail:raise RuntimeError('synthetic secret must never be persisted')
        (self.root/'evidence'/'E1.json').write_text('{"observed":"synthetic assertion"}')
        return dict(result='PASS',evidence={} if self.empty else {
            'E1':dict(verdict='PASS',observed='Synthetic sidebar hidden and redirect',reference='E1.json')},reason='')

    def cancel(self,plan):self.events.append('cancel')
    def cleanup(self,plan):self.events.append('cleanup');return self.cleanup_ok


class SupervisorTests(unittest.TestCase):
    def fixture(self,root):
        q,j=f.TransportTests().fixture(root)
        ledgerdir=root/'supervisor';ledgerdir.mkdir(mode=0o700)
        ledger=s.Ledger(ledgerdir)
        grant=dict(version=1,mode='supervised live',explicit_start=True,reviewed_by='Synthetic reviewer',
            queue_hash=q['scope_hash'],owner='Reviewer',set='set',session='session',lab_uuid=UUID,
            target_revision='a'*40,expires_at='2099-01-01T00:00:00+00:00')
        driver=FakeDriver(root,q,grant,ledger)
        return q,j,ledger,grant,driver

    def call(self,root,q,j,ledger,grant,driver):
        return s.supervise(q,j,grant,ledger,root/'state',root/'bridge',driver)

    def test_durable_consumption_cleanup_and_complete_item_result(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            result=self.call(root,q,j,l,g,driver)
            self.assertEqual(result['result'],'PASS')
            self.assertEqual(driver.events,['verify','verify','run','cleanup','verify'])
            state=l.snapshot(UUID)
            self.assertEqual(state['attempts'][0]['status'],'complete')
            self.assertFalse(state['halted'])
            self.assertFalse(j['active_case']['actions'], 'Offline journal must not be promoted/mutated')

    def test_offline_or_wrong_grant_is_not_live_start(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            for field,value in [('mode','offline'),('explicit_start',False),('owner','Other'),
                ('target_revision','b'*40),('queue_hash','changed'),('expires_at','2000-01-01T00:00:00+00:00')]:
                grant=copy.deepcopy(g);grant[field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):self.call(root,q,j,l,grant,driver)
            self.assertFalse(driver.events)

    def test_lock_is_exclusive_across_independent_handles(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            other=s.Ledger(root/'supervisor')
            with l.claim(UUID):
                with self.assertRaises(ValueError):self.call(root,q,j,other,g,driver)
            self.assertFalse(driver.events)

    def test_host_claim_excludes_even_a_different_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            other_dir=root/'other-ledger';other_dir.mkdir(mode=0o700)
            other=s.Ledger(other_dir)
            with l.claim(UUID):
                with self.assertRaises(ValueError):
                    with other.claim(UUID):self.fail('Different ledger bypassed host exclusion')
                with self.assertRaises(ValueError):
                    with s.control.claim():self.fail('Controller bypassed supervisor claim')

    def test_bad_runtime_proof_never_dispatches(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root);driver.bad_proof=True
            with self.assertRaises(ValueError):self.call(root,q,j,l,g,driver)
            self.assertNotIn('run',driver.events)
            self.assertFalse(l.snapshot(UUID)['attempts'])

    def test_action_replay_rejected_even_with_different_session(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            self.call(root,q,j,l,g,driver)
            # Delete synthetic evidence to isolate replay rejection from overwrite guards.
            (root/'evidence'/'E1.json').unlink()
            j['session_id']='another';j.pop('journal_hash');j['journal_hash']=s.t.x.queue.cat.digest(j)
            g['session']='another'
            with self.assertRaises(ValueError):self.call(root,q,j,l,g,driver)
            self.assertEqual(driver.events.count('run'),1)

    def test_timeout_exception_and_cleanup_failure_halt_without_secret_leak(self):
        for failure in ('timeout','fail','cleanup','empty','crash'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as d:
                root=Path(d);q,j,l,g,driver=self.fixture(root)
                if failure=='cleanup':driver.cleanup_ok=False
                else:setattr(driver,failure,True)
                with self.assertRaises((ValueError,KeyboardInterrupt)):self.call(root,q,j,l,g,driver)
                state=l.snapshot(UUID)
                self.assertTrue(state['halted'])
                self.assertNotIn('synthetic secret',json.dumps(state))
                self.assertIn('cleanup',driver.events)
                if failure in ('timeout','fail','crash'):self.assertIn('cancel',driver.events)
                self.assertNotEqual(state['attempts'][0]['status'],'complete')

    def test_persisted_running_attempt_survives_new_ledger_object(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            plan=s.t.prepare(q,j,root/'state',root/'bridge')
            with l.claim(UUID):l.consume(UUID,plan)
            restarted=s.Ledger(root/'supervisor')
            with self.assertRaises(ValueError):self.call(root,q,j,restarted,g,driver)
            self.assertFalse(driver.events)

    def test_five_batch_budget_is_durable_across_handles(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            plan=s.t.prepare(q,j,root/'state',root/'bridge')
            for i in range(5):
                changed=copy.deepcopy(plan);changed['case']=f'TC-SYNTHETIC-{i}';changed['batch']=f'set-{i}'
                with l.claim(UUID):l.consume(UUID,changed);l.finish(UUID,True,{'result':'synthetic'})
            other=s.Ledger(root/'supervisor');plan['case']='TC-SYNTHETIC-6';plan['batch']='sixth'
            with other.claim(UUID),self.assertRaisesRegex(ValueError,'five-batch'):other.consume(UUID,plan)

    def test_corrupt_state_and_failed_consumption_cannot_dispatch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            with patch.object(l,'save',side_effect=OSError('synthetic persistence failure')):
                with self.assertRaises(OSError):self.call(root,q,j,l,g,driver)
            self.assertNotIn('run',driver.events)
            path=root/'supervisor'/f'{UUID}.json';path.write_text('{"invalid":true}');path.chmod(0o600)
            driver.events.clear()
            with self.assertRaises(ValueError):self.call(root,q,j,l,g,driver)
            self.assertFalse(driver.events)

    def test_live_receipt_fields_and_staleness_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            plan=s.t.prepare(q,j,root/'state',root/'bridge');proof=driver.verify(plan)
            for field,value in [('observed_at','2000-01-01T00:00:00+00:00'),
                ('lab_uuid','87654321-1234-1234-1234-123456789abc'),('deployment_clean',False),
                ('runtime_identity_verified',False),('recovery_verified',False),('origin','http://unsafe.invalid')]:
                changed=copy.deepcopy(proof);changed[field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):s.proof_check(changed,plan,UUID)

    def test_failure_verdict_is_retained_without_claiming_product_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root);original=driver.run
            def failed_assertion(plan,timeout):
                outcome=original(plan,timeout)
                outcome.update(result='FAIL',reason='Synthetic expected-item violation')
                outcome['evidence']['E1']['verdict']='FAIL'
                return outcome
            driver.run=failed_assertion
            result=self.call(root,q,j,l,g,driver)
            self.assertEqual(result['result'],'FAIL')
            self.assertEqual(l.snapshot(UUID)['attempts'][0]['result']['result'],'FAIL')
            self.assertFalse(l.snapshot(UUID)['halted'], 'Restored product failure is not unresolved infrastructure')

    def test_parser_cleanup_failure_cannot_be_overridden_by_driver_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root);original=driver.run
            def missing_browser_cleanup(plan,timeout):
                outcome=original(plan,timeout);outcome['restored']=False;return outcome
            driver.run=missing_browser_cleanup
            with self.assertRaises(ValueError):self.call(root,q,j,l,g,driver)
            self.assertTrue(l.snapshot(UUID)['halted'])

    def test_prior_offline_result_does_not_substitute_for_supervised_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            # Isolate the lifecycle proof check from the transport prefix validator.
            plan=s.t.prepare(q,j,root/'state',root/'bridge')
            j['results']=[dict(case='TC-SYNTHETIC-PRIOR',result='PASS')]
            with patch.object(s.t,'prepare',return_value=plan):
                with self.assertRaisesRegex(ValueError,'Prior offline result'):self.call(root,q,j,l,g,driver)
            self.assertFalse(driver.events)

    def test_returned_elapsed_overrun_cancels_and_halts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            with patch.object(s.time,'monotonic',side_effect=[0,100,101,102]):
                with self.assertRaises(ValueError):self.call(root,q,j,l,g,driver)
            self.assertTrue(l.snapshot(UUID)['halted'])
            self.assertIn('cancel',driver.events)
            self.assertIn('cleanup',driver.events)

    def test_private_store_and_symlink_lock_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q,j,l,g,driver=self.fixture(root)
            (root/'supervisor').chmod(0o755)
            with self.assertRaises(ValueError):s.Ledger(root/'supervisor')
            (root/'supervisor').chmod(0o700)
            (root/'supervisor'/f'{UUID}.lock').symlink_to(root/'state'/'restricted-email')
            with self.assertRaises(ValueError):self.call(root,q,j,l,g,driver)


if __name__=='__main__':unittest.main()
