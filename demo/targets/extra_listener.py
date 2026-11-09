"""Fixed helper run inside an owned demo container to open, close or list extra ports.

It takes only an action and a port, binds TCP on all addresses, and records the
process in a pidfile with its start ticks so a later close cannot signal an
unrelated process. Callers validate the target, service and port first.
"""
import os
import re
import signal
import socket
import sys
import time

RUN_DIR='/run'
PREFIX='pinpoint-extra-'
BODY=b'HTTP/1.0 200 OK\r\nContent-Length: 6\r\nContent-Type: text/plain\r\n\r\nextra\n'


def pidfile(port):
    return os.path.join(RUN_DIR,PREFIX+str(port)+'.pid')


def start_ticks(pid):
    with open('/proc/%d/stat'%pid) as stream:
        return int(stream.read().rsplit(')',1)[1].split()[19])


def alive(pid):
    """A zombie has stopped listening even if its parent has not reaped it."""
    try:
        with open('/proc/%d/stat'%pid) as stream:
            return stream.read().rsplit(')',1)[1].split()[0]!='Z'
    except (OSError,IndexError):
        return False


def recorded(port):
    """Return the live recorded pid for the port, removing a stale record."""
    path=pidfile(port)
    try:
        with open(path) as stream:
            pid,ticks=[int(value) for value in stream.read().split()]
    except FileNotFoundError:
        return None
    try:
        if start_ticks(pid)==ticks and alive(pid):
            return pid
    except (OSError,IndexError,ValueError):
        pass
    os.unlink(path)
    return None


def serve(service,port):
    server=socket.socket()
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind(('0.0.0.0',port))
    server.listen(8)
    return server


def loop(server,service):
    while True:
        client,_=server.accept()
        client.settimeout(1)
        try:
            if service=='http':
                client.recv(1024)
                client.sendall(BODY)
        except OSError:
            pass
        finally:
            client.close()


def open_port(service,port):
    if recorded(port) is not None:
        raise SystemExit('already open')
    server=serve(service,port)
    if os.fork():
        server.close()
        deadline=time.monotonic()+5
        while recorded(port) is None:
            if time.monotonic()>deadline:
                raise SystemExit('listener did not start')
            time.sleep(0.05)
        return
    os.setsid()
    path=pidfile(port)
    with open(path,'w') as stream:
        stream.write('%d %d\n'%(os.getpid(),start_ticks(os.getpid())))
    for descriptor in (0,1,2):
        os.close(descriptor)
    os.open(os.devnull,os.O_RDWR)
    os.dup2(0,1)
    os.dup2(0,2)
    signal.signal(signal.SIGTERM,lambda *_:os._exit(0))
    loop(server,service)


def close_port(port):
    pid=recorded(port)
    if pid is None:
        raise SystemExit('not open')
    os.kill(pid,signal.SIGTERM)
    deadline=time.monotonic()+5
    while alive(pid):
        if time.monotonic()>deadline:
            raise SystemExit('listener did not stop')
        time.sleep(0.05)
    try:
        os.unlink(pidfile(port))
    except FileNotFoundError:
        pass


def list_ports():
    for name in sorted(os.listdir(RUN_DIR)):
        match=re.fullmatch(re.escape(PREFIX)+r'(\d{1,5})\.pid',name)
        if match and recorded(int(match[1])) is not None:
            print(int(match[1]))


def main(argv):
    action=argv[0] if argv else ''
    if action=='list' and len(argv)==1:
        list_ports()
    elif action=='open' and len(argv)==3 and argv[1] in {'http','tcp'} and re.fullmatch(r'\d{4,5}',argv[2]):
        open_port(argv[1],int(argv[2]))
    elif action=='close' and len(argv)==2 and re.fullmatch(r'\d{4,5}',argv[1]):
        close_port(int(argv[1]))
    else:
        raise SystemExit('invalid request')


if __name__=='__main__':
    main(sys.argv[1:])
