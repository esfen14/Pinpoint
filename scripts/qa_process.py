#!/usr/bin/env python3
"""Bound trusted local commands by time/output and terminate their POSIX group.

No CLI, default command, shell expansion, credentials or live lab integration.
Container-daemon cleanup and children that deliberately leave the process group
require a production driver/cgroup boundary; this helper does not prove those.
"""
from __future__ import annotations
import importlib.util
import math
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import time

spec=importlib.util.spec_from_file_location('transport',Path(__file__).with_name('qa_transport.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class ProcessFailure(ValueError):
    """Sanitized infrastructure failure; raw stdout/stderr remain private."""


class GroupRunner:
    """Run one allowlisted executable at a time, retaining bounded private output."""
    def __init__(self,output_dir:Path,allowed_executables:set[str],grace_seconds:float=1):
        """Require private output and an explicit trusted absolute executable set."""
        self.root=t.private_directory(output_dir)
        if not allowed_executables or any(not Path(p).is_absolute() or str(Path(p).resolve())!=p or not Path(p).is_file() for p in allowed_executables):
            raise ValueError('Explicit canonical executable allowlist required')
        if not isinstance(grace_seconds,(int,float)) or not math.isfinite(grace_seconds) or not 0<grace_seconds<=5:
            raise ValueError('Bounded cancellation grace required')
        self.allowed=allowed_executables;self.grace=grace_seconds;self.process=None;self.group=None;self.halted=False;self.group_finished=True

    def members(self) -> list[int]:
        """Return executable Linux group members, excluding dead zombies.

        The direct child is reaped separately. An adopted zombie cannot execute;
        it may await its own parent/init reaper. This is not a cgroup enumerator.
        """
        if self.group is None:return []
        result=[]
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():continue
            try:
                value=(entry/'stat').read_text();fields=value[value.rfind(')')+2:].split()
                if int(fields[2])==self.group and fields[0] not in ('Z','X'):result.append(int(entry.name))
            except FileNotFoundError:continue
            except (PermissionError,ValueError,IndexError):raise ProcessFailure('process identity unavailable') from None
        return result

    def idle(self) -> bool:
        """Require the direct child reaped and no executable group descendants."""
        return not self.halted and (self.process is None or self.group_finished) and not self.members()

    def exited(self) -> bool:
        """Observe direct-child exit without reaping/releasing its group-leader PID."""
        if self.process is None or self.group_finished:return True
        try:return os.waitid(os.P_PID,self.process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is not None
        except ChildProcessError:raise ProcessFailure('owned process identity unavailable') from None

    def cancel(self) -> None:
        """Terminate/escalate the whole owned group and reap its direct child."""
        if self.group is None or self.group_finished:return
        self.exited()  # Establish the still-owned child before any group signal.
        for sig,grace in ((signal.SIGTERM,self.grace),(signal.SIGKILL,1)):
            try:os.killpg(self.group,sig)
            except ProcessLookupError:pass
            until=time.monotonic()+grace
            while time.monotonic()<until:
                if not self.members():break
                time.sleep(0.01)
            if not self.members():break
        if self.process is not None:
            try:self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:raise ProcessFailure('process termination unresolved') from None
        if self.members():raise ProcessFailure('process group cleanup unresolved')
        self.group_finished=True

    def run(self,argv:list[str],environment:dict,timeout:float,label:str,max_output_bytes:int=8*1024*1024) -> dict:
        """Execute without a shell; preserve logs and sanitize all raised failures.

        Caller must consume its durable action slot before calling this function.
        Arguments/environment are trusted-driver input, never agent/user-shell
        strings. This allowlist does not determine allowed arguments or targets.
        """
        if (not isinstance(argv,list) or not argv or argv[0] not in self.allowed
            or any(not isinstance(v,str) or not v or '\x00' in v for v in argv)
            or not isinstance(environment,dict) or set(environment)-{'PATH','HOME','LANG','LC_ALL'}
            or any(not isinstance(v,str) or '\x00' in v for v in environment.values())
            or not isinstance(timeout,(int,float)) or isinstance(timeout,bool) or not math.isfinite(timeout) or not 0<timeout<=21600
            or not isinstance(label,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',label)
            or type(max_output_bytes) is not int or not 1<=max_output_bytes<=64*1024*1024):
            raise ValueError('Invalid bounded process request')
        if not self.idle():raise ValueError('Previous process group not cleaned')
        t.private_directory(self.root)
        paths=[self.root/f'{label}.{name}' for name in ('stdout','stderr')]
        outputs=[];selector=selectors.DefaultSelector();failure=None;count=0;deadline=time.monotonic()+timeout
        try:
            for path in paths:
                try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
                except OSError:raise ValueError('Private process log exists or is unsafe') from None
                outputs.append(os.fdopen(fd,'wb'))
            self.process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                cwd=self.root,env=environment,start_new_session=True,close_fds=True,umask=0o077)
            self.group=self.process.pid;self.group_finished=False
            for stream,output in zip((self.process.stdout,self.process.stderr),outputs):
                os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,output)
            while selector.get_map() or not self.exited():
                if time.monotonic()>=deadline:raise ProcessFailure('process timeout')
                # A successful parent must not leave children running independently.
                if self.exited() and self.members():self.cancel()
                for key,_ in selector.select(timeout=min(0.02,max(0,deadline-time.monotonic()))):
                    chunk=os.read(key.fileobj.fileno(),65536)
                    if not chunk:selector.unregister(key.fileobj);continue
                    permitted=min(len(chunk),max_output_bytes-count)
                    key.data.write(chunk[:permitted]);count+=permitted
                    if permitted<len(chunk):raise ProcessFailure('process output limit exceeded')
            self.cancel()
            status=self.process.returncode
        except BaseException as error:
            failure=error if isinstance(error,(ValueError,ProcessFailure)) else ProcessFailure('process invocation interrupted or unavailable')
        finally:
            try:self.cancel()
            except BaseException:
                self.halted=True;failure=ProcessFailure('process group cleanup unresolved')
            selector.close()
            if self.process is not None:
                for stream in (self.process.stdout,self.process.stderr):
                    if stream is not None:stream.close()
            if not self.halted:self.process=None;self.group=None
            for output in outputs:
                try:output.flush();os.fsync(output.fileno())
                except OSError:
                    self.halted=True;failure=ProcessFailure('private output persistence unresolved')
                finally:
                    try:output.close()
                    except OSError:
                        self.halted=True;failure=ProcessFailure('private output persistence unresolved')
            try:
                directory=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(directory)
                finally:os.close(directory)
            except OSError:
                self.halted=True;failure=ProcessFailure('private output persistence unresolved')
        if failure is not None:raise failure from None
        return dict(returncode=status,stdout=str(paths[0]),stderr=str(paths[1]),group_clean=True,output_bytes=count)
