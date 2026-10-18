"""Cooperative host controller lock; no VM command, authorization or live driver.

All cooperating checkouts serialize host lab mutations through one fixed local
store. An inherited descriptor preserves the same flock across nested controller
calls. This is not protection against another user namespace, malicious same-user
code, direct VBoxManage/demo calls, or an administrator changing the lock store.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import sys

FD_ENV = 'PINPOINT_QA_CONTROL_FD'
PID_ENV = 'PINPOINT_QA_CONTROL_PID'


def canonical_root():
    """Do not let checkout, HOME, TMPDIR or lab configuration split host claims."""
    return Path('/tmp') / f'pinpoint-qa-control-{os.getuid()}'


def checked_file(fd):
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077 or info.st_nlink != 1):
        raise ValueError('Unsafe host controller lock')
    return info.st_dev, info.st_ino


@contextmanager
def claim(*, root=None, inherited_fd=None):
    """Acquire a new claim or verify an already held inherited open description.

    The root argument exists for isolated tests; controller CLI and supervisor
    always use the canonical root. Close without LOCK_UN: duplicated/inherited
    descriptors must never release their ancestor's lock.
    """
    fd = None
    entered = False
    try:
        root = canonical_root() if root is None else Path(root)
        if not root.is_absolute() or root.resolve() != root:
            raise ValueError('Canonical host lock directory required')
        try:
            root.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Private host lock directory required')
        # Anchor the file open to the checked directory, rejecting replacement.
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            actual = os.fstat(directory)
            if (info.st_dev, info.st_ino) != (actual.st_dev, actual.st_ino):
                raise ValueError('Host lock directory changed')
            probe = os.open('controller.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                            0o600, dir_fd=directory)
        finally:
            os.close(directory)
        try:
            identity = checked_file(probe)
            if inherited_fd is None:
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fd, probe = probe, None
            else:
                if type(inherited_fd) is not int or inherited_fd < 3 or checked_file(inherited_fd) != identity:
                    raise ValueError('Invalid inherited controller descriptor')
                # A plain open descriptor is not a parent-held claim.
                try:
                    fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    pass
                else:
                    raise ValueError('Inherited controller descriptor has no held claim')
                fcntl.flock(inherited_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fd = os.dup(inherited_fd)
            entered = True
            yield fd
        finally:
            if probe is not None:
                os.close(probe)
    except (OSError, ValueError):
        if entered:
            raise
        raise ValueError('Host controller unavailable, already owned or unsafe') from None
    finally:
        if fd is not None:
            os.close(fd)


def main():
    """Wrap only the repository controller, or verify its inherited descriptor."""
    try:
        value = os.environ.get(FD_ENV)
        inherited = int(value) if value is not None else None
        if sys.argv[1:] == ['--check']:
            if inherited is None or os.environ.get(PID_ENV) != str(os.getppid()):
                raise ValueError('Controller wrapper required')
            with claim(inherited_fd=inherited):
                return 0
        script = Path(__file__).resolve().with_name('vmlab')
        if len(sys.argv) < 2 or Path(sys.argv[1]).resolve() != script:
            raise ValueError('Repository VM controller required')
        with claim(inherited_fd=inherited) as fd:
            os.set_inheritable(fd, True)
            if inherited is not None and inherited != fd:
                os.close(inherited)
            environment = dict(os.environ, **{FD_ENV: str(fd), PID_ENV: str(os.getpid())})
            os.execve('/bin/bash', ['bash', str(script), *sys.argv[2:]], environment)
    except (OSError, ValueError):
        print('vmlab: host control claim failed; another owner or invalid lock metadata.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
