"""Read-only guest probe body, appended to the standalone deployment observer.

No application imports, mutations or secrets are returned. The host supplies a
reviewed manifest and an email fingerprint, never credentials. This body is sent
through the bounded SSH runner, not installed into the serving application.
"""

def runtime_file(path):
    """Hash canonical runtime files, including legitimate package-cache hard links."""
    path=clean_path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as source:
        before=os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size>64*1024*1024:
            raise ValueError('Unsafe runtime file')
        digest=hashlib.sha256();total=0
        while chunk:=source.read(128*1024):
            total+=len(chunk)
            if total>64*1024*1024:raise ValueError('Runtime file grew beyond bound')
            digest.update(chunk)
        if (stamp(before)!=stamp(os.fstat(source.fileno())) or stamp(before)!=stamp(path.lstat())
            or before.st_nlink!=path.stat().st_nlink):raise ValueError('Runtime file changed')
    return dict(sha256=digest.hexdigest(),stamp=stamp(before),links=before.st_nlink)


def runtime_inventory(root):
    """Fingerprint installed package code/resources without following links."""
    root=clean_path(root);entries={};total=0
    for directory,folders,files in os.walk(root,followlinks=False):
        folders[:]=[name for name in folders if name!='__pycache__']
        if any((Path(directory)/name).is_symlink() for name in folders):
            raise ValueError('Symlink runtime directory')
        for name in files:
            path=Path(directory)/name;value=runtime_file(path)
            entries[path.relative_to(root).as_posix()]=value;total+=value['stamp'][2]
            if len(entries)>10000 or total>256*1024*1024:raise ValueError('Runtime inventory budget exceeded')
    if not entries:raise ValueError('Runtime inventory empty')
    return dict(inventory_sha256=manifest_digest(entries),file_count=len(entries),
        latest_ctime_ns=max(value['stamp'][4] for value in entries.values()))


def pilot_guest(manifest, email_fingerprint):
    import sqlite3
    import subprocess
    root=Path('/opt/pinpoint/Network-Diagnosis-System')
    observation=observe(manifest,root)
    pid=int(subprocess.check_output(['systemctl','show','pinpoint-gunicorn.service',
        '--property=MainPID','--value'],timeout=5).strip())
    process=Path('/proc')/str(pid)
    ticks=int((process/'stat').read_text().rsplit(') ',1)[1].split()[19])
    boot=next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
    launch_epoch=boot+ticks/os.sysconf('SC_CLK_TCK')
    environment=dict(entry.split(b'=',1) for entry in bounded_read(process/'environ',131072).split(b'\0') if b'=' in entry)
    if environment.get(b'PINPOINT_SCHEDULER')!=b'0' or environment.get(b'DATABASE_URL'):
        raise ValueError('Reviewed scheduler-off/default-database baseline required')
    configuration={str(p):file_observation(p) for p in [Path('/etc/pinpoint/pinpoint.env'),
        Path('/etc/systemd/system/pinpoint-gunicorn.service'),
        Path('/run/systemd/system/pinpoint-gunicorn.service.d/90-qa-preparation.conf'),
        Path('/run/pinpoint-qa-preparation.env')]}
    dependencies=runtime_inventory(Path('/opt/pinpoint/venv/lib/python3.14/site-packages'))
    sources={name:file_observation(root/name) for name in manifest['sources']}
    if any(value['stamp'][4]/1e9>=launch_epoch for group in (configuration,sources) for value in group.values()):
        raise ValueError('Deployment inputs changed since controlled launch')
    if dependencies['latest_ctime_ns']/1e9>=launch_epoch:raise ValueError('Dependencies changed since launch')
    executables={row['pid']:runtime_file(Path(os.readlink(Path('/proc')/str(row['pid'])/'exe')).resolve()) for row in observation['processes']}
    connection=sqlite3.connect((root/'server/system.db').as_uri()+'?mode=ro',uri=True)
    connection.execute('PRAGMA query_only=ON')
    users=connection.execute('SELECT u.Email,u.Status,u.Needs_Setup,u.Must_Change_Password,r.Name,r.Is_Active,(SELECT count(*) FROM ROLE_PERMISSION p WHERE p.RoleID=r.RoleID) FROM USER u JOIN ROLE r ON r.RoleID=u.RoleID').fetchall()
    staff=[list(row[1:]) for row in users if hashlib.sha256(row[0].encode()).hexdigest()==email_fingerprint]
    networks=connection.execute('SELECT Networks FROM DISCOVERY_SETTINGS').fetchall()
    scans=connection.execute('SELECT count(*),max(Start_At) FROM NETWORK_DISCOVERY_STATUS').fetchone()
    versions={}
    for name in ['system.db','history.db']:
        db=sqlite3.connect((root/'server'/name).as_uri()+'?mode=ro',uri=True)
        versions[name]=[r[0] for r in db.execute('SELECT version_num FROM alembic_version')];db.close()
    connection.close()
    if (int(subprocess.check_output(['systemctl','show','pinpoint-gunicorn.service','--property=MainPID','--value'],timeout=5).strip())!=pid
        or any(file_observation(root/name)!=value for name,value in sources.items())):
        raise ValueError('Guest changed during observation')
    return dict(observation=observation,main_pid=pid,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        configuration=configuration,dependencies=dependencies,sources=sources,executables=executables,
        staff=staff,networks=networks,scans=scans,database_versions=versions,scheduler_enabled=False,inputs_precede_launch=True)
