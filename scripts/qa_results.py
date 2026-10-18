#!/usr/bin/env python3
"""Parse supported current-case reports strictly; never run a browser or lab.

Only reviewed fixed observations are copied into sanitized item files. A failed
browser attempt without explicit failed-item evidence is INCONCLUSIVE, not a
product failure. These current adapters emit PASS items only; FAIL import is not
implemented. Cleanup attachment is necessary, not sufficient for live recovery.
"""
from __future__ import annotations
import base64
import binascii
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import stat

spec=importlib.util.spec_from_file_location('coverage',Path(__file__).with_name('qa_coverage.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
transport_spec=importlib.util.spec_from_file_location('transport',Path(__file__).with_name('qa_transport.py'))
t=importlib.util.module_from_spec(transport_spec);transport_spec.loader.exec_module(t)
OBSERVATIONS={'TC-SS-04': {'E1': 'System Status absent from sidebar; direct address redirects to Settings.'},
 'TC-HIS-01': {'E1': 'History absent from sidebar; direct address redirects to Settings; API address returns '
                     '403.'},
 'TC-RPT-07': {'E1': 'Report absent from sidebar; direct address redirects to Settings; API address returns '
                     '403.'},
 'TC-LOG-05': {'E1': 'System Logs absent from sidebar; direct address redirects to Settings; API address '
                     'returns 403.'},
 'TC-PLG-07': {'E1': 'Plugins absent from sidebar; direct address redirects to Settings; API address returns '
                     '403.'},
 'TC-ACC-09': {'E1': 'Manage Accounts absent from sidebar; direct address redirects to Settings.',
               'E2': 'Accounts API address returns 403.'},
 'TC-NCPA-08': {'E1': 'NCPA Deployment absent from sidebar; direct address redirects to Settings.'},
 'TC-ACC-08': {'E1': 'Super Admin sees the Email Alerts column and email-alert checkbox.',
               'E2': 'The qa-accounts user does not see the email-alert checkbox.'},
 'TC-ROL-04': {'E1': 'Sidebar contains Overview and Settings only.',
               'E2': 'All 13 protected page addresses redirect to the Dashboard.',
               'E3': 'All three protected API addresses return 403.'},
 'TC-DI-02': {'E1': 'Port group headers appear in the required order.',
              'E2': 'Every shown group has a matching positive count; empty groups are absent.',
              'E3': 'Each visible port group is ordered TCP then UDP, by port number.'},
 'TC-DI-03': {'E1': 'Exactly one reason is shown and the held-back reason is absent.',
              'E2': 'The reason explains the expected/found names and says monitoring waits for acknowledgement.'},
 'TC-DASH-07': {'E1': 'Network Latency and both Network Performance metrics show No data.',
                'E2': 'Average Resource Utilization is absent without NCPA data.'}}
MODULE_CASES=frozenset({'TC-ACC-08','TC-ROL-04','TC-DI-02','TC-DI-03','TC-DASH-07'})


def unique_object(pairs):
    """Reject duplicate JSON keys, including nested evidence identities."""
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate report key')
        result[key]=value
    return result


def decode_json(raw:bytes):
    """Parse bounded private JSON without surfacing its values in exceptions."""
    def invalid(_):raise ValueError('Nonfinite JSON value')
    try:return json.loads(raw,object_pairs_hook=unique_object,parse_constant=invalid)
    except (ValueError,UnicodeError):raise ValueError('Invalid private report JSON') from None


def read_private(path:Path,root:Path,limit:int) -> bytes:
    """Read a bounded same-owner regular file inside the reviewed private root."""
    path=t.clean_path(path)
    if not path.is_relative_to(root):raise ValueError('Report evidence escapes private root')
    try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    except OSError:raise ValueError('Unavailable private report evidence') from None
    with os.fdopen(fd,'rb') as source:
        info=os.fstat(source.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1
            or info.st_mode & 0o077 or info.st_size>limit):raise ValueError('Unsafe or oversized private evidence')
        value=source.read(limit+1)
        if len(value)>limit:raise ValueError('Private evidence grew past limit')
        return value


def instant(value) -> datetime:
    """Require an explicit timezone for report/observation timestamps."""
    if not isinstance(value,str):raise ValueError('Missing report timestamp')
    observed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if observed.tzinfo is None:raise ValueError('Ambiguous report timestamp')
    return observed


def attachment_data(attachment:dict,root:Path) -> dict:
    """Decode inline base64 or map the fixed container evidence mount to host paths."""
    if attachment.get('contentType')!='application/json':raise ValueError('Expected JSON evidence attachment')
    if ('body' in attachment)==('path' in attachment):raise ValueError('Ambiguous evidence source')
    if 'body' in attachment:
        value=attachment['body']
        if not isinstance(value,str) or len(value)>8192:raise ValueError('Oversized inline evidence')
        try:raw=base64.b64decode(value,validate=True)
        except (binascii.Error,ValueError):raise ValueError('Invalid attachment encoding') from None
        if len(raw)>4096:raise ValueError('Oversized attachment')
    else:
        value=attachment['path']
        if not isinstance(value,str):raise ValueError('Missing attachment path')
        container=Path(value)
        if not container.is_relative_to('/evidence') or '..' in container.parts:
            raise ValueError('Attachment outside fixed evidence mount')
        raw=read_private(root/container.relative_to('/evidence'),root,4096)
    result=decode_json(raw)
    if not isinstance(result,dict):raise ValueError('Malformed expected-item evidence')
    return result


def parse_report(path:Path,case_id:str,evidence_root:Path,run_started_at:str,
                 run_finished_at:str,*,run_elapsed_seconds:float,max_run_seconds:float) -> dict:
    """Validate a single current adapter/attempt and write only sanitized observations.

    Both bounds must come from the owned container attach, not the report or
    caller import time. max_run_seconds is the consumed remaining case budget.
    Playwright duration sums monotonic slots, not a wall-clock interval. Parser
    output still requires the supervisor's independent runtime/cleanup proof.
    Caller must preserve the raw report privately and never import it as prose.
    """
    try:return parse_checked(path,case_id,evidence_root,run_started_at,run_finished_at,run_elapsed_seconds=run_elapsed_seconds,max_run_seconds=max_run_seconds)
    except (ValueError,KeyError,TypeError,IndexError,OverflowError,OSError,RecursionError):
        raise ValueError('Malformed or unavailable current-case report') from None


def parse_checked(path:Path,case_id:str,evidence_root:Path,run_started_at:str,
                  run_finished_at:str,*,run_elapsed_seconds:float,max_run_seconds:float) -> dict:
    """Internal checked parse; supplied documents are observations, never instructions."""
    root=t.private_directory(evidence_root)
    if case_id not in OBSERVATIONS:raise ValueError('Unsupported current-case report')
    mapping=c.load()['cases'][case_id]
    if mapping['status']!='implemented' or set(mapping['items'])!=set(OBSERVATIONS[case_id]):raise ValueError('Unreviewed adapter coverage')
    report=decode_json(read_private(path,root,16*1024*1024))
    config=report['config'];project=config['projects'];filtered=config['filteredProjects']
    pinned=json.loads((c.ROOT/'client/package.json').read_text())['devDependencies']['@playwright/test']
    is_module=case_id in MODULE_CASES
    project_name='qa-modules-2-9' if is_module else 'qa-permissions'
    config_path='/work/client/playwright.modules.qa.config.ts' if is_module else '/work/client/playwright.qa.config.ts'
    spec_file='qa-modules-2-9.lab.spec.ts' if is_module else 'qa-permissions.lab.spec.ts'
    if (config.get('version')!=pinned or config.get('workers')!=1 or config.get('forbidOnly') is not True
        or config.get('fullyParallel') is not False or config.get('configFile')!=config_path
        or config.get('rootDir')!='/work/client/e2e'
        or config.get('metadata',{}).get('currentCaseIds')!=[case_id]
        or config.get('metadata',{}).get('mode')!='scripted automation'
        or len(project)!=1 or len(filtered)!=1):raise ValueError('Report configuration differs from reviewed adapter')
    if (project[0].get('name')!=project_name or project[0].get('retries')!=0
        or project[0].get('repeatEach')!=1 or project[0].get('outputDir')!='/evidence/artifacts'
        or filtered[0].get('name')!=project_name or filtered[0].get('retries')!=0
        or filtered[0].get('dependencies')!=[]):raise ValueError('Broader or retried report selection')
    use=filtered[0]['use']
    if use.get('baseURL')!='http://127.0.0.1:18080' or any(use.get(k)!='off' for k in ('trace','video','screenshot')):
        raise ValueError('Unreviewed origin or capture policy')
    def specs(suites):
        values=[]
        for suite in suites:
            values.extend(suite.get('specs',[]));values.extend(specs(suite.get('suites',[])))
        return values
    selected=specs(report['suites'])
    if len(selected)!=1 or selected[0].get('title')!=mapping['adapter']['title'] or selected[0].get('file')!=spec_file:
        raise ValueError('Report contains wrong or additional cases')
    tests=selected[0]['tests']
    if len(tests)!=1 or tests[0].get('projectName')!=project_name or tests[0].get('expectedStatus')!='passed':
        raise ValueError('Unexpected project/expected failure annotation')
    results=tests[0]['results']
    if len(results)!=1 or results[0].get('retry')!=0:raise ValueError('Exactly one initial attempt required')
    attempt=results[0];status=attempt.get('status')
    if status not in ('passed','failed','timedOut','interrupted'):raise ValueError('Skipped or unknown attempt')
    stats=report['stats']
    for key in ('expected','unexpected','flaky','skipped'):
        if type(stats.get(key)) is not int or stats[key]<0:raise ValueError('Invalid unique-case totals')
    if stats['flaky'] or stats['skipped'] or stats['expected']+stats['unexpected']!=1:raise ValueError('Flaky/skipped/broader totals')
    if (status=='passed')!=(stats['expected']==1) or tests[0].get('status')!=('expected' if status=='passed' else 'unexpected'):
        raise ValueError('Attempt and summary disagree')
    duration=attempt['duration']
    if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or not 0<=duration<=60000:
        raise ValueError('Unbounded report duration')
    # Independent host wall-clock bounds surround the owned attach only. Never
    # derive a wall end from Playwright's sum of selected monotonic timeout slots,
    # or use parser/import time as the completion bound. The narrow pilot caps
    # this envelope at its reviewed 300-second case budget; no timing grace.
    launched=instant(run_started_at);finished=instant(run_finished_at)
    began=instant(attempt['startTime']);report_began=instant(stats['startTime'])
    report_duration=stats['duration']
    if (type(max_run_seconds) not in (int,float) or not math.isfinite(max_run_seconds)
        or not 0<max_run_seconds<=300
        or type(run_elapsed_seconds) not in (int,float) or not math.isfinite(run_elapsed_seconds)
        or not 0<run_elapsed_seconds<=max_run_seconds
        or not 0<(finished-launched).total_seconds()<=max_run_seconds
        or finished>datetime.now(timezone.utc)
        or not launched<=report_began<=began<=finished
        or type(report_duration) not in (int,float) or not math.isfinite(report_duration)
        or not duration<=report_duration<=min(90000,run_elapsed_seconds*1000)):
        raise ValueError('Stale or inconsistent report time')
    attachments={};allowed={case_id+'-'+item for item in OBSERVATIONS[case_id]}|{'cleanup'}
    for att in attempt.get('attachments',[]):
        name=att.get('name')
        if name not in allowed:
            # Never open/copy diagnostics; disallow unexpected media captures.
            if att.get('contentType','').startswith(('image/','video/','audio/')) or str(name).startswith(case_id+'-'):
                raise ValueError('Unreviewed evidence/capture')
            continue
        if name in attachments:raise ValueError('Duplicate expected-item or cleanup attachment')
        attachments[name]=attachment_data(att,root)
    cleanup_data=attachments.get('cleanup')
    cleanup=(isinstance(cleanup_data,dict) and set(cleanup_data)=={'session_closed'}
             and cleanup_data['session_closed'] is True)
    # Validate every supplied expected item before writing any sanitized output.
    observations={}
    for item,text in OBSERVATIONS[case_id].items():
        observation=attachments.get(case_id+'-'+item)
        if observation is None:continue
        if (set(observation)!={'case_id','item','verdict','observed','at'} or observation['case_id']!=case_id
            or observation['item']!=item or observation['verdict']!='PASS'
            or observation['observed']!=text or not began<=instant(observation['at'])<=finished):
            raise ValueError('Unreviewed or stale expected-item observation')
        observations[item]=observation
    evidence={}
    for item,observation in observations.items():
        name=f'observed-{case_id}-{item}.json'
        # Never overwrite earlier evidence, including an interrupted import.
        try:fd=os.open(root/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        except OSError:raise ValueError('Sanitized evidence already exists or is unsafe') from None
        with os.fdopen(fd,'w') as output:
            json.dump(observation,output);output.flush();os.fsync(output.fileno())
        directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
        evidence[item]=dict(verdict='PASS',observed=OBSERVATIONS[case_id][item],reference=name)
    passed=(status=='passed' and not attempt.get('errors') and not attempt.get('error') and not report.get('errors')
            and cleanup and set(evidence)==set(OBSERVATIONS[case_id]))
    return dict(result='PASS' if passed else 'INCONCLUSIVE',evidence=evidence,restored=cleanup,
        reason='' if passed else 'Browser execution or expected-item/cleanup evidence incomplete; review private artifacts')
