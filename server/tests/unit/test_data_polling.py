"""Data polling API validation, live scheduling and atomic saves."""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from apscheduler.schedulers.background import BackgroundScheduler

import app.scheduler as scheduler
from app.system_models import ConfigurationChanges, SystemSettings
from tests.unit.test_settings_permissions import current_settings, save, stored


@pytest.fixture
def running_scheduler(monkeypatch):
    engine = BackgroundScheduler(timezone="UTC")
    engine.start(paused=True)
    job = engine.add_job(lambda: None, 'interval', seconds=60, id='nagios_poll',
                         max_instances=1, coalesce=True)
    monkeypatch.setattr(scheduler, '_scheduler', engine)
    yield engine, job
    engine.shutdown(wait=False)


def test_default(logged_in_client):
    assert current_settings(logged_in_client)['dataPollingInterval'] == 60


@pytest.mark.parametrize('value', [30, 60, 120, 300])
def test_save_reschedules_existing_job(logged_in_client, db_session, running_scheduler, value):
    engine, job = running_scheduler
    before = current_settings(logged_in_client)
    with patch('app.network_discovery.create_host_cfg.regenerate_and_apply_config_status') as nagios:
        response = save(logged_in_client, dataPollingInterval=value)
    assert response.status_code == 200
    assert stored(db_session).Data_Polling_Interval == value
    assert current_settings(logged_in_client)['dataPollingInterval'] == value
    assert engine.get_job('nagios_poll') is job
    assert job.trigger.interval.total_seconds() == value
    assert 0 < (job.next_run_time - datetime.now(timezone.utc)).total_seconds() <= value
    assert job.max_instances == 1 and job.coalesce is True
    assert len(engine.get_jobs()) == 1
    assert current_settings(logged_in_client)['checkInterval'] == before['checkInterval']
    nagios.assert_not_called()
    assert save(logged_in_client, dataPollingInterval=value).status_code == 200
    assert len(engine.get_jobs()) == 1


@pytest.mark.parametrize('value', [0, 31, 600, '30', True, False, None, 30.0, [], {}])
def test_invalid_never_changes_state(logged_in_client, db_session, running_scheduler, value):
    engine, job = running_scheduler
    original = (job.trigger, job.next_run_time)
    before = current_settings(logged_in_client)
    assert save(logged_in_client, dataPollingInterval=value).status_code == 400
    assert current_settings(logged_in_client) == before
    assert (job.trigger, job.next_run_time) == original


def test_permission_and_auth(limited_client, db_session, running_scheduler):
    _, job = running_scheduler
    assert save(limited_client, dataPollingInterval=30).status_code == 403
    assert stored(db_session).Data_Polling_Interval == 60
    assert job.trigger.interval.total_seconds() == 60


def test_omitted_and_conflict(logged_in_client, db_session, running_scheduler):
    _, job = running_scheduler
    old = current_settings(logged_in_client)
    assert save(logged_in_client, dataPollingInterval=120).status_code == 200
    assert logged_in_client.put('/api/system', json=old).status_code == 409
    payload = current_settings(logged_in_client)
    del payload['dataPollingInterval']
    payload['scanFrequency'] = 12
    assert logged_in_client.put('/api/system', json=payload).status_code == 200
    assert stored(db_session).Data_Polling_Interval == 120
    assert job.trigger.interval.total_seconds() == 120


@pytest.mark.parametrize('failure', ['reschedule', 'commit', 'audit'])
def test_failed_save_restores_job_and_database(logged_in_client, db_session, running_scheduler, failure):
    engine, job = running_scheduler
    before = current_settings(logged_in_client)
    original = (job.trigger, job.next_run_time)
    target = {'reschedule': 'apscheduler.job.Job.reschedule',
              'commit': 'app.api.system.settings.db.session.commit',
              'audit': 'app.api.system.settings.create_configuration_log'}[failure]
    with patch(target, side_effect=RuntimeError('injected failure')):
        response = save(logged_in_client, dataPollingInterval=30)
    assert response.status_code == 500
    assert current_settings(logged_in_client) == before
    assert (job.trigger, job.next_run_time) == original
    assert len(engine.get_jobs()) == 1


def test_disabled_stays_disabled_and_audits(logged_in_client, db_session, monkeypatch):
    monkeypatch.setattr(scheduler, '_scheduler', None)
    assert save(logged_in_client, dataPollingInterval=300).status_code == 200
    assert scheduler._scheduler is None
    assert stored(db_session).Data_Polling_Interval == 300
    changes = db_session.session.query(ConfigurationChanges).filter_by(Parameter_Name='Data_Polling_Interval').all()
    assert len(changes) == 1


def test_audit_disabled(logged_in_client, db_session):
    row = db_session.session.get(SystemSettings, 1)
    if row is None:
        current_settings(logged_in_client)
        row = db_session.session.get(SystemSettings, 1)
    row.Audit_Logging = False
    db_session.session.commit()
    assert save(logged_in_client, dataPollingInterval=30).status_code == 200
    assert db_session.session.query(ConfigurationChanges).count() == 0


