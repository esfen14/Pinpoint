"""Behavioral tests for the in-container extra listener helper using a temporary run directory."""
from pathlib import Path
import io
import os
import socket
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from defense import extra_listener


def free_port():
    probe=socket.socket();probe.bind(('127.0.0.1',0));port=probe.getsockname()[1];probe.close()
    return port


def connects(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=1) as client:
            client.sendall(b'GET / HTTP/1.0\r\n\r\n')
            return client.recv(100)
    except OSError:
        return None


class ExtraListenerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();extra_listener.RUN_DIR=self.tmp.name
        self.opened=[]
    def tearDown(self):
        for port in self.opened:
            try:extra_listener.close_port(port)
            except SystemExit:pass
        extra_listener.RUN_DIR='/run';self.tmp.cleanup()
    def open(self,service,port):
        extra_listener.open_port(service,port);self.opened.append(port)
    def listed(self):
        out=io.StringIO()
        with redirect_stdout(out):extra_listener.list_ports()
        return out.getvalue().split()
    def test_open_serves_lists_and_close_removes_the_listener(self):
        port=free_port()
        self.open('http',port)
        self.assertIn(b'200 OK',connects(port) or b'')
        self.assertEqual(self.listed(),[str(port)])
        extra_listener.close_port(port)
        self.assertIsNone(connects(port));self.assertEqual(self.listed(),[])
    def test_tcp_listener_accepts_connections(self):
        port=free_port();self.open('tcp',port)
        with socket.create_connection(('127.0.0.1',port),timeout=1):pass
    def test_double_open_and_close_of_unknown_port_are_refused(self):
        port=free_port();self.open('tcp',port)
        with self.assertRaises(SystemExit):extra_listener.open_port('tcp',port)
        with self.assertRaises(SystemExit):extra_listener.close_port(free_port())
    def test_stale_record_with_different_start_ticks_is_never_signalled(self):
        port=free_port()
        Path(extra_listener.pidfile(port)).write_text('%d %d\n'%(os.getpid(),1))
        with self.assertRaises(SystemExit):extra_listener.close_port(port)
        self.assertFalse(Path(extra_listener.pidfile(port)).exists())
    def test_main_accepts_only_the_closed_vocabulary(self):
        for argv in ([],['stop'],['open','ftp','8088'],['open','http','80'],['open','http','8088','x'],['close','abc'],['list','x'],['open','http','8088;id']):
            with self.subTest(argv=argv),self.assertRaises(SystemExit):extra_listener.main(argv)
if __name__=='__main__':unittest.main()
