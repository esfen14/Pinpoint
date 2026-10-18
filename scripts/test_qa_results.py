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

    def parse(self,path,root,start):return r.parse_report(path,'TC-SS-04',root,start)

    def test_complete_single_attempt_pass_has_sanitized_item_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);report,path,start=self.fixture(root)
            result=self.parse(path,root,start)
            self.assertEqual(result['result'],'PASS');self.assertTrue(result['restored'])
            self.assertEqual(result['evidence']['E1']['reference'],'observed-TC-SS-04-E1.json')
            self.assertTrue((root/result['evidence']['E1']['reference']).is_file())
            self.assertNotIn('body',json.dumps(result))

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
