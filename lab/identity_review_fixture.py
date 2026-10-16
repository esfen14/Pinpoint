"""Opt-in fixtures for #164 on a disposable Docker appliance, never production.

Run with PINPOINT_IDENTITY_LAB=1 and PINPOINT_SCHEDULER=0 inside an isolated
appliance. No network scan is performed: controlled observations exercise the
real discovery reconciler; configuration uses the real Nagios apply path.
"""
import json
import os
import sys
import time

import sqlalchemy as sa

if os.environ.get('PINPOINT_IDENTITY_LAB') != '1' or os.environ.get('PINPOINT_SCHEDULER') != '0':
    raise SystemExit('Requires an explicitly opted-in disposable appliance with scheduler disabled.')

from app import app, db
from app.api.plugin.reconcile import reconcile_plugin_monitoring
from app.network_discovery.device_identity import reconcile_scan
from app.network_discovery.port_lifecycle import process_device_ports
from app.system_models import (
    ActivityLog, DeviceReviewItem, DeviceState, DiscoveryStatus, NetworkDiscovery,
    NetworkDiscoveryStatus, Open_TCP_Services, ReviewKind, User,
)

NETWORK = '10.79.164.0/28'
CURRENT_IP = '10.79.164.2'
SOURCE = 'issue164-duplicate'
TARGET = 'issue164-survivor'


def observe(status_id, ip, mac, name, ports):
    """Reconcile one controlled scan result and process ports, committing like discovery."""
    services = {'tcp': {str(p): {'service_name': s, 'identified_by': 'FINGERPRINT'} for p, s in ports.items()}, 'udp': {}}
    observation = {NETWORK: {ip: {'data': {'hostname': name, 'mac_address': mac, 'os': 'Linux', 'identifiers': []}, 'services': services}}}
    device = reconcile_scan(observation, status_id)[(NETWORK, ip)]
    process_device_ports(device, services, host_seen=True)
    db.session.commit()
    return device


def records():
    """Return only the two uniquely named fixture records."""
    source = db.session.scalar(sa.select(NetworkDiscovery).where(NetworkDiscovery.Display_Name == SOURCE))
    target = db.session.scalar(sa.select(NetworkDiscovery).where(NetworkDiscovery.Display_Name == TARGET))
    assert source is not None and target is not None
    return source, target


with app.app_context():
    admin = db.session.scalar(sa.select(User).where(User.Email == 'admin@test.com'))
    assert admin is not None
    if sys.argv[1] == 'seed':
        assert db.session.scalar(sa.select(sa.func.count()).select_from(NetworkDiscovery)) == 0, 'Use a fresh disposable appliance.'
        log = ActivityLog(Action_Type='Issue 164 controlled discovery observations', UserID=admin.UserID)
        db.session.add(log)
        db.session.flush()
        status = NetworkDiscoveryStatus(Status=DiscoveryStatus.SUCCESS, Progress=100, Message='controlled identity observations', LogID=log.LogID)
        db.session.add(status)
        db.session.flush()
        old = observe(status.DiscoveryStatusID, '10.79.164.3', '00:11:22:33:44:01', SOURCE, {22: 'ssh', 8080: 'http'})
        old_id = old.NetDiscoveryID
        moved = observe(status.DiscoveryStatusID, CURRENT_IP, '00:11:22:33:44:01', SOURCE, {22: 'ssh', 8080: 'http'})
        assert moved.NetDiscoveryID == old_id and moved.IP_Address == CURRENT_IP
        assert db.session.scalar(sa.select(sa.func.count()).select_from(NetworkDiscovery)) == 1
        assert not db.session.scalars(sa.select(DeviceReviewItem)).all(), 'Recognized move must need no review.'
        target = observe(status.DiscoveryStatusID, CURRENT_IP, '00:11:22:33:44:02', TARGET, {22: 'ssh'})
        old.Display_Name = SOURCE
        target.Display_Name = TARGET
        assert old.Device_State is DeviceState.ADDRESS_UNKNOWN
        reviews = db.session.scalars(sa.select(DeviceReviewItem).where(DeviceReviewItem.Kind == ReviewKind.IP_REUSE)).all()
        assert len(reviews) == 1
        # Leave the generated insufficient-candidate review intact, exercising lookup.
        assert old_id in reviews[0].Candidate_Device_IDs
        db.session.add(DeviceReviewItem(Kind=ReviewKind.SERVICE_CHANGED, IP_Address=CURRENT_IP,
            Message='Issue 164 fixture: port mismatch is excluded from identity review', Candidate_Device_IDs=[old_id]))
        db.session.commit()
        applied = reconcile_plugin_monitoring(admin.UserID)
        assert applied['success'], applied['message']
        print(json.dumps({'source': old_id, 'target': target.NetDiscoveryID, 'review': reviews[0].ReviewID, 'recognized_move_same_record': True, 'config_ok': True}))
    elif sys.argv[1] == 'prime-source':
        # Force one real check of the fixture's otherwise disabled address-unknown
        # host, so its information drawer can be tested from a genuine snapshot.
        from app.history_models import HostStatus
        from app.nagios.status import get_status
        source, target = records()
        assert source.Device_State is DeviceState.ADDRESS_UNKNOWN
        command = f"[{int(time.time())}] SCHEDULE_FORCED_HOST_CHECK;{SOURCE};{int(time.time())}\n"
        descriptor = os.open('/usr/local/nagios/var/rw/nagios.cmd', os.O_WRONLY | os.O_NONBLOCK)
        try:
            os.write(descriptor, command.encode())
        finally:
            os.close(descriptor)
        for attempt in range(15):
            time.sleep(2)
            get_status()
            if db.session.scalar(sa.select(HostStatus).where(HostStatus.Hostname == SOURCE)) is not None:
                break
        else:
            raise AssertionError('No genuine source snapshot after forced lab check.')
        print(json.dumps({'real_source_snapshot': True}))
    elif sys.argv[1] == 'verify':
        source, target = records()
        assert source.Device_State is DeviceState.MERGED and source.Merged_Into_ID == target.NetDiscoveryID
        assert target.IP_Address == CURRENT_IP and target.Device_State is DeviceState.ACTIVE
        assert db.session.scalar(sa.select(Open_TCP_Services).where(Open_TCP_Services.NetDiscoveryID == target.NetDiscoveryID, Open_TCP_Services.Port_Number == 8080)) is not None
        assert not db.session.scalars(sa.select(DeviceReviewItem).where(DeviceReviewItem.Resolved_At.is_(None))).all()
        config = open('/usr/local/nagios/etc/objects/hosts.cfg').read()
        assert SOURCE not in config and TARGET in config
        print(json.dumps({'source_merged': True, 'target_address_retained': True, 'nonconflicting_port_moved': True, 'reviews_resolved': True, 'source_removed_from_config': True, 'target_in_config': True}))
    else:
        raise SystemExit('Use seed, prime-source or verify.')
