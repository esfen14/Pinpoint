"""Synthetic Playwright JSON only; collection/acceptance cases never execute."""
import base64
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('results',Path(__file__).with_name('qa_results.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def body(value):return base64.b64encode(json.dumps(value).encode()).decode()


class ResultTests(unittest.TestCase):
    def fixture(self,root):
        now=datetime.now(timezone.utc);start=now-timedelta(seconds=1)
        observation=dict(case_id='TC-SS-04',item='E1',verdict='PASS',
            observed='System Status absent from sidebar; direct address redirects to Settings.',at=(start+timedelta(milliseconds=500)).isoformat())
        use=dict(baseURL='http://127.0.0.1:18080',trace='off',screenshot='off',video='off')
        report=dict(config=dict(version='1.64.0',workers=1,forbidOnly=True,fullyParallel=False,
            configFile='/work/client/playwright.qa.config.ts',rootDir='/work/client/e2e',
            metadata=dict(currentCaseIds=['TC-SS-04'],mode='scripted automation'),
            projects=[dict(name='qa-permissions',retries=0,repeatEach=1,outputDir='/evidence/artifacts')],
            filteredProjects=[dict(name='qa-permissions',retries=0,dependencies=[],use=use)]),
            errors=[],stats=dict(startTime=start.isoformat(),duration=1000,expected=1,unexpected=0,flaky=0,skipped=0),
            suites=[dict(title='qa-permissions.lab.spec.ts',specs=[dict(title='TC-SS-04: System Status needs permission',
                file='qa-permissions.lab.spec.ts',tests=[dict(projectName='qa-permissions',expectedStatus='passed',status='expected',
                results=[dict(status='passed',retry=0,startTime=start.isoformat(),duration=1000,errors=[],attachments=[
                    dict(name='TC-SS-04-E1',contentType='application/json',body=body(observation)),
                    dict(name='cleanup',contentType='application/json',body=body(dict(session_closed=True)))])])])])])
        path=root/'results.json';path.write_text(json.dumps(report));path.chmod(0o600)
        return report,path,(start-timedelta(seconds=1)).isoformat()

    def parse(self,path,root,start,finish=None):
        return r.parse_report(path,'TC-SS-04',root,start,
            finish or datetime.now(timezone.utc).isoformat(),run_elapsed_seconds=2.2,max_run_seconds=300)

    def timing_fixture(self,root):
        """Construct from public sanitized timings, never read owner-held evidence."""
        report,path,_=self.fixture(root)
        report['stats'].update(startTime='2026-10-18T07:21:17.708Z',duration=1448.738)
        attempt=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
        attempt.update(startTime='2026-10-18T07:21:18.069Z',duration=910,
            workerIndex=0,parallelIndex=0,stdout=[],stderr=[],annotations=[])
        observation=json.loads(base64.b64decode(attempt['attachments'][0]['body']))
        observation['at']='2026-10-18T07:21:19.023Z'
        attempt['attachments'][0]['body']=body(observation)
        path.write_text(json.dumps(report))
        # Synthetic independently observed launch/attach completion surround the
        # published times. They are NOT new observations about the original pilot.
        return report,path,'2026-10-18T07:21:17.000Z','2026-10-18T07:21:19.200Z'

    def test_observed_44ms_mismatch_uses_independent_run_window(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700)
            report,path,start,finish=self.timing_fixture(root)
            attempt=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
            observation=json.loads(base64.b64decode(attempt['attachments'][0]['body']))
            computed=r.instant(attempt['startTime'])+timedelta(milliseconds=attempt['duration'])
            self.assertEqual((r.instant(observation['at'])-computed).total_seconds(),0.044)
            self.assertEqual(self.parse(path,root,start,finish)['result'],'PASS')

    def test_independent_window_rejects_stale_future_foreign_and_forged_items(self):
        for fault in ('before-launch','after-finish','before-attempt','foreign-case','foreign-item',
                      'forged-text','future-finish','reversed-window','over-budget','bad-stats',
                      'stats-too-long','stats-exceeds-attach','stats-before-launch','attempt-after-finish'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);root.chmod(0o700)
                report,path,start,finish=self.timing_fixture(root)
                attempt=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
                att=attempt['attachments'][0];obs=json.loads(base64.b64decode(att['body']))
                if fault=='before-launch':start='2026-10-18T07:21:19.100Z'
                elif fault=='after-finish':obs['at']='2026-10-18T07:21:19.201Z'
                elif fault=='before-attempt':obs['at']='2026-10-18T07:21:18.068Z'
                elif fault=='foreign-case':obs['case_id']='TC-HIS-01'
                elif fault=='foreign-item':obs['item']='E2'
                elif fault=='forged-text':obs['observed']='forged unreviewed claim'
                elif fault=='future-finish':finish=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
                elif fault=='reversed-window':finish=start
                elif fault=='over-budget':start='2026-10-18T07:16:19.199Z'
                elif fault=='bad-stats':report['stats']['duration']=True
                elif fault=='stats-too-long':report['stats']['duration']=90001
                elif fault=='stats-exceeds-attach':report['stats']['duration']=2201
                elif fault=='stats-before-launch':report['stats']['startTime']='2026-10-18T07:21:16.999Z'
                else:attempt['startTime']='2026-10-18T07:21:19.201Z'
                att['body']=body(obs);path.write_text(json.dumps(report))
                with self.assertRaises(ValueError):self.parse(path,root,start,finish)
                self.assertFalse((root/'observed-TC-SS-04-E1.json').exists())

    def test_independent_receipts_reject_future_and_invalid_monotonic_budgets(self):
        for fault in ('future','elapsed-boolean','elapsed-nan','elapsed-zero','elapsed-over-budget',
                      'budget-boolean','budget-infinite','budget-above-reviewed-cap'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);root.chmod(0o700)
                report,path,start,finish=self.timing_fixture(root)
                elapsed=2.2;budget=300
                if fault=='future':
                    start=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
                    finish=(r.instant(start)+timedelta(seconds=2)).isoformat()
                    report['stats']['startTime']=start
                    attempt=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
                    attempt['startTime']=start
                    obs=json.loads(base64.b64decode(attempt['attachments'][0]['body']))
                    obs['at']=start;attempt['attachments'][0]['body']=body(obs)
                    path.write_text(json.dumps(report))
                elif fault=='elapsed-boolean':elapsed=True
                elif fault=='elapsed-nan':elapsed=float('nan')
                elif fault=='elapsed-zero':elapsed=0
                elif fault=='elapsed-over-budget':elapsed=301
                elif fault=='budget-boolean':budget=True
                elif fault=='budget-infinite':budget=float('inf')
                else:budget=301
                with self.assertRaises(ValueError):
                    r.parse_report(path,'TC-SS-04',root,start,finish,
                        run_elapsed_seconds=elapsed,max_run_seconds=budget)
                self.assertFalse((root/'observed-TC-SS-04-E1.json').exists())

    def test_44ms_fixture_with_failed_logout_stays_inconclusive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700)
            report,path,start,finish=self.timing_fixture(root)
            report['suites'][0]['specs'][0]['tests'][0]['results'][0]['attachments'][1]['body']=body(dict(session_closed=False))
            path.write_text(json.dumps(report))
            result=self.parse(path,root,start,finish)
            self.assertEqual(result['result'],'INCONCLUSIVE');self.assertFalse(result['restored'])

    def test_complete_single_attempt_pass_has_sanitized_item_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            result=self.parse(path,root,start)
            self.assertEqual(result['result'],'PASS');self.assertTrue(result['restored'])
            self.assertEqual(result['evidence']['E1']['reference'],'observed-TC-SS-04-E1.json')
            self.assertTrue((root/result['evidence']['E1']['reference']).is_file())
            self.assertNotIn('body',json.dumps(result))

    def test_new_permission_cases_require_each_exact_reviewed_item(self):
        cases={
            'TC-ACC-09': ('TC-ACC-09: The accounts page needs permission', {
                'E1':'Manage Accounts absent from sidebar; direct address redirects to Settings.',
                'E2':'Accounts API address returns 403.'}),
            'TC-NCPA-08': ('TC-NCPA-08: NCPA Deployment needs permission', {
                'E1':'NCPA Deployment absent from sidebar; direct address redirects to Settings.'}),
        }
        for case_id,(title,observations) in cases.items():
            for fault in ('none','missing-last','forged-last','foreign-item'):
                with self.subTest(case=case_id,fault=fault),tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp);root.chmod(0o700)
                    report,path,start=self.fixture(root)
                    report['config']['metadata']['currentCaseIds']=[case_id]
                    spec=report['suites'][0]['specs'][0];spec['title']=title
                    attempt=spec['tests'][0]['results'][0]
                    attached=[]
                    for item,observed in observations.items():
                        obs=dict(case_id=case_id,item=item,verdict='PASS',observed=observed,
                            at=(r.instant(attempt['startTime'])+timedelta(milliseconds=500)).isoformat())
                        attached.append(dict(name=case_id+'-'+item,contentType='application/json',body=body(obs)))
                    if fault=='missing-last':attached.pop()
                    elif fault in ('forged-last','foreign-item'):
                        obs=json.loads(base64.b64decode(attached[-1]['body']))
                        obs['observed' if fault=='forged-last' else 'item']='unreviewed'
                        attached[-1]['body']=body(obs)
                    attempt['attachments']=attached+[attempt['attachments'][-1]]
                    path.write_text(json.dumps(report))
                    if fault in ('forged-last','foreign-item'):
                        with self.assertRaises(ValueError):
                            r.parse_report(path,case_id,root,start,datetime.now(timezone.utc).isoformat(),
                                run_elapsed_seconds=2.2,max_run_seconds=300)
                        self.assertEqual(list(root.glob('observed-*.json')),[])
                    else:
                        parsed=r.parse_report(path,case_id,root,start,datetime.now(timezone.utc).isoformat(),
                            run_elapsed_seconds=2.2,max_run_seconds=300)
                        self.assertEqual(parsed['result'],'PASS' if fault=='none' else 'INCONCLUSIVE')
                        self.assertEqual(set(parsed['evidence']),set(observations) if fault=='none' else set(observations)-{list(observations)[-1]})

    def test_module_cases_require_the_exact_module_project_and_all_items(self):
        cases={
            'TC-ACC-08': ('TC-ACC-08: "Send this user email alerts" depends on permission', {
                'E1':'Super Admin sees the Email Alerts column and email-alert checkbox.',
                'E2':'The qa-accounts user does not see the email-alert checkbox.'}),
            'TC-ROL-04': ('TC-ROL-04: A dashboard-only user is limited to the Dashboard', {
                'E1':'Sidebar contains Overview and Settings only.',
                'E2':'All 13 protected page addresses redirect to the Dashboard.',
                'E3':'All three protected API addresses return 403.'}),
            'TC-DI-02': ('TC-DI-02: Port groups and their order', {
                'E1':'Port group headers appear in the required order.',
                'E2':'Every shown group has a matching positive count; empty groups are absent.',
                'E3':'Each visible port group is ordered TCP then UDP, by port number.'}),
            'TC-DI-03': ('TC-DI-03: One reason per port', {
                'E1':'Exactly one reason is shown and the held-back reason is absent.',
                'E2':'The reason explains the expected/found names and says monitoring waits for acknowledgement.'}),
            'TC-DASH-07': ('TC-DASH-07: "No data" instead of blank cards', {
                'E1':'Network Latency and both Network Performance metrics show No data.',
                'E2':'Average Resource Utilization is absent without NCPA data.'}),
        }
        for case_id,(title,observations) in cases.items():
            with self.subTest(case=case_id),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);root.chmod(0o700)
                report,path,start=self.fixture(root)
                config=report['config'];config['configFile']='/work/client/playwright.modules.qa.config.ts'
                config['metadata']['currentCaseIds']=[case_id]
                config['projects'][0]['name']='qa-modules-2-9'
                config['filteredProjects'][0]['name']='qa-modules-2-9'
                suite=report['suites'][0];suite['title']='qa-modules-2-9.lab.spec.ts'
                spec_row=suite['specs'][0];spec_row['title']=title;spec_row['file']='qa-modules-2-9.lab.spec.ts'
                test_row=spec_row['tests'][0];test_row['projectName']='qa-modules-2-9'
                attempt=test_row['results'][0];attachments=[]
                for item,observed in observations.items():
                    obs=dict(case_id=case_id,item=item,verdict='PASS',observed=observed,
                        at=(r.instant(attempt['startTime'])+timedelta(milliseconds=500)).isoformat())
                    attachments.append(dict(name=case_id+'-'+item,contentType='application/json',body=body(obs)))
                attachments.append(dict(name='cleanup',contentType='application/json',body=body(dict(session_closed=True))))
                attempt['attachments']=attachments
                path.write_text(json.dumps(report))
                parsed=r.parse_report(path,case_id,root,start,datetime.now(timezone.utc).isoformat(),
                    run_elapsed_seconds=2.2,max_run_seconds=300)
                self.assertEqual(parsed['result'],'PASS')
                self.assertTrue(parsed['restored'])
                self.assertEqual(set(parsed['evidence']),set(observations))
                self.assertEqual(len(list(root.glob('observed-*.json'))),len(observations))

    def test_extra_case_retry_skip_wrong_project_and_capture_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            for change in ('extra','retry','skip','project','capture','metadata','version'):
                value=copy.deepcopy(report)
                if change=='extra':value['suites']*=2
                elif change=='retry':value['suites'][0]['specs'][0]['tests'][0]['results']*=2
                elif change=='skip':value['stats']['skipped']=1
                elif change=='project':value['config']['projects'][0]['name']='admin'
                elif change=='capture':value['config']['filteredProjects'][0]['use']['trace']='on'
                elif change=='metadata':value['config']['metadata']['currentCaseIds']=['TC-HIS-01']
                else:value['config']['version']='unknown'
                path.write_text(json.dumps(value))
                with self.subTest(change=change),self.assertRaises(ValueError):self.parse(path,root,start)

    def test_missing_cleanup_or_item_never_becomes_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            attempt=report['suites'][0]['specs'][0]['tests'][0]['results'][0]
            attempt['attachments'][1]['body']=body(dict(session_closed=1))
            path.write_text(json.dumps(report));numeric=self.parse(path,root,start)
            self.assertEqual(numeric['result'],'INCONCLUSIVE');self.assertFalse(numeric['restored'])
            (root/'observed-TC-SS-04-E1.json').unlink()
            attempt['attachments']=[];path.write_text(json.dumps(report))
            result=self.parse(path,root,start)
            self.assertEqual(result['result'],'INCONCLUSIVE');self.assertFalse(result['restored'])
            self.assertFalse(result['evidence'])

    def test_browser_failure_without_failed_item_is_inconclusive_and_raw_errors_not_copied(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            test=report['suites'][0]['specs'][0]['tests'][0];test['status']='unexpected'
            test['results'][0].update(status='failed',errors=[dict(message='synthetic private value')],attachments=[])
            report['stats'].update(expected=0,unexpected=1);path.write_text(json.dumps(report))
            result=self.parse(path,root,start)
            self.assertEqual(result['result'],'INCONCLUSIVE')
            self.assertNotIn('synthetic private value',json.dumps(result))

    def test_private_path_escape_symlink_and_old_report_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            att=report['suites'][0]['specs'][0]['tests'][0]['results'][0]['attachments'][0]
            att.pop('body');att['path']='/etc/passwd';path.write_text(json.dumps(report))
            with self.assertRaises(ValueError):self.parse(path,root,start)
            report,path,start=self.fixture(root)
            with self.assertRaises(ValueError):self.parse(path,root,datetime.now(timezone.utc).isoformat())
            link=root/'link.json';link.symlink_to(path)
            with self.assertRaises(ValueError):self.parse(link,root,start)

    def test_unknown_observation_duplicate_item_and_invalid_base64_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            for change in ('unknown','duplicate','base64'):
                value=copy.deepcopy(report);attachments=value['suites'][0]['specs'][0]['tests'][0]['results'][0]['attachments']
                if change=='unknown':attachments[0]['body']=body(dict(case_id='TC-SS-04',item='E1',verdict='PASS',observed='private unreviewed text',at=datetime.now(timezone.utc).isoformat()))
                elif change=='duplicate':attachments.append(copy.deepcopy(attachments[0]))
                else:attachments[0]['body']='not base64!'
                path.write_text(json.dumps(value))
                with self.subTest(change=change),self.assertRaises(ValueError):self.parse(path,root,start)

    def test_private_file_attachment_is_mapped_only_inside_evidence_mount(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            att=report['suites'][0]['specs'][0]['tests'][0]['results'][0]['attachments'][0]
            artifact=root/'item.json';artifact.write_bytes(base64.b64decode(att.pop('body')));artifact.chmod(0o600)
            att['path']='/evidence/item.json';path.write_text(json.dumps(report))
            self.assertEqual(self.parse(path,root,start)['result'],'PASS')

    def test_invalid_private_timestamp_never_leaks_into_parser_error(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            report['suites'][0]['specs'][0]['tests'][0]['results'][0]['startTime']='synthetic-private-timestamp'
            path.write_text(json.dumps(report))
            with self.assertRaises(ValueError) as error:self.parse(path,root,start)
            self.assertNotIn('synthetic-private-timestamp',str(error.exception))

    def test_evidence_write_refuses_existing_output_and_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            (root/'observed-TC-SS-04-E1.json').write_text('keep')
            with self.assertRaises(ValueError):self.parse(path,root,start)
            self.assertEqual((root/'observed-TC-SS-04-E1.json').read_text(),'keep')
            path.write_text('{"config":{},"config":{}}')
            with self.assertRaises(ValueError):self.parse(path,root,start)


if __name__=='__main__':unittest.main()
