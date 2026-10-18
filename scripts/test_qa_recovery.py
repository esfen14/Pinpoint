"""Recovery contracts use disposable ledgers and synthetic proofs, never live tools."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

s=module('supervisor','qa_supervisor.py')
f=module('fixtures','test_qa_supervisor.py')


class RecoveryTests(unittest.TestCase):
    def fixture(self,root):
        q,j,ledger,grant,driver=f.SupervisorTests().fixture(root)
        driver.fail=True
        with self.assertRaises(ValueError):s.supervise(q,j,grant,ledger,root/'state',root/'bridge',driver)
        before=ledger.snapshot(f.UUID)
        self.assertTrue(before['halted'], 'Fixture must reach a consumed halt, not an unrelated preflight failure')
        self.assertEqual(len(before['attempts']),1)
        plan=dict(queue_hash='b'*64,target_revision='a'*40,baseline_hash='c'*64,bridge_origin='http://127.0.0.1:18080')
        review=dict(version=1,mode='supervised recovery',explicit_recovery=True,reviewed_by='Paeng',
            lab_uuid=f.UUID,source_checksum=before['checksum'],attempt_hash=s.t.x.queue.cat.digest(before['attempts'][-1]),
            next_queue_hash=plan['queue_hash'],target_revision=plan['target_revision'],baseline_hash=plan['baseline_hash'],evidence_hash='d'*64,
            expires_at=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat())
        proof=dict(lab_uuid=f.UUID,target_revision='a'*40,origin=plan['bridge_origin'],observed_at=s.t.x.now(),
            exclusive=True,runtime_identity_verified=True,baseline_verified=True,recovery_verified=True,deployment_clean=True,
            container_absent=True,bridge_absent=True,processes_absent=True,session_closed=True,
            evidence_hash='d'*64)
        return ledger,before,plan,review,proof

    def test_append_recovery_preserves_exact_original_archive_attempts_and_budgets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);l,before,plan,review,proof=self.fixture(root)
            raw=l.path(f.UUID,'json').read_bytes()
            with l.claim(f.UUID):
                l.recover(f.UUID,plan,review,proof)
                state=l.ready(f.UUID)
            self.assertEqual(state['attempts'],before['attempts'])
            self.assertEqual(state['sessions'],before['sessions'])
            self.assertEqual(state['attempts'][0]['status'],'halted')
            self.assertFalse(state['halted'])
            with l.claim(f.UUID),self.assertRaises(ValueError):l.finish(f.UUID,False)
            record=state['recoveries'][0]
            archive=l.path(f.UUID,'archive-'+record['source_checksum']+'.json')
            self.assertEqual(archive.read_bytes(),raw)
            self.assertEqual(record['next_queue_hash'],plan['queue_hash'])
            self.assertEqual(record['evidence_hash'],proof['evidence_hash'])
            self.assertNotIn('synthetic secret',json.dumps(state))

    def test_recovery_requires_lock_explicit_fresh_bound_review_and_all_proofs(self):
        for fault in ('lock','explicit','expired','checksum','attempt','queue','target','baseline','session',
                      'container','bridge','process','evidence-hash','stale-proof','pending','running'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                l,before,plan,review,proof=self.fixture(Path(d))
                if fault=='explicit':review['explicit_recovery']=False
                elif fault=='expired':review['expires_at']='2000-01-01T00:00:00+00:00'
                elif fault=='checksum':review['source_checksum']='f'*64
                elif fault=='attempt':review['attempt_hash']='f'*64
                elif fault=='queue':review['next_queue_hash']='f'*64
                elif fault=='target':review['target_revision']='f'*40
                elif fault=='baseline':review['baseline_hash']='f'*64
                elif fault=='session':proof['session_closed']=False
                elif fault=='container':proof['container_absent']=False
                elif fault=='bridge':proof['bridge_absent']=False
                elif fault=='process':proof['processes_absent']=False
                elif fault=='evidence-hash':review['evidence_hash']='e'*64
                elif fault=='stale-proof':proof['observed_at']='2000-01-01T00:00:00+00:00'
                elif fault=='pending':l.path(f.UUID,'pending').touch(mode=0o600)
                if fault=='lock':
                    with self.assertRaises(ValueError):l.recover(f.UUID,plan,review,proof)
                else:
                    with l.claim(f.UUID):
                        if fault=='running':
                            changed=copy.deepcopy(before);changed['attempts'][-1]['status']='running';l.save(f.UUID,changed)
                            review['source_checksum']=l.snapshot(f.UUID)['checksum']
                            review['attempt_hash']=s.t.x.queue.cat.digest(changed['attempts'][-1])
                        snapshot=l.path(f.UUID,'json').read_bytes()
                        with self.assertRaises(ValueError):l.recover(f.UUID,plan,review,proof)
                        self.assertEqual(l.path(f.UUID,'json').read_bytes(),snapshot)
                self.assertTrue(l.snapshot(f.UUID)['halted'])

    def test_no_replay_or_foreign_queue_after_recovery_and_next_halt_needs_new_review(self):
        with tempfile.TemporaryDirectory() as d:
            l,before,plan,review,proof=self.fixture(Path(d))
            with l.claim(f.UUID):
                l.recover(f.UUID,plan,review,proof)
                old=before['attempts'][0]
                with self.assertRaises(ValueError):l.consume(f.UUID,old)
                fresh={**old,'queue_hash':plan['queue_hash'],'session':'new-session'}
                with self.assertRaises(ValueError):l.consume(f.UUID,{**fresh,'queue_hash':'e'*64})
                l.consume(f.UUID,fresh)
                l.finish(f.UUID,False)
                with self.assertRaises(ValueError):l.ready(f.UUID)
                with self.assertRaises(ValueError):l.recover(f.UUID,plan,review,proof)
            self.assertEqual(l.snapshot(f.UUID)['attempts'][0],old)

    def test_missing_or_changed_archive_never_allows_dispatch(self):
        for fault in ('missing','changed','symlink'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                l,before,plan,review,proof=self.fixture(Path(d))
                with l.claim(f.UUID):
                    l.recover(f.UUID,plan,review,proof)
                    archive=l.path(f.UUID,'archive-'+before['checksum']+'.json')
                    if fault=='changed':archive.write_text('{}')
                    else:
                        archive.unlink()
                        if fault=='symlink':archive.symlink_to(l.path(f.UUID,'json'))
                    with self.assertRaises((ValueError,OSError)):l.ready(f.UUID)

    def test_interrupted_recovery_never_grants_readiness(self):
        with tempfile.TemporaryDirectory() as d:
            l,before,plan,review,proof=self.fixture(Path(d));raw=l.path(f.UUID,'json').read_bytes()
            with l.claim(f.UUID),patch.object(l,'save',side_effect=OSError('synthetic-private')):
                with self.assertRaises(OSError):l.recover(f.UUID,plan,review,proof)
                self.assertEqual(l.path(f.UUID,'json').read_bytes(),raw)
                with self.assertRaises(ValueError):l.ready(f.UUID)


class ProbeTests(unittest.TestCase):
    def setUp(self):self.r=module('recovery','qa_recovery.py')

    def test_request_requires_current_new_recheck_source_baseline_image_and_no_missing_human_item(self):
        for fault in ('none','same-queue','wrong-purpose','image','human','stale'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                q,_,_,_,_=f.SupervisorTests().fixture(Path(d));prior=copy.deepcopy(q)
                card=q['sets'][0]['cases'][0]['execution'];card['baseline_hash']='c'*64
                card['container_image_id']='sha256:'+'d'*64
                q['sets'][0]['purpose']='recheck'
                baseline=dict(checksum='c'*64,container_image_id=card['container_image_id'],manifest=dict(target_revision=q['target_revision']))
                if fault=='wrong-purpose':q['sets'][0]['purpose']='untested'
                elif fault=='image':card['container_image_id']='sha256:'+'e'*64
                elif fault=='human':card['human_required']=True
                elif fault=='stale':q['references']={}
                s.t.x.queue.seal(q)
                if fault=='same-queue':prior=copy.deepcopy(q)
                with patch.object(self.r.v,'validate_baseline'):
                    if fault=='none':
                        plan=self.r.request_plan(q,prior,baseline)
                        self.assertEqual(plan['queue_hash'],q['scope_hash'])
                        self.assertEqual(plan['write_paths'],card['write_paths'])
                    else:
                        with self.assertRaises(ValueError):self.r.request_plan(q,prior,baseline)

    def old_fixture(self,root):
        for name in ('evidence','bridge','control','control/container'):(root/name).mkdir(mode=0o700)
        fixtures=module('results_fixture','test_qa_results.py')
        report,path,_,_=fixtures.ResultTests().timing_fixture(root/'evidence')
        attempt=dict(queue_hash='a'*64,set='set',owner='Reviewer',case='TC-SS-04',session='session',transport_hash='c'*64)
        prior=dict(scope_hash='a'*64,sets=[dict(name='set',owner='Reviewer',cases=[dict(id='TC-SS-04',execution=dict(
            evidence_dir=str(root/'evidence'),selection=dict(title='TC-SS-04: System Status needs permission')))])])
        common=dict(version=1,status='complete',transport_hash='c'*64,queue_hash='a'*64,case='TC-SS-04')
        container={**common,'session':'session','container_id':'b'*64,'name':'pinpoint-qa-'+'d'*32,'token':'e'*64}
        relay={**common,'lab_uuid':f.UUID,'origin':self.r.v.b.ORIGIN}
        journal=dict(status='halted',queue_hash='a'*64,session_id='session',results=[])
        journal['journal_hash']=s.t.x.queue.cat.digest(journal)
        for file,value in [('control/container/container-intent.json',container),('bridge/bridge-intent.json',relay),('control/session.json',journal)]:
            path=root/file;path.write_text(json.dumps(value));path.chmod(0o600)
        return prior,attempt,report

    def test_original_logout_and_terminal_metadata_are_read_without_accepting_or_writing_items(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);prior,attempt,_=self.old_fixture(root)
            raw=(root/'evidence/results.json').read_bytes()
            identity=self.r.old_evidence(prior,attempt,f.UUID)
            self.assertEqual(len(identity['evidence_hash']),64)
            self.assertEqual((root/'evidence/results.json').read_bytes(),raw)
            self.assertEqual(list((root/'evidence').iterdir()),[root/'evidence/results.json'])

    def test_unknown_cleanup_foreign_transport_and_session_history_reject(self):
        for fault in ('numeric-cleanup','failed-cleanup','retry','foreign-transport','incomplete-intent','journal'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);prior,attempt,report=self.old_fixture(root)
                if fault in ('numeric-cleanup','failed-cleanup','retry'):
                    result=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
                    if fault=='retry':result['retry']=1
                    else:
                        fixtures=module('results_fixture','test_qa_results.py')
                        result['attachments'][1]['body']=fixtures.body(dict(session_closed=1 if fault=='numeric-cleanup' else False))
                    (root/'evidence/results.json').write_text(json.dumps(report))
                elif fault=='foreign-transport':attempt['transport_hash']='f'*64
                elif fault=='incomplete-intent':
                    file=root/'bridge/bridge-intent.json';value=json.loads(file.read_text());value['status']='running';file.write_text(json.dumps(value))
                else:(root/'control/session.json').write_text('{}')
                with self.assertRaises((ValueError,KeyError)):self.r.old_evidence(prior,attempt,f.UUID)

    def test_daemon_absence_requires_successful_empty_queries_by_id_and_name(self):
        for fault in ('none','daemon-error','remaining'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);output=root/'stdout';output.write_text('x' if fault=='remaining' else '');output.chmod(0o600)
                runner=Mock(root=root);runner.run.return_value=dict(returncode=1 if fault=='daemon-error' else 0,group_clean=True,stdout=str(output))
                identity=dict(container_id='a'*64,name='pinpoint-qa-'+'b'*32)
                if fault=='none':
                    self.r.daemon_absence(identity,runner,'synthetic')
                    self.assertEqual(runner.run.call_count,2)
                    self.assertIn('id='+identity['container_id'],runner.run.call_args_list[0].args[0])
                    self.assertIn('name=^/'+identity['name']+'$',runner.run.call_args_list[1].args[0])
                else:
                    with self.assertRaises(ValueError):self.r.daemon_absence(identity,runner,'synthetic')

    def test_process_and_unlinked_unix_endpoint_presence_reject_without_killing(self):
        for fault in ('none','process','socket','unlinked-endpoint'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);(root/'net').mkdir();(root/'123').mkdir()
                identity=dict(container_id='a'*64,name='pinpoint-qa-'+'b'*32,socket=str(root/'old.sock'),old_control=str(root/'old-control'))
                (root/'123/cmdline').write_bytes(identity['container_id'].encode() if fault=='process' else b'unrelated')
                (root/'net/unix').write_text(identity['socket'] if fault=='unlinked-endpoint' else 'header')
                if fault=='socket':(root/'old.sock').symlink_to(root/'missing')
                if fault=='none':self.r.process_absence(identity,root)
                else:
                    with self.assertRaises(ValueError):self.r.process_absence(identity,root)

    def test_composed_recovery_checks_grant_before_probes_and_preserves_state_on_failure(self):
        for fault in ('none','unapproved','daemon','baseline'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);l,before,plan,review,proof=RecoveryTests().fixture(root)
                if fault=='unapproved':review['explicit_recovery']=False
                output=root/'recovery';output.mkdir(mode=0o700);plan['write_paths']=[str(output)]
                baseline=dict(lab_uuid=f.UUID,state_dir=str(root/'state'))
                identity=dict(container_id='a'*64,name='pinpoint-qa-'+'b'*32,socket=str(root/'prior/bridge/web.sock'),old_control=str(root/'prior/control'),evidence_hash='d'*64)
                inspector=Mock();inspector.verify.return_value=proof
                if fault=='baseline':inspector.verify.side_effect=ValueError('synthetic drift')
                with patch.object(self.r,'request_plan',return_value=plan),patch.object(self.r.v.s,'Ledger',return_value=l),patch.object(self.r,'old_evidence',return_value=identity) as old,patch.object(self.r,'prior_card',return_value=dict(evidence_dir=str(root/'prior/evidence'))),patch.object(self.r,'process_absence'),patch.object(self.r,'daemon_absence',side_effect=ValueError('synthetic daemon error') if fault=='daemon' else None),patch.object(self.r.v,'Inspector',return_value=inspector) as factory:
                    if fault=='none':
                        result=self.r.recover_pilot(dict(scope_hash=plan['queue_hash']),{},review,baseline,output,root/'key')
                        self.assertFalse(result['case_attempted']);self.assertEqual(result['original_result'],'INCONCLUSIVE')
                        with l.claim(f.UUID):l.ready(f.UUID)
                    else:
                        with self.assertRaises(ValueError):self.r.recover_pilot(dict(scope_hash=plan['queue_hash']),{},review,baseline,output,root/'key')
                        self.assertEqual(l.snapshot(f.UUID),before)
                        if fault=='unapproved':factory.assert_not_called();old.assert_not_called()
                self.assertEqual(l.snapshot(f.UUID)['attempts'],before['attempts'])


if __name__=='__main__':unittest.main()
