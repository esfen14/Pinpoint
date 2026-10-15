"""Multiple-parent graph validation, generation and transactional lifecycle regression tests."""
import re
from unittest.mock import patch
import pytest
import sqlalchemy as sa
from app import db
from app.system_models import DeviceParent, DeviceState
from app.network_discovery.create_host_cfg import _create_host_cfg_file, _load_monitored_hosts, config_fingerprint
from tests.unit.test_create_host_cfg import make_device

@pytest.fixture
def devices(db_session, admin_user):
    rows = [make_device(db_session, admin_user, f'node-{i}', f'10.77.0.{i+2}') for i in range(4)]
    db.session.commit()
    return rows

@pytest.fixture
def writer():
    with patch('app.network_discovery.create_host_cfg.regenerate_and_apply_config_status', return_value=('applied', 'Applied.')) as fake:
        yield fake

def parents(child):
    return sorted(db.session.scalars(sa.select(DeviceParent.Parent_ID).where(DeviceParent.Child_ID == child.NetDiscoveryID)))

def link(child, *upstream):
    db.session.add_all([DeviceParent(Child_ID=child.NetDiscoveryID, Parent_ID=p.NetDiscoveryID) for p in upstream])
    db.session.commit()

def save(client, child, ids, **extra):
    return client.put(f'/api/system/hosts/{child.NetDiscoveryID}', json={'parent_device_ids': ids, **extra})

def test_set_change_clear_and_omission(logged_in_client, devices, writer):
    c,a,b,_ = devices
    ids=[a.NetDiscoveryID,b.NetDiscoveryID]
    r=save(logged_in_client,c,ids)
    assert r.status_code == 200
    assert r.json['data']['device']['parent_device_ids'] == ids
    writer.assert_called_once_with(commit_history=False)
    summary=logged_in_client.get(f'/api/system/hosts/{c.NetDiscoveryID}/addresses').json['data']['device']
    assert [p['id'] for p in summary['parents']] == ids
    assert logged_in_client.put(f'/api/system/hosts/{c.NetDiscoveryID}',json={'display_name':'Label'}).status_code == 200
    assert parents(c)==ids
    assert save(logged_in_client,c,[b.NetDiscoveryID]).status_code==200
    assert parents(c)==[b.NetDiscoveryID]
    assert save(logged_in_client,c,[]).status_code==200 and parents(c)==[]

@pytest.mark.parametrize('invalid',[None,'1',[True],[0],[-1],['1'],[99999]])
def test_invalid_ids(logged_in_client,devices,writer,invalid):
    assert save(logged_in_client,devices[0],invalid,display_name='Not saved').status_code==400
    assert devices[0].Display_Name is None
    writer.assert_not_called()

def test_duplicate_self_and_cycle_via_second_parent(logged_in_client,devices,writer):
    c,a,b,root=devices
    link(c,a,b); link(b,root)
    for target,ids in [(c,[a.NetDiscoveryID]*2),(c,[c.NetDiscoveryID]),(root,[c.NetDiscoveryID])]:
        r=save(logged_in_client,target,ids)
        assert r.status_code==400 and r.json['message']
    assert parents(c)==[a.NetDiscoveryID,b.NetDiscoveryID]
    writer.assert_not_called()

@pytest.mark.parametrize('state',[DeviceState.RETIRED,DeviceState.MERGED])
def test_terminal_parent_refused(logged_in_client,devices,writer,state):
    devices[1].Device_State=state; db.session.commit()
    assert save(logged_in_client,devices[0],[devices[1].NetDiscoveryID]).status_code==400
    writer.assert_not_called()

@pytest.mark.parametrize('failure',[('failed','Config rejected'),('failed','Reload failed')])
def test_apply_failure_atomic(logged_in_client,devices,writer,failure):
    c,a,b,_=devices; link(c,a); writer.return_value=failure
    r=save(logged_in_client,c,[b.NetDiscoveryID],display_name='Not saved')
    assert r.status_code==422 and failure[1] in r.json['message']
    assert parents(c)==[a.NetDiscoveryID] and c.Display_Name is None

@pytest.mark.parametrize('state',['paused','address_unknown','retired','merged'])
def test_mixed_eligibility(app,logged_in_client,devices,tmp_path,monkeypatch,state):
    c,a,b,_=devices
    if state=='paused': b.Include_Device_In_Scanning=False
    else: b.Device_State=DeviceState[state.upper()]
    db.session.commit(); link(c,a,b)
    monkeypatch.setitem(app.config,'HOST_CONFIG_DIR',tmp_path)
    text=_create_host_cfg_file(_load_monitored_hosts()).read_text()
    obj=next(x for x in re.findall(r'define host\s*\{(.*?)\}',text,re.S) if re.search(r'host_name\s+'+c.Hostname+r'\s*$',x,re.M))
    assert re.search(r'parents\s+'+a.Hostname+r'\s*$',obj,re.M)
    edge=next(e for e in logged_in_client.get('/api/system/topology').json['data']['edges'] if e['parent_id']==b.NetDiscoveryID)
    assert edge['nagios_eligible'] is False and edge['omission_reason']

def test_multiple_output_and_default_unchanged(app,devices,tmp_path,monkeypatch):
    c,a,b,_=devices; monkeypatch.setitem(app.config,'HOST_CONFIG_DIR',tmp_path)
    before=_create_host_cfg_file(_load_monitored_hosts()).read_text()
    assert not re.search(r'^\s*parents\s',before,re.M)
    link(c,a,b)
    text=_create_host_cfg_file(_load_monitored_hosts()).read_text()
    assert re.search(r'parents\s+'+a.Hostname+','+b.Hostname+r'\s*$',text,re.M)
    db.session.execute(sa.delete(DeviceParent)); db.session.commit()
    assert config_fingerprint(before)==config_fingerprint(_create_host_cfg_file(_load_monitored_hosts()).read_text())

