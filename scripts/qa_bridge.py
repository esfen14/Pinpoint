"""Owned, bounded Unix bridge to the single appliance loopback origin; no CLI.

Only a future trusted driver may start this after its actual live proofs and
explicit start. A consumed slot/host claim does not establish those proofs.
Tests replace connect_origin with local Unix socket pairs, never appliance TCP.
"""
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import selectors
import socket
import stat
import struct
import threading
import time


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

t=module('transport','qa_transport.py')
control=module('control','qa_control.py')
ORIGIN='http://127.0.0.1:18080'
BUFFER=65536


def connect_origin(timeout):
    """The only production upstream; no URL/environment/redirect target input."""
    return socket.create_connection(('127.0.0.1',18080),timeout=timeout)


def peer_uid(client):
    return struct.unpack('3i',client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))[1]


class Bridge:
    """One consumed case's relay, with owned socket/lock custody and no retries."""
    def __init__(self,root:Path,*,max_bytes=32*1024*1024,max_connections=16):
        self.root=t.private_directory(root,empty=True)
        if (type(max_bytes) is not int or not 1<=max_bytes<=64*1024*1024
            or type(max_connections) is not int or not 1<=max_connections<=32):
            raise ValueError('Bounded bridge limits required')
        self.path=self.root/'web.sock';self.intent=self.root/'bridge-intent.json'
        self.pending=self.root/'bridge-intent.pending';self.max_bytes=max_bytes;self.max_connections=max_connections
        self.thread=None;self.listener=None;self.control_fd=None;self.socket_identity=None
        self.failed=False;self.started=False;self.stopped=False;self.bytes_moved=0;self.disconnects=0
        self.pairs={};self.stop_event=threading.Event();self.ready=threading.Event()

    @property
    def active_count(self):return len(self.pairs)

    def persist(self,status):
        """Store only scope/resource metadata and counters, never traffic or errors."""
        t.private_directory(self.root)
        value=dict(version=1,status=status,origin=ORIGIN,lab_uuid=self.uuid,transport_hash=self.scope_hash,
            queue_hash=self.plan['queue_hash'],case=self.plan['case'],bytes_moved=self.bytes_moved,
            disconnects=self.disconnects,max_bytes=self.max_bytes,max_connections=self.max_connections)
        fd=os.open(self.pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as output:
            json.dump(value,output);output.flush();os.fsync(output.fileno())
        os.replace(self.pending,self.intent)
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)

    def scope_valid(self):
        """Require the original consumed slot and claim throughout the relay."""
        if self.uuid not in self.ledger.held:return False
        with control.claim(inherited_fd=self.control_fd):pass
        state=self.ledger.snapshot(self.uuid)
        return (not state['halted'] and bool(state['attempts'])
            and state['attempts'][-1].get('status')=='running'
            and state['attempts'][-1].get('transport_hash')==self.scope_hash)

    def socket_owned(self):
        try:
            t.private_directory(self.root)
            info=self.path.lstat()
            return (stat.S_ISSOCK(info.st_mode) and info.st_uid==os.getuid() and not info.st_mode & 0o077
                and (info.st_dev,info.st_ino)==self.socket_identity)
        except (OSError,ValueError):return False

    def start(self,plan,ledger,uuid,timeout):
        """Bind only after a durable consumed action; retain the kernel host lock."""
        if self.started or self.stopped:raise ValueError('Bridge already used; no implicit retry')
        if (type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0
            or timeout>plan.get('remaining_seconds',0) or timeout>21600
            or plan.get('bridge_limits')!=dict(max_bytes=self.max_bytes,max_connections=self.max_connections)
            or plan.get('bridge_origin')!=ORIGIN or plan.get('bridge_socket')!=str(self.path)
            or uuid not in ledger.held or getattr(ledger,'control_fd',None) is None):
            raise ValueError('Bounded scope and held host/UUID claim required')
        self.plan=json.loads(json.dumps(plan));self.scope_hash=t.x.queue.cat.digest(self.plan)
        self.uuid=uuid;self.ledger=ledger
        state=ledger.snapshot(uuid)
        if (state['halted'] or not state['attempts'] or state['attempts'][-1].get('status')!='running'
            or state['attempts'][-1].get('transport_hash')!=self.scope_hash):
            raise ValueError('Matching durable consumed transport required')
        elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(state['attempts'][-1]['started_at'])).total_seconds()
        if not 0<=elapsed<plan['remaining_seconds']:raise ValueError('Consumed case budget expired')
        self.deadline=time.monotonic()+min(timeout,plan['remaining_seconds']-elapsed)
        t.private_directory(self.root,empty=True)
        with control.claim(inherited_fd=ledger.control_fd):pass
        self.control_fd=os.dup(ledger.control_fd);self.started=True
        try:
            self.persist('binding')
            self.listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            self.listener.bind(str(self.path))
            info=self.path.lstat();self.socket_identity=(info.st_dev,info.st_ino)
            self.path.chmod(0o600)
            self.listener.listen(self.max_connections);self.listener.setblocking(False)
            self.persist('running')
            self.thread=threading.Thread(target=self.loop,name='pinpoint-qa-bridge',daemon=True)
            self.thread.start()
            if not self.ready.wait(min(1,max(0,self.deadline-time.monotonic()))) or self.failed:
                raise ValueError('Bridge start unresolved')
        except BaseException:
            self.failed=True;self.stop()
            raise ValueError('Bridge start failed; verified recovery required') from None

    def verify(self,plan,ledger,uuid):
        """Check custody/liveness, never application version or baseline readiness."""
        try:
            valid=(self.started and not self.stopped and not self.failed and self.thread.is_alive()
                and ledger is self.ledger and uuid==self.uuid and self.scope_hash==t.x.queue.cat.digest(plan)
                and time.monotonic()<self.deadline and self.scope_valid() and self.socket_owned())
            if not valid and self.started and not self.stopped:self.failed=True;self.stop_event.set()
            return bool(valid)
        except (OSError,ValueError,KeyError,TypeError,AttributeError):
            self.failed=True;self.stop_event.set();return False

    def drop(self,key,selector):
        pair=self.pairs.pop(key,None)
        if pair is None:return
        for endpoint in pair['sockets']:
            try:selector.unregister(endpoint)
            except KeyError:pass
            endpoint.close()

    def refresh(self,key,selector):
        pair=self.pairs[key]
        for side,endpoint in enumerate(pair['sockets']):
            if pair['eof'][1-side] and not pair['pending'][side] and not pair['write_closed'][side]:
                endpoint.shutdown(socket.SHUT_WR);pair['write_closed'][side]=True
            events=0
            if not pair['eof'][side] and len(pair['pending'][1-side])<BUFFER:events|=selectors.EVENT_READ
            if pair['pending'][side]:events|=selectors.EVENT_WRITE
            try:selector.get_key(endpoint);registered=True
            except KeyError:registered=False
            if events:
                if registered:selector.modify(endpoint,events,(key,side))
                else:selector.register(endpoint,events,(key,side))
            elif registered:selector.unregister(endpoint)
        if all(pair['eof']) and not any(pair['pending']):self.drop(key,selector)

    def accept(self,selector):
        try:client,_=self.listener.accept()
        except BlockingIOError:return
        upstream=None
        try:
            uid=peer_uid(client)
            if uid!=os.getuid() or len(self.pairs)>=self.max_connections or not self.scope_valid():
                raise ValueError('Peer, connection budget or claim invalid')
            upstream=connect_origin(max(.001,min(1,self.deadline-time.monotonic())))
            client.setblocking(False);upstream.setblocking(False);key=client.fileno()
            self.pairs[key]=dict(sockets=(client,upstream),eof=[False,False],write_closed=[False,False],pending=[bytearray(),bytearray()])
            self.refresh(key,selector)
        except BaseException:
            client.close()
            if upstream is not None:upstream.close()
            raise

    def relay(self,key,side,events,selector):
        if key not in self.pairs:return
        pair=self.pairs[key];endpoint=pair['sockets'][side]
        try:
            if events & selectors.EVENT_READ:
                try:data=endpoint.recv(min(BUFFER-len(pair['pending'][1-side]),self.max_bytes-self.bytes_moved+1))
                except BlockingIOError:data=None
                if data:
                    self.bytes_moved+=len(data)
                    if self.bytes_moved>self.max_bytes:raise ValueError('Bridge byte budget exhausted')
                    pair['pending'][1-side].extend(data)
                elif data==b'':pair['eof'][side]=True
            if events & selectors.EVENT_WRITE and pair['pending'][side]:
                try:count=endpoint.send(pair['pending'][side]);del pair['pending'][side][:count]
                except BlockingIOError:pass
            self.refresh(key,selector)
        except OSError:
            self.disconnects+=1;self.drop(key,selector)

    def resources_close(self):
        try:
            if self.listener is not None:self.listener.close()
            if self.socket_identity is not None:
                if self.socket_owned():self.path.unlink()
                else:self.failed=True
        except BaseException:self.failed=True
        try:self.persist('halted' if self.failed else 'complete')
        except BaseException:self.failed=True
        if self.control_fd is not None:
            try:os.close(self.control_fd);self.control_fd=None
            except OSError:self.failed=True

    def loop(self):
        selector=selectors.DefaultSelector()
        try:
            selector.register(self.listener,selectors.EVENT_READ,None);self.ready.set()
            while not self.stop_event.is_set():
                if time.monotonic()>=self.deadline or not self.scope_valid() or not self.socket_owned():
                    raise ValueError('Bridge deadline, claim or socket identity lost')
                for key,events in selector.select(.02):
                    if self.stop_event.is_set():break
                    if time.monotonic()>=self.deadline:raise ValueError('Bridge deadline expired')
                    if key.data is None:self.accept(selector)
                    else:self.relay(*key.data,events,selector)
        except BaseException:self.failed=True;self.stop_event.set();self.ready.set()
        finally:
            for key in list(self.pairs):self.drop(key,selector)
            selector.close();self.resources_close()

    def stop(self):
        """Join the owned relay, close every connection and remove only its socket."""
        if self.stopped:return not self.failed
        if not self.started:return not self.failed
        if time.monotonic()>=self.deadline:self.failed=True
        self.stop_event.set()
        if self.thread is not None and self.thread.ident is not None:
            self.thread.join(2)
            if self.thread.is_alive():self.failed=True;return False
        else:self.resources_close()
        self.stopped=True
        return not self.failed and not self.pairs and self.control_fd is None
