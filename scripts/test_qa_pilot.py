"""Composed pilot-driver contracts: synthetic observers/resources, no live tools."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
spec=importlib.util.spec_from_file_location('pilot',Path(__file__).with_name('qa_pilot.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
f=v.module('fixtures','test_qa_supervisor.py')


class DriverTests(unittest.TestCase):
    def fixture(self,root):
        q,j,ledger,grant,_=f.SupervisorTests().fixture(root)
        runtime=root/'runtime';runtime.mkdir(mode=0o700)
        inspector=Mock()
        inspector.verify.return_value=dict(lab_uuid=f.UUID,target_revision='a'*40,
            origin=v.b.ORIGIN,observed_at=v.s.t.x.now(),exclusive=True,
            runtime_identity_verified=True,baseline_verified=True,recovery_verified=True,deployment_clean=True)
        driver=v.PilotDriver(inspector,ledger,f.UUID,runtime)
        return q,j,ledger,grant,driver

    def test_full_supervisor_composition_consumes_then_runs_and_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);q,j,ledger,grant,driver=self.fixture(root)
            bridge=Mock();bridge.stop.return_value=True
            runner=Mock();runner.idle.return_value=True
            container=Mock()
            def execute(plan,*args):
                self.assertEqual(ledger.snapshot(f.UUID)['attempts'][-1]['status'],'running')
                return dict(container_clean=True,exit_code=0,run_started_at=v.s.t.x.now(),run_finished_at=v.s.t.x.now(),run_elapsed_seconds=1)
            container.execute.side_effect=execute
            def parsed(*args,**kwargs):
                self.assertEqual(args[1],'TC-SS-04')
                (root/'evidence/E1.json').write_text('{}')
                return dict(result='PASS',restored=True,evidence={'E1':dict(verdict='PASS',observed='Synthetic permission evidence',reference='E1.json')},reason='')
            with patch.object(v.b,'Bridge',return_value=bridge),patch.object(v.p,'GroupRunner',return_value=runner),patch.object(v.c,'ContainerRuntime',return_value=container),patch.object(v.r,'parse_report',side_effect=parsed):
                result=v.s.supervise(q,j,grant,ledger,root/'state',root/'bridge',driver)
            self.assertEqual(result['result'],'PASS');self.assertEqual(driver.inspector.verify.call_count,3)
            bridge.stop.assert_called_once();self.assertFalse(ledger.snapshot(f.UUID)['halted'])

    def test_real_parser_44ms_result_and_rejections_through_supervisor(self):
        fixtures=v.module('result_fixtures','test_qa_results.py')
        for fault in ('none','stale','future-item','foreign-item','cleanup','missing-finish','missing-elapsed'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);q,j,ledger,grant,driver=self.fixture(root)
                (root/'fixture').mkdir(mode=0o700)
                report,path,start,finish=fixtures.ResultTests().timing_fixture(root/'fixture')
                attempt=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
                if fault=='stale':start='2026-10-18T07:21:19.100Z'
                elif fault in ('future-item','foreign-item'):
                    obs=fixtures.json.loads(fixtures.base64.b64decode(attempt['attachments'][0]['body']))
                    if fault=='future-item':obs['at']='2026-10-18T07:21:19.201Z'
                    else:obs['case_id']='TC-HIS-01'
                    attempt['attachments'][0]['body']=fixtures.body(obs)
                elif fault=='cleanup':attempt['attachments'][1]['body']=fixtures.body(dict(session_closed=False))
                path.write_text(fixtures.json.dumps(report))
                runtime=dict(container_clean=True,exit_code=0,run_started_at=start,run_finished_at=finish,run_elapsed_seconds=2.2)
                if fault=='missing-finish':runtime.pop('run_finished_at')
                if fault=='missing-elapsed':runtime.pop('run_elapsed_seconds')
                bridge=Mock();bridge.stop.return_value=True
                runner=Mock();runner.idle.return_value=True
                container=Mock()
                def execute(*args):
                    self.assertEqual(ledger.snapshot(f.UUID)['attempts'][-1]['status'],'running')
                    output=root/'evidence/results.json';output.write_text(path.read_text());output.chmod(0o600)
                    return runtime
                container.execute.side_effect=execute
                with patch.object(v.b,'Bridge',return_value=bridge),patch.object(v.p,'GroupRunner',return_value=runner),patch.object(v.c,'ContainerRuntime',return_value=container):
                    if fault=='none':
                        result=v.s.supervise(q,j,grant,ledger,root/'state',root/'bridge',driver)
                        self.assertEqual(result['result'],'PASS')
                    else:
                        with self.assertRaises(ValueError):v.s.supervise(q,j,grant,ledger,root/'state',root/'bridge',driver)
                state=ledger.snapshot(f.UUID)
                self.assertEqual(state['halted'],fault!='none')
                self.assertEqual(len(state['attempts']),1)
                bridge.stop.assert_called_once()

    def test_inspector_failure_never_creates_transport_or_consumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);q,j,l,g,driver=self.fixture(root)
            driver.inspector.verify.side_effect=ValueError('Synthetic drift')
            with patch.object(v.b,'Bridge') as bridge,self.assertRaises(ValueError):
                v.s.supervise(q,j,g,l,root/'state',root/'bridge',driver)
            bridge.assert_not_called();self.assertEqual(l.snapshot(f.UUID)['attempts'],[])

    def test_session_container_bridge_and_process_cleanup_are_all_required(self):
        for failure in ('session','container','bridge','runner','report'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);q,j,l,g,driver=self.fixture(root)
                bridge=Mock();bridge.stop.return_value=failure!='bridge'
                runner=Mock();runner.idle.return_value=failure!='runner'
                container=Mock();container.execute.return_value=dict(container_clean=failure!='container',exit_code=0,run_started_at=v.s.t.x.now(),run_finished_at=v.s.t.x.now(),run_elapsed_seconds=1)
                outcome=dict(result='INCONCLUSIVE',restored=failure!='session',evidence={},reason='Synthetic incomplete evidence')
                with patch.object(v.b,'Bridge',return_value=bridge),patch.object(v.p,'GroupRunner',return_value=runner),patch.object(v.c,'ContainerRuntime',return_value=container),patch.object(v.r,'parse_report',side_effect=ValueError('Synthetic malformed report') if failure=='report' else None,return_value=outcome):
                    with self.assertRaises(ValueError):v.s.supervise(q,j,g,l,root/'state',root/'bridge',driver)
                self.assertTrue(l.snapshot(f.UUID)['halted']);bridge.stop.assert_called_once()

    def test_verify_requires_held_claim_and_run_cannot_repeat_or_change_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);q,j,l,g,driver=self.fixture(root)
            with self.assertRaises(ValueError):driver.verify({})
            for plan in ({'case':'TC-HIS-01'},{'case':'TC-SS-04'}):
                driver.used=plan['case']=='TC-SS-04'
                with self.assertRaises(ValueError):driver.run(plan,10)
            driver.inspector.verify.assert_not_called()

    def test_every_baseline_dimension_and_runtime_identity_is_compared(self):
        expected=dict(main_pid=1,boot_id='boot',configuration={},dependencies={},sources={},executables={},staff=[],networks=[],scans=[],database_versions={},scheduler_enabled=False,
            observation=dict(source_files_match=True,frontend_files_match=True,unexpected_python_count=0,target_revision='a'*40,manifest_hash='hash',artifact_hashes={},processes=[]))
        v.compare_guest(expected,copy.deepcopy(expected))
        for key in expected:
            actual=copy.deepcopy(expected)
            if key=='observation':continue
            actual[key]='changed'
            with self.subTest(key=key),self.assertRaises(ValueError):v.compare_guest(expected,actual)
        for key in expected['observation']:
            actual=copy.deepcopy(expected);actual['observation'][key]='changed'
            with self.subTest(key=key),self.assertRaises(ValueError):v.compare_guest(expected,actual)

    def baseline(self):
        sources={name:'a'*64 for name in v.d.REQUIRED|{'client/package-lock.json'}}
        manifest=v.d.seal(dict(version=1,target_revision='a'*40,reviewed_by='Synthetic reviewer',sources=sources,frontend={'index.html':'b'*64}))
        obs=dict(source_files_match=True,frontend_files_match=True,unexpected_python_count=0,
            target_revision='a'*40,manifest_hash=manifest['checksum'],artifact_hashes={k:manifest[k] for k in ('sources','frontend')},
            processes=[dict(pid=123,parent_pid=1,starts_after_source_files=False)])
        guest=dict(observation=obs,main_pid=123,boot_id='synthetic-boot',configuration={'config':{}},
            dependencies=dict(file_count=30,inventory_sha256='a'*64),sources={name:dict(sha256=h) for name,h in sources.items()},
            executables={'123':{}},staff=[['ACTIVE',0,0,'Staff',1,0]],networks=[['["10.77.0.0/28"]']],
            scans=[3,'synthetic'],database_versions={'system.db':['synthetic']},scheduler_enabled=False,inputs_precede_launch=True)
        host=dict(lab_uuid=f.UUID,controller_pid=1,controller_start_ticks=2,vm_pid=3,vm_start_ticks=4,running_endpoints_verified=True)
        launch=dict(main_pid=123,target='a'*40,database_revisions_after=guest['database_versions'],scheduler_enabled=False,service_active=True,
            steps=[dict(step=name,returncode=0) for name in ['database-upgrade','start-application']])
        return v.d.seal(dict(version=1,reviewed_by='Synthetic reviewer',preparation_report='synthetic report',
            method='controlled stopped-service deployment',launch_verified=True,build_verified=True,lab_uuid=f.UUID,
            email_fingerprint='c'*64,state_dir='/synthetic-state',container_image_id='sha256:'+'a'*64,
            browser_relative_path='synthetic-browser',browser_sha256='d'*64,manifest=manifest,guest=guest,host=host,launch=launch,
            build=dict(target='a'*40,frontend_artifacts=manifest['frontend'],package_lock_sha256='a'*64)))

    def test_launch_and_build_provenance_and_input_order_are_independent_requirements(self):
        baseline=self.baseline();v.validate_baseline(baseline)
        for group,key,value in [('guest','inputs_precede_launch',False),('launch','main_pid',999),
            ('launch','scheduler_enabled',True),('build','target','b'*40),('build','package_lock_sha256','bad')]:
            changed=copy.deepcopy(baseline);changed[group][key]=value;v.d.seal(changed)
            with self.subTest(group=group,key=key),self.assertRaises(ValueError):v.validate_baseline(changed)

    def test_inspector_requires_claim_and_rechecks_guest_served_and_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);key=root/'key';key.write_text('synthetic');key.chmod(0o600)
            baseline=self.baseline();inspector=v.Inspector(baseline,root,key)
            plan=dict(case='TC-SS-04',target_revision='a'*40,baseline_hash=baseline['checksum'],bridge_origin=v.b.ORIGIN)
            with patch.object(inspector,'guest',return_value=baseline['guest']) as guest,patch.object(inspector,'served') as served,patch.object(inspector,'local'),patch.object(v.h,'observe',return_value=baseline['host']):
                with self.assertRaises((ValueError,OSError,TypeError)):inspector.verify(plan,-1)
                guest.assert_not_called()
                with v.s.control.claim() as fd:proof=inspector.verify(plan,fd)
                self.assertTrue(proof['runtime_identity_verified']);self.assertEqual(guest.call_count,2);served.assert_called_once()
                changed=copy.deepcopy(baseline['guest']);changed['boot_id']='changed';guest.return_value=changed
                with v.s.control.claim() as fd,self.assertRaises(ValueError):inspector.verify(plan,fd)

    def test_missing_start_is_rejected_before_output_or_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);q,j,l,g,driver=self.fixture(root);baseline=self.baseline()
            baseline['manifest']['target_revision']=q['target_revision'];baseline['state_dir']=str(root/'state')
            card=q['sets'][0]['cases'][0]['execution'];card['baseline_hash']=baseline['checksum'];card['container_image_id']='sha256:'+'a'*64;v.s.t.x.queue.seal(q)
            # Identity fields use the current immutable scope, but start is absent.
            g.update(queue_hash=q['scope_hash'],explicit_start=False)
            with patch.object(v,'validate_baseline'),patch.object(v,'Inspector') as inspector,patch.object(v.s.t,'private_directory') as directory:
                with self.assertRaises(ValueError):v.run_pilot(q,'set','Reviewer','session',g,baseline,root/'state',root/'bridge',root/'new-control',root/'key')
            inspector.assert_not_called();directory.assert_not_called();self.assertFalse((root/'new-control').exists())

    def test_explicit_start_path_durably_records_one_result_without_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);q,j,l,g,driver=self.fixture(root);baseline=self.baseline()
            baseline['state_dir']=str(root/'state');v.d.seal(baseline)
            control=root/'control';control.mkdir(mode=0o700)
            card=q['sets'][0]['cases'][0]['execution']
            card.update(baseline_hash=baseline['checksum'],container_image_id=baseline['container_image_id'],
                write_paths=[str(root/name) for name in ('control','bridge','evidence')])
            v.s.t.x.queue.seal(q);g['queue_hash']=q['scope_hash']
            outcome=dict(case='TC-SS-04',result='INCONCLUSIVE',reason='Synthetic journal wiring',restored=True)
            with patch.object(v,'Inspector',return_value=driver.inspector),patch.object(v.s,'supervise',return_value=outcome) as supervise,patch.object(v.s.control,'canonical_root',return_value=root/'host-control'):
                result=v.run_pilot(q,'set','Reviewer','session',g,baseline,root/'state',root/'bridge',control,root/'key')
                with self.assertRaises(ValueError):v.run_pilot(q,'set','Reviewer','session',g,baseline,root/'state',root/'bridge',control,root/'key')
            self.assertEqual(result,outcome);supervise.assert_called_once()
            journal=v.private_json(control/'session.json')
            self.assertEqual(journal['results'],[outcome]);self.assertIsNone(journal['active_case'])
            self.assertEqual(journal['batches_started'],['set-001'])
            self.assertEqual(journal['journal_hash'],v.s.t.x.queue.cat.digest({k:value for k,value in journal.items() if k!='journal_hash'}))
            self.assertEqual((control/'session.json').stat().st_mode & 0o777,0o600)

    def test_two_case_permission_batch_saves_each_result_and_stops_on_nonpass(self):
        for first_result in ('PASS','INCONCLUSIVE'):
            with self.subTest(first=first_result),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);q,j,l,g,driver=self.fixture(root);baseline=self.baseline()
                baseline['state_dir']=str(root/'state');v.d.seal(baseline)
                q=v.s.t.x.queue.prepare(['set:Reviewer:TC-ACC-09,TC-NCPA-08'],v.s.t.x.queue.load_catalog(),'a'*40)
                for case in q['sets'][0]['cases']:
                    evidence=root/case['id'];evidence.mkdir(mode=0o700)
                    card=v.s.t.x.queue.coverage.card_template(case['coverage'])
                    card.update(reviewed_by='Synthetic reviewer',timeout_seconds=300,step_timeout_seconds=30,
                        human_required=False,prerequisites=['Synthetic observed Staff baseline'],
                        baseline_hash=baseline['checksum'],container_image_id=baseline['container_image_id'],
                        evidence_dir=str(evidence),control_dir=str(root/'control'/case['id']),
                        bridge_dir=str(root/'bridge'/case['id']),
                        write_paths=[str(root/name) for name in ('control','bridge',case['id'])])
                    case['execution']=card
                v.s.t.x.queue.seal(q);g['queue_hash']=q['scope_hash'];(root/'control').mkdir(mode=0o700)
                calls=[];original_supervise=v.s.supervise
                def supervised(queue,journal,grant,ledger,state,bridge,actual_driver):
                    case=journal['active_case']['id'];calls.append(case)
                    if len(calls)==2:
                        saved=v.private_json(root/'control/session.json')
                        self.assertEqual(saved['results'][0]['case'],'TC-ACC-09')
                        self.assertEqual(saved['active_case']['id'],'TC-NCPA-08')
                    self.assertEqual(bridge,root/'bridge'/case)
                    self.assertEqual(actual_driver.root,root/'control'/case/'container')
                    def synthetic_run(plan,timeout):
                        card=next(c['execution'] for c in queue['sets'][0]['cases'] if c['id']==case)
                        observations={}
                        for item in v.r.OBSERVATIONS[case]:
                            file=Path(card['evidence_dir'])/(item+'.json');file.write_text('{}')
                            observations[item]=dict(verdict='PASS',observed='Synthetic orchestration '+item,reference=file.name)
                        return dict(result=first_result if len(calls)==1 else 'PASS',restored=True,
                            evidence=observations,reason='Synthetic orchestration evidence')
                    with patch.object(actual_driver,'run',side_effect=synthetic_run),patch.object(actual_driver,'cleanup',return_value=True):
                        return original_supervise(queue,journal,grant,ledger,state,bridge,actual_driver)
                with patch.object(v,'Inspector',return_value=driver.inspector),patch.object(v.s,'supervise',side_effect=supervised),patch.object(v.s.control,'canonical_root',return_value=root/'host-control'):
                    result=v.run_pilot(q,'set','Reviewer','session',g,baseline,root/'state',root/'bridge',root/'control',root/'key')
                saved=v.private_json(root/'control/session.json')
                self.assertEqual(calls,['TC-ACC-09','TC-NCPA-08'] if first_result=='PASS' else ['TC-ACC-09'])
                self.assertEqual(len(saved['results']),2 if first_result=='PASS' else 1)
                self.assertEqual(saved['status'],'complete' if first_result=='PASS' else 'stopped')
                self.assertEqual(result['next_case'],None if first_result=='PASS' else 'TC-NCPA-08')
                self.assertEqual(saved['batches_started'],['set-001'])

    def test_runtime_hardlinks_are_hashed_but_symlinks_rejected(self):
        import os
        namespace=dict(vars(v.d));exec((v.ROOT/'scripts/qa_pilot_guest.py').read_text(),namespace)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=root/'a.py';a.write_text('synthetic runtime')
            os.link(a,root/'b.py');before=namespace['runtime_inventory'](root)
            self.assertEqual(before['file_count'],2)
            a.write_text('changed runtime')
            self.assertNotEqual(namespace['runtime_inventory'](root)['inventory_sha256'],before['inventory_sha256'])
            (root/'alias.py').symlink_to(a)
            with self.assertRaises(ValueError):namespace['runtime_inventory'](root)

    def test_unreviewed_or_checksum_modified_baseline_rejected(self):
        for value in ({},dict(version=1,launch_verified=True,build_verified=True)):
            with self.assertRaises(ValueError):v.validate_baseline(value)

if __name__=='__main__':unittest.main()