def test_topology_includes_paused_and_unchecked(logged_in_client,devices):
    devices[1].Include_Device_In_Scanning=False; db.session.commit()
    r=logged_in_client.get('/api/system/topology'); assert r.status_code==200
    nodes=r.json['data']['devices']; assert {n['id'] for n in nodes}=={d.NetDiscoveryID for d in devices}
    p=next(n for n in nodes if n['id']==devices[1].NetDiscoveryID)
    assert p['monitoring_state']=='paused' and p['host_state'] is None

def test_unauthenticated(client, db_session):
    assert client.get('/api/system/topology').status_code in (401,302)

def test_auth(limited_client,devices,writer):
    assert limited_client.get('/api/system/topology').status_code==403
    assert save(limited_client,devices[0],[]).status_code==403
    writer.assert_not_called()

def test_retire_atomic(logged_in_client,devices,writer):
    c,a,b,root=devices; link(c,a,b); link(a,root)
    path=f'/api/system/hosts/{a.NetDiscoveryID}/retire'
    writer.return_value=('failed','Rejected')
    assert logged_in_client.post(path).status_code==422
    assert parents(c)==[a.NetDiscoveryID,b.NetDiscoveryID] and a.Device_State is DeviceState.ACTIVE
    writer.return_value=('applied','Applied')
    assert logged_in_client.post(path).status_code==200
    assert parents(c)==[b.NetDiscoveryID] and parents(a)==[]

def test_merge_repoints_and_deduplicates(logged_in_client,devices,writer):
    c,source,target,root=devices; link(c,source,target); link(source,root); link(target,root)
    r=logged_in_client.post(f'/api/system/hosts/{source.NetDiscoveryID}/merge',json={'target_id':target.NetDiscoveryID})
    assert r.status_code==200
    assert parents(c)==[target.NetDiscoveryID] and parents(target)==[root.NetDiscoveryID] and parents(source)==[]

def test_merge_cycle_refused(logged_in_client,devices,writer):
    c,source,target,_=devices; link(c,source); link(target,c)
    r=logged_in_client.post(f'/api/system/hosts/{source.NetDiscoveryID}/merge',json={'target_id':target.NetDiscoveryID})
    assert r.status_code==400 and source.Device_State is DeviceState.ACTIVE
    assert parents(c)==[source.NetDiscoveryID]; writer.assert_not_called()

@pytest.mark.parametrize('bad',['router\nparents injected','router,other','$(whoami)','router!command'])
def test_parent_names_cannot_inject_config(db_session,bad):
    from app.network_discovery.host_config_templates import create_host
    with pytest.raises(ValueError,match='Invalid Nagios parent'):
        create_host({'host_name':'safe','alias':'safe','address':'10.77.0.3','contact_groups':'','parents':[bad]})

def test_deep_graph_is_iterative(db_session):
    from app.network_discovery.device_identity import validate_parent_graph
    pairs={(i+1,i) for i in range(4000)}
    validate_parent_graph(pairs)
    with pytest.raises(ValueError,match='cycle'): validate_parent_graph(pairs|{(0,4000)})

@pytest.mark.parametrize('failure',['validation','reload'])
def test_real_writer_restores_files_and_graph(app,logged_in_client,devices,tmp_path,monkeypatch,failure):
    import app.network_discovery.create_host_cfg as cfg
    c,a,b,_=devices; link(c,a)
    monkeypatch.setitem(app.config,'HOST_CONFIG_DIR',tmp_path)
    text=cfg._create_host_cfg_file(cfg._load_monitored_hosts()).read_text()
    live=tmp_path/'running.cfg';live.write_text(text)
    monkeypatch.setitem(app.config,'NAGIOS_HOST_CFG',live)
    monkeypatch.setitem(app.config,'BACKUP_DIR',tmp_path/'backup')
    with patch.object(cfg,'_validate_config',return_value=(failure!='validation','Rejected')),patch.object(cfg.subprocess,'run',side_effect=RuntimeError('Rejected')):
        response=save(logged_in_client,c,[b.NetDiscoveryID])
    assert response.status_code==422 and parents(c)==[a.NetDiscoveryID]
    assert live.read_text()==text

def test_merge_apply_failure_restores_graph(logged_in_client,devices,writer):
    c,source,target,_=devices;link(c,source)
    writer.return_value=('failed','Rejected')
    r=logged_in_client.post(f'/api/system/hosts/{source.NetDiscoveryID}/merge',json={'target_id':target.NetDiscoveryID})
    assert r.status_code==422 and source.Device_State is DeviceState.ACTIVE
    assert parents(c)==[source.NetDiscoveryID]

def test_host_routes_expose_parents(logged_in_client,db_session,devices):
    from tests.support.seed_helpers import _make_host
    c,a,_,_=devices;link(c,a);_make_host(db_session,hostname=c.Hostname);db.session.commit()
    response=logged_in_client.get('/api/system/network-health/hosts')
    item=next(x for x in response.json['data']['items'] if x['hostname']==c.Hostname)
    assert item['parent_device_ids']==[a.NetDiscoveryID]
    detail=logged_in_client.get(f'/api/system/network-health/hosts/{c.Hostname}/detail').json['data']
    assert detail['parent_device_ids']==[a.NetDiscoveryID]
