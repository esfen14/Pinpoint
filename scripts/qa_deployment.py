"""Read-only Git/artifact/process observation; no SSH, restart, HTTP or live CLI.

Disk matches and candidate Gunicorn process metadata are useful evidence, not
proof of loaded backend code or bytes actually served by the frontend. This
module never emits a verified running revision or positive runtime readiness.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time

HASH=re.compile(r'[0-9a-f]{64}')
REV=re.compile(r'[0-9a-f]{40}')
MAX_FILE=32*1024*1024
BANNED={'.git','.venv','venv','__pycache__','tests','node_modules','dist'}
SUFFIXES={'.py','.json','.txt','.toml','.ini','.cfg','.sh','.js','.jsx','.ts','.tsx','.css','.html','.svg','.png','.ico','.woff','.woff2','.ttf','.webp','.jpg','.jpeg','.map'}
REQUIRED={'server/server.py','server/config.py','server/requirements.txt','server/app/__init__.py','client/package.json'}


def manifest_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def clean_path(value):
    """Keep the read-only observer standalone for a future guest-side probe."""
    path=Path(value)
    if not path.is_absolute() or path.resolve()!=path or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Canonical deployment path required')
    return path


def relative_name(value):
    if (not isinstance(value,str) or not value or len(value)>512 or any(c in value for c in '\x00\r\n')
        or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts
        or str(PurePosixPath(value))!=value):raise ValueError('Invalid artifact path')
    return PurePosixPath(value)


def source_name(value):
    path=relative_name(value)
    return (path.parts[0] in ('server','client') and not any(p in BANNED or p.startswith('.') for p in path.parts)
        and path.suffix in SUFFIXES and (path.parts[0]=='server' or value.startswith('client/src/')
            or value in ('client/package.json','client/package-lock.json','client/index.html')
            or value.startswith(('client/vite.config.','client/tsconfig'))))


def seal(value):
    value['checksum']=manifest_digest({k:v for k,v in value.items() if k!='checksum'})
    return value


def validate(value):
    if (not isinstance(value,dict) or value.get('version')!=1 or not REV.fullmatch(value.get('target_revision',''))
        or not isinstance(value.get('reviewed_by'),str) or not value['reviewed_by'].strip()
        or value.get('checksum')!=manifest_digest({k:v for k,v in value.items() if k!='checksum'})):
        raise ValueError('Reviewed source/build manifest required')
    for group in ('sources','frontend'):
        entries=value.get(group)
        if not isinstance(entries,dict) or not entries or len(entries)>10000:raise ValueError('Incomplete artifact manifest')
        for name,digest in entries.items():
            path=relative_name(name)
            if (not isinstance(digest,str) or not HASH.fullmatch(digest) or path.suffix not in SUFFIXES
                or any(part.startswith('.') for part in path.parts) or (group=='sources' and not source_name(name))):
                raise ValueError('Unreviewed artifact path or digest')
    if not REQUIRED<=set(value['sources']) or 'index.html' not in value['frontend']:
        raise ValueError('Required source/build entrypoints missing')


def stamp(info):return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def file_observation(path):
    """Hash an unchanged regular non-symlink file, never expose its contents."""
    path=clean_path(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as source:
        before=os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size>MAX_FILE:
            raise ValueError('Unsafe or oversized deployment artifact')
        digest=hashlib.sha256();total=0
        while chunk:=source.read(128*1024):
            total+=len(chunk)
            if total>MAX_FILE:raise ValueError('Artifact grew beyond bound')
            digest.update(chunk)
        if stamp(before)!=stamp(os.fstat(source.fileno())) or stamp(before)!=stamp(path.lstat()):
            raise ValueError('Deployment artifact changed during observation')
    return dict(sha256=digest.hexdigest(),stamp=stamp(before))


def tree_files(root):
    """List regular artifact paths without traversing symlinks or secret stores."""
    root=clean_path(root)
    if not root.exists():return set()
    result=set()
    for directory,folders,files in os.walk(root,followlinks=False):
        folders[:]=[name for name in folders if name not in BANNED and not name.startswith('.')]
        files=[name for name in files if not name.startswith('.')]
        for name in (*folders,*files):
            if (Path(directory)/name).is_symlink():raise ValueError('Symlink in deployment tree')
        for name in files:
            path=Path(directory)/name
            if not name.startswith('.') and path.suffix in SUFFIXES:result.add(path.relative_to(root).as_posix())
        if len(result)>10000:raise ValueError('Deployment tree too large')
    return result


def make_manifest(repository,revision,frontend_root,reviewed_by):
    """Bind expected source hashes to Git objects plus reviewed build artifacts.

    This is a local preparation operation. Build hashes still require reviewed
    provenance linking that build to its source; reading dist does not prove it.
    """
    if (not isinstance(revision,str) or not REV.fullmatch(revision)
        or not isinstance(reviewed_by,str) or not reviewed_by.strip()):
        raise ValueError('Explicit full revision and build review required')
    repository=clean_path(repository);deadline=time.monotonic()+30
    def git(*args):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise ValueError('Manifest preparation budget exhausted')
        try:
            result=subprocess.run(['git','-c','protocol.allow=never','-C',str(repository),*args],
                capture_output=True,timeout=min(5,remaining),check=True,
                env={'PATH':'/usr/bin:/bin','HOME':str(repository),'GIT_CONFIG_NOSYSTEM':'1',
                    'GIT_CONFIG_GLOBAL':os.devnull,'GIT_NO_REPLACE_OBJECTS':'1','GIT_NO_LAZY_FETCH':'1'})
        except (OSError,subprocess.SubprocessError):raise ValueError('Git object source unavailable') from None
        if len(result.stdout)>64*1024*1024:raise ValueError('Git object output too large')
        return result.stdout
    sources={};total=0
    for row in git('ls-tree','-rz',revision,'--','server','client').split(b'\x00'):
        if not row:continue
        metadata,name=row.split(b'\t',1);name=name.decode();mode,kind,object_id=metadata.decode().split()
        if not source_name(name):continue
        if kind!='blob' or mode not in ('100644','100755'):raise ValueError('Nonregular source object')
        blob=git('cat-file','blob',object_id)
        total+=len(blob)
        if len(blob)>MAX_FILE or total>64*1024*1024 or len(sources)>=10000:raise ValueError('Source manifest too large')
        sources[name]=hashlib.sha256(blob).hexdigest()
    frontend={}
    for name in sorted(tree_files(frontend_root)):
        observation=file_observation(Path(frontend_root)/name);total+=observation['stamp'][2]
        if total>64*1024*1024:raise ValueError('Combined source/build artifact budget exceeded')
        frontend[name]=observation['sha256']
    value=seal(dict(version=1,target_revision=revision,reviewed_by=reviewed_by,sources=sources,frontend=frontend))
    validate(value);return value


def bounded_read(path,limit):
    with path.open('rb') as source:value=source.read(limit+1)
    if len(value)>limit:raise ValueError('Process metadata too large')
    return value


def process_observations(app_root,proc_root,latest_source_ctime):
    """Candidate process metadata only; never copy command arguments/environ."""
    rows=[]
    boot=next(int(line.split()[1]) for line in (proc_root/'stat').read_text().splitlines() if line.startswith('btime '))
    def ticks(path):
        try:
            value=int(path.read_text().rsplit(') ',1)[1].split()[19])
            if value<1:raise ValueError()
            return value
        except (ValueError,IndexError):raise ValueError('Process start identity unavailable') from None
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():continue
        try:
            command=bounded_read(entry/'cmdline',65536)
            if b'gunicorn' not in command.lower():continue
            cwd=os.readlink(entry/'cwd')
            if cwd!=str(app_root/'server'):continue
            started=ticks(entry/'stat');executable=os.readlink(entry/'exe')
            status=dict(line.split(':',1) for line in (entry/'status').read_text().splitlines() if ':' in line)
            again=dict(line.split(':',1) for line in (entry/'status').read_text().splitlines() if ':' in line)
            if (started!=ticks(entry/'stat') or command!=bounded_read(entry/'cmdline',65536)
                or cwd!=os.readlink(entry/'cwd') or executable!=os.readlink(entry/'exe') or status['PPid']!=again['PPid']):
                raise ValueError('Process identity changed during observation')
            start_lower=boot+started/os.sysconf('SC_CLK_TCK')
            rows.append(dict(pid=int(entry.name),parent_pid=int(status['PPid']),start_ticks=started,
                command_hash=hashlib.sha256(command).hexdigest(),executable_name=Path(executable).name,
                starts_after_source_files=start_lower>latest_source_ctime+1))
            if len(rows)>128:raise ValueError('Ambiguous application process inventory')
        except FileNotFoundError:raise ValueError('Process inventory changed or inaccessible') from None
    return sorted(rows,key=lambda row:row['pid'])


def observe(manifest,app_root,*,proc_root=Path('/proc')):
    """Collect stable disk/process facts without asserting loaded/served identity."""
    validate(manifest);app_root=clean_path(app_root);proc_root=Path(proc_root)
    python_before={name for name in tree_files(app_root/'server') if name.endswith('.py')}
    frontend_before=tree_files(app_root/'client'/'dist');observed={};total=0
    for group in ('sources','frontend'):
        base=app_root if group=='sources' else app_root/'client'/'dist'
        for name in manifest[group]:
            path=base/name
            try:record=file_observation(path)
            except FileNotFoundError:record=None
            observed[(group,name)]=(path,record)
            if record:total+=record['stamp'][2]
            if total>64*1024*1024:raise ValueError('Deployment artifact budget exceeded')
    latest=max((record['stamp'][4]/1e9 for (group,_),(_,record) in observed.items() if group=='sources' and record),default=0)
    processes=process_observations(app_root,proc_root,latest)
    for path,record in observed.values():
        if record and stamp(path.lstat())!=record['stamp']:raise ValueError('Artifact changed during process observation')
    if python_before!={name for name in tree_files(app_root/'server') if name.endswith('.py')} or frontend_before!=tree_files(app_root/'client'/'dist'):
        raise ValueError('Deployment inventory changed during observation')
    expected_python={name.removeprefix('server/') for name in manifest['sources'] if name.startswith('server/') and name.endswith('.py')}
    source_match=not python_before-expected_python
    frontend_match=frontend_before==set(manifest['frontend'])
    hashes={'sources':{},'frontend':{}}
    for (group,name),(_,record) in observed.items():
        hashes[group][name]=record['sha256'] if record else None
        matches=record is not None and record['sha256']==manifest[group][name]
        if group=='sources':source_match=source_match and matches
        else:frontend_match=frontend_match and matches
    return dict(version=1,target_revision=manifest['target_revision'],manifest_hash=manifest['checksum'],
        observed_at=datetime.now(timezone.utc).isoformat(),source_files_match=source_match,
        frontend_files_match=frontend_match,unexpected_python_count=len(python_before-expected_python),
        artifact_hashes=hashes,processes=processes,live_authorized=False,runtime_identity_verified=False,
        served_frontend_verified=False,verified_running_revision=None,
        missing_proof=['Reviewed frontend build provenance and actual served bytes',
            'Trusted running backend launch/import identity, dependencies and configuration',
            'Fresh host ownership, baseline, session/recovery and explicit named live start'])
