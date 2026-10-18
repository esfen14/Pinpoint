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
                return dict(container_clean=True,exit_code=0,run_started_at=v.s.t.x.now())
            container.execute.side_effect=execute
            def parsed(*args):
                self.assertEqual(args[1],'TC-SS-04')
                (root/'evidence/E1.json').write_text('{}')
                return dict(result='PASS',restored=True,evidence={'E1':dict(verdict='PASS',observed='Synthetic permission evidence',reference='E1.json')},reason='')
            with patch.object(v.b,'Bridge',return_value=bridge),patch.object(v.p,'GroupRunner',return_value=runner),patch.object(v.c,'ContainerRuntime',return_value=container),patch.object(v.r,'parse_report',side_effect=parsed):
                result=v.s.supervise(q,j,grant,ledger,root/'state',root/'bridge',driver)
            self.assertEqual(result['result'],'PASS');self.assertEqual(driver.inspector.verify.call_count,3)
            bridge.stop.assert_called_once();self.assertFalse(ledger.snapshot(f.UUID)['halted'])

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
                container=Mock();container.execute.return_value=dict(container_clean=failure!='container',exit_code=0,run_started_at=v.s.t.x.now())
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
