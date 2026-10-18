"""Owned bridge contracts use local Unix socket pairs, never TCP or an appliance."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

b=module('bridge','qa_bridge.py')
s=module('supervisor','qa_supervisor.py')
f=module('fixtures','test_qa_transport.py')
UUID='12345678-1234-1234-1234-123456789abc'


class BridgeTests(unittest.TestCase):
    def fixture(self,root,**kwargs):
        q,j=f.TransportTests().fixture(root)
        plan=b.t.prepare(q,j,root/'state',root/'bridge')
        plan.update(remaining_seconds=60,step_timeout_seconds=10)
        plan['bridge_limits']=dict(max_bytes=kwargs.get('max_bytes',32*1024*1024),max_connections=kwargs.get('max_connections',16))
        (root/'ledger').mkdir(mode=0o700);ledger=s.Ledger(root/'ledger')
        bridge=b.Bridge(root/'bridge',**kwargs)
        self.addCleanup(bridge.stop)
        return plan,ledger,bridge

    def client(self,bridge):
        client=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);client.settimeout(2)
        self.addCleanup(client.close);client.connect(str(bridge.path));return client

    def wait_for(self,condition):
        until=time.monotonic()+2
        while not condition() and time.monotonic()<until:time.sleep(.01)
        self.assertTrue(condition())

    def test_duplex_half_close_and_private_durable_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);plan,ledger,bridge=self.fixture(root)
            upstream,server=socket.socketpair();server.settimeout(2)
            self.addCleanup(server.close)
            with ledger.claim(UUID),patch.object(b,'connect_origin',return_value=upstream):
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10)
                self.assertEqual(bridge.path.stat().st_mode & 0o777,0o600)
                client=self.client(bridge);client.sendall(b'private-fixture-request');client.shutdown(socket.SHUT_WR)
                self.assertEqual(server.recv(1024),b'private-fixture-request')
                self.assertEqual(server.recv(1),b'')
                server.sendall(b'fixture-response');server.shutdown(socket.SHUT_WR)
                self.assertEqual(client.recv(1024),b'fixture-response')
                self.assertTrue(bridge.verify(plan,ledger,UUID))
                self.assertTrue(bridge.stop())
                self.assertFalse(bridge.path.exists())
            self.assertFalse(bridge.thread.is_alive())
            text=bridge.intent.read_text();self.assertNotIn('private-fixture-request',text)
            self.assertEqual(json.loads(text)['status'],'complete')
            with self.assertRaises(ValueError):b.Bridge(root/'bridge')

    def test_no_start_without_consumed_scope_and_live_host_claim(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with patch.object(b,'connect_origin') as connector:
                with self.assertRaises(ValueError):bridge.start(plan,ledger,UUID,10)
                with ledger.claim(UUID):
                    with self.assertRaises(ValueError):bridge.start(plan,ledger,UUID,10)
                connector.assert_not_called()
            self.assertFalse(bridge.path.exists())

    def test_origin_scope_and_budget_cannot_be_changed(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID):
                ledger.consume(UUID,plan)
                with self.assertRaises(ValueError):bridge.start(plan,ledger,UUID,61)
                changed=dict(plan,bridge_origin='http://example.invalid')
                with self.assertRaises(ValueError):bridge.start(changed,ledger,UUID,10)
                changed=dict(plan,case='TC-LOG-05')
                with self.assertRaises(ValueError):bridge.start(changed,ledger,UUID,10)

    def test_deadline_halts_and_closes_socket_without_upstream_access(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID),patch.object(b,'connect_origin') as connector:
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10)
                bridge.deadline=time.monotonic()+.08
                self.wait_for(lambda:bridge.failed)
                self.assertFalse(bridge.stop());connector.assert_not_called()
            self.assertEqual(json.loads(bridge.intent.read_text())['status'],'halted')

    def test_connection_failure_is_sanitized_and_halts(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID),patch.object(b,'connect_origin',side_effect=OSError('private-fixture-error')):
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10);self.client(bridge)
                self.wait_for(lambda:bridge.failed);self.assertFalse(bridge.stop())
            self.assertNotIn('private-fixture-error',bridge.intent.read_text())

    def test_byte_and_connection_budgets_halt(self):
        for fault in ('bytes','connections'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                plan,ledger,bridge=self.fixture(Path(d),max_bytes=16,max_connections=1)
                upstream,server=socket.socketpair();self.addCleanup(server.close)
                with ledger.claim(UUID),patch.object(b,'connect_origin',return_value=upstream):
                    ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10)
                    first=self.client(bridge)
                    if fault=='bytes':first.sendall(b'x'*32)
                    else:
                        self.wait_for(lambda:bridge.active_count==1);self.client(bridge)
                    self.wait_for(lambda:bridge.failed);self.assertFalse(bridge.stop())

    def test_socket_replacement_is_not_unlinked_or_certified(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID):
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10)
                bridge.path.unlink();bridge.path.write_text('replacement')
                self.assertFalse(bridge.verify(plan,ledger,UUID));self.assertFalse(bridge.stop())
                self.assertEqual(bridge.path.read_text(),'replacement')

    def test_lost_claim_stops_relay_and_retained_fd_is_released(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID):
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10)
                ledger.held.remove(UUID)
                self.wait_for(lambda:bridge.failed);self.assertFalse(bridge.stop())
            with b.control.claim():pass

    def test_initial_checkpoint_failure_never_binds_or_connects(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID),patch.object(bridge,'persist',side_effect=OSError('private')),patch.object(b,'connect_origin') as connector:
                ledger.consume(UUID,plan)
                with self.assertRaises(ValueError):bridge.start(plan,ledger,UUID,10)
                connector.assert_not_called();self.assertFalse(bridge.path.exists())

    def test_foreign_peer_is_rejected_without_upstream_connection(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d))
            with ledger.claim(UUID),patch.object(b,'peer_uid',return_value=os.getuid()+1),patch.object(b,'connect_origin') as connector:
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10);self.client(bridge)
                self.wait_for(lambda:bridge.failed);self.assertFalse(bridge.stop())
                connector.assert_not_called()

    def test_large_bidirectional_transfer_drains_bounded_buffers(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,bridge=self.fixture(Path(d));payload=b'fixture-data'*32768
            upstream,server=socket.socketpair();server.settimeout(3);self.addCleanup(server.close)
            received=[];errors=[]
            def reply():
                try:
                    while chunk:=server.recv(65536):received.append(chunk)
                    server.sendall(b''.join(received));server.shutdown(socket.SHUT_WR)
                except BaseException as error:errors.append(type(error).__name__)
            worker=threading.Thread(target=reply,daemon=True);worker.start()
            with ledger.claim(UUID),patch.object(b,'connect_origin',return_value=upstream):
                ledger.consume(UUID,plan);bridge.start(plan,ledger,UUID,10)
                client=self.client(bridge);client.sendall(payload);client.shutdown(socket.SHUT_WR)
                returned=[]
                while chunk:=client.recv(65536):returned.append(chunk)
                worker.join(2);self.assertFalse(worker.is_alive());self.assertFalse(errors)
                self.assertEqual(b''.join(returned),payload)
                self.assertEqual(bridge.bytes_moved,len(payload)*2)
                self.assertTrue(bridge.stop())


if __name__=='__main__':unittest.main()