def test_startup_reads_persisted_interval(logged_in_client, db_session, app, monkeypatch):
    current_settings(logged_in_client)
    row = db_session.session.get(SystemSettings, 1)
    row.Data_Polling_Interval = 120
    db_session.session.commit()
    monkeypatch.setattr(app, 'testing', False)
    monkeypatch.setattr(app, 'debug', False)
    monkeypatch.setattr(scheduler, '_scheduler', None)
    engine = BackgroundScheduler(timezone='UTC')
    # Keep jobs pending without executing Nagios or retention work.
    with patch.object(scheduler, 'BackgroundScheduler', return_value=engine), \
         patch.object(engine, 'start'), patch.object(scheduler.atexit, 'register'):
        scheduler.init_scheduler()
    job = engine.get_job('nagios_poll')
    assert job.trigger.interval.total_seconds() == 120
    assert abs((job.next_run_time - datetime.now(timezone.utc)).total_seconds()) < 2
    assert job.max_instances == 1 and job.coalesce is True
    scheduler.init_scheduler()
    assert len([j for j in engine.get_jobs() if j.id == 'nagios_poll']) == 1


def test_unauthenticated_write(client, db_session):
    assert client.put('/api/system', json={}).status_code == 401


def test_reschedule_does_not_interrupt_or_duplicate_running_poll(logged_in_client, db_session, monkeypatch):
    from threading import Event
    from apscheduler.events import EVENT_JOB_MAX_INSTANCES

    entered, release, skipped = Event(), Event(), Event()
    calls = []

    def poll():
        calls.append('start')
        entered.set()
        release.wait(5)
        calls.append('end')

    engine = BackgroundScheduler(timezone='UTC')
    engine.add_listener(lambda event: skipped.set(), EVENT_JOB_MAX_INSTANCES)
    engine.add_job(poll, 'interval', seconds=60, id='nagios_poll', max_instances=1,
                   coalesce=True, next_run_time=datetime.now(timezone.utc))
    monkeypatch.setattr(scheduler, '_scheduler', engine)
    engine.start()
    try:
        assert entered.wait(3)
        assert save(logged_in_client, dataPollingInterval=30).status_code == 200
        job = engine.get_job('nagios_poll')
        assert calls == ['start']
        # Force the next due time while the first execution is still in flight.
        job.modify(next_run_time=datetime.now(timezone.utc))
        assert skipped.wait(3)
        assert calls == ['start']
        assert job.max_instances == 1 and job.coalesce is True
        assert len(engine.get_jobs()) == 1
    finally:
        release.set()
        engine.shutdown(wait=True)
    assert calls == ['start', 'end']


def test_partial_reschedule_failure_restores_phase(logged_in_client, db_session, running_scheduler):
    _, job = running_scheduler
    before = current_settings(logged_in_client)
    original = (job.trigger, job.next_run_time)
    reschedule = job.__class__.reschedule

    def fail_after_change(self, *args, **kwargs):
        reschedule(self, *args, **kwargs)
        raise RuntimeError('failure after changing trigger')

    with patch('apscheduler.job.Job.reschedule', fail_after_change):
        assert save(logged_in_client, dataPollingInterval=30).status_code == 500
    assert current_settings(logged_in_client) == before
    assert (job.trigger, job.next_run_time) == original


def test_check_and_browser_changes_preserve_polling(logged_in_client, db_session, running_scheduler):
    _, job = running_scheduler
    assert save(logged_in_client, dataPollingInterval=120).status_code == 200
    schedule = (job.trigger, job.next_run_time)
    with patch('app.network_discovery.create_host_cfg.regenerate_and_apply_config_status', return_value=('applied', 'ok')):
        assert save(logged_in_client, checkInterval=2, retryInterval=2).status_code == 200
    assert (job.trigger, job.next_run_time) == schedule
    preferences = logged_in_client.get('/api/user/preferences').get_json()
    preferences['dashboardRefreshRate'] = 0
    assert logged_in_client.put('/api/user/preferences', json=preferences).status_code == 200
    assert current_settings(logged_in_client)['dataPollingInterval'] == 120
    assert (job.trigger, job.next_run_time) == schedule


def test_overdue_runs_coalesce(monkeypatch):
    from datetime import timedelta
    from threading import Event
    from apscheduler.events import EVENT_JOB_SUBMITTED

    submitted = Event()
    runs = []
    engine = BackgroundScheduler(timezone='UTC')
    engine.start(paused=True)
    job = engine.add_job(lambda: None, 'interval', seconds=30, id='nagios_poll',
                         coalesce=True, max_instances=1)
    monkeypatch.setattr(scheduler, '_scheduler', engine)
    engine.add_listener(lambda event: (runs.extend(event.scheduled_run_times), submitted.set()), EVENT_JOB_SUBMITTED)
    job.modify(next_run_time=datetime.now(timezone.utc) - timedelta(seconds=61))
    engine.resume()
    try:
        assert submitted.wait(3)
        assert len(runs) == 1
    finally:
        engine.shutdown(wait=True)
