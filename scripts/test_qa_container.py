"""Synthetic Docker responses only; no daemon, container, bridge or lab access."""
import copy
import importlib.util
import json
import os
import socket
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

c=module('container','qa_container.py')
s=module('supervisor','qa_supervisor.py')
f=module('fixture','test_qa_transport.py')
UUID='12345678-1234-1234-1234-123456789abc'
CID='c'*64
IMAGE='sha256:'+'d'*64


class Commands:
    def __init__(self,root):
        self.root=root;self.calls=[];self.resource=None;self.fail=None;self.absence_error=False
        self.attached=False;self.wrong_owner=False
        self.tamper=None
    def idle(self):return True
    def run(self,argv,environment,timeout,label,max_output_bytes=0):
        assert 0<timeout<=60
        assert set(environment)<= {'HOME','PATH','LANG','LC_ALL'}
        self.calls.append(argv[1:]);args=argv[1:];text='';status=0
        if args[0]=='create':
            assert json.loads((self.root/'container-intent.json').read_text())['status']=='creating'
            name=args[args.index('--name')+1]
            token=args[args.index('--label')+1].split('=',1)[1]
            mounts=[]
            for i,v in enumerate(args):
                if v=='--mount':
                    data=dict(x.split('=',1) for x in args[i+1].split(',') if '=' in x)
                    mounts.append(dict(Source=data['src'],Destination=data['dst'],RW='readonly' not in args[i+1]))
            self.resource=dict(Id=CID,Name='/'+name,Image=IMAGE,
                Config=dict(Labels={c.LABEL:token},Entrypoint=['bash'],Cmd=args[args.index(IMAGE)+1:],User=f'{os.getuid()}:{os.getgid()}'),
                HostConfig=dict(NetworkMode='none',ReadonlyRootfs=True,Privileged=False,CapDrop=['ALL'],
                    SecurityOpt=['no-new-privileges'],AutoRemove=False,RestartPolicy=dict(Name='no')),
                Mounts=mounts,State=dict(Running=False,ExitCode=0,Status='created'))
            cid=Path(args[args.index('--cidfile')+1]);cid.write_text(CID);cid.chmod(0o600)
            text=CID+'\n'
            if self.fail=='create':raise ValueError('synthetic-private-error')
        elif args[:2]==['container','inspect']:
            value=copy.deepcopy(self.resource)
            if self.wrong_owner:value['Config']['Labels'][c.LABEL]='other'
            if self.tamper=='network':value['HostConfig']['NetworkMode']='host'
            if self.tamper=='mount':value['Mounts'][0]['RW']=True
            if self.tamper=='command':value['Config']['Cmd'].append('--retries=1')
            text=json.dumps([value])
        elif args[:2]==['start','--attach']:
            self.attached=True
            if self.fail=='start':
                self.resource['State']['Running']=True
                self.resource['State']['Status']='running'
                raise ValueError('synthetic-private-error')
            self.resource['State']['ExitCode']=1 if self.fail=='test' else 0
            self.resource['State']['Status']='exited'
            if self.fail=='test':status=1
        elif args[:2]==['container','kill']:
            self.resource['State']['Running']=False
            self.resource['State']['Status']='exited'
        elif args[:2]==['container','rm']:
            self.resource=None
        elif args[:2]==['container','ls']:
            if self.absence_error:status=1
            text=CID+'\n' if self.resource else ''
        else:raise AssertionError(args)
        stdout=self.root/f'{label}.stdout';stderr=self.root/f'{label}.stderr'
        for path,value in ((stdout,text),(stderr,'')):
            path.write_text(value);path.chmod(0o600)
        return dict(returncode=status,stdout=str(stdout),stderr=str(stderr),group_clean=True)


class ContainerTests(unittest.TestCase):
    def fixture(self,root):
        q,j=f.TransportTests().fixture(root)
        q['sets'][0]['cases'][0]['execution']['container_image_id']=IMAGE
        c.t.x.queue.seal(q);j['queue_hash']=q['scope_hash']
        j.pop('journal_hash');j['journal_hash']=c.t.x.queue.cat.digest(j)
        plan=c.t.prepare(q,j,root/'state',root/'bridge')
        plan.update(remaining_seconds=60,step_timeout_seconds=10)
        bridge=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.addCleanup(bridge.close)
        bridge.bind(str(root/'bridge'/'web.sock'));(root/'bridge'/'web.sock').chmod(0o600)
        (root/'ledger').mkdir(mode=0o700);ledger=s.Ledger(root/'ledger')
        (root/'control').mkdir(mode=0o700);commands=Commands(root/'control')
        class Cleanup:
            def __init__(self):self.root=commands.root
            def run(self,*a,**kw):return commands.run(*a,**kw)
            def idle(self):return commands.idle()
        runtime=c.ContainerRuntime(root/'control',str(Path('/bin/true').resolve()),commands,Cleanup())
        return plan,ledger,commands,runtime

    def run_case(self,root,change=None):
        plan,ledger,commands,runtime=self.fixture(root)
        if change:change(plan,ledger,commands,runtime)
        with ledger.claim(UUID):
            ledger.consume(UUID,plan)
            return runtime.execute(plan,ledger,UUID,IMAGE,60,10),commands,runtime

    def test_pinned_create_attach_remove_and_durable_intent(self):
        with tempfile.TemporaryDirectory() as d:
            result,commands,runtime=self.run_case(Path(d))
            self.assertTrue(result['container_clean'])
            self.assertEqual(result['exit_code'],0)
            create=commands.calls[0]
            self.assertEqual(create[0],'create')
            self.assertNotIn('--rm',create)
            self.assertIn('--entrypoint',create)
            self.assertIn(IMAGE,create)
            self.assertTrue(commands.attached)
            self.assertIsNone(commands.resource)
            intent=json.loads(runtime.intent.read_text())
            self.assertEqual(intent['status'],'complete')
            self.assertEqual(intent['container_id'],CID)
            self.assertNotIn('synthetic-private-error',runtime.intent.read_text())

    def test_no_dispatch_without_real_lock_and_consumed_slot(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d))
            with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            with ledger.claim(UUID):
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            self.assertFalse(commands.calls)

    def test_modified_transport_and_mutable_image_are_rejected(self):
        for bad in ('image','argv','pin'):
            with self.subTest(bad=bad),tempfile.TemporaryDirectory() as d:
                plan,ledger,commands,runtime=self.fixture(Path(d))
                if bad=='argv':plan['docker_argv'].insert(2,'--privileged')
                with ledger.claim(UUID):
                    ledger.consume(UUID,plan)
                    with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,
                        'tag:latest' if bad=='image' else ('sha256:'+'e'*64 if bad=='pin' else IMAGE),60,10)
                self.assertFalse(commands.calls)

    def test_timeout_kills_owned_container_and_never_retries(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);plan,ledger,commands,runtime=self.fixture(root);commands.fail='start'
            with ledger.claim(UUID):
                ledger.consume(UUID,plan)
                with self.assertRaisesRegex(ValueError,'halted'):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
                self.assertIsNone(commands.resource)
                self.assertTrue(any(a[:2]==['container','kill'] for a in commands.calls))
                count=len(commands.calls)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
                self.assertEqual(len(commands.calls),count)
            self.assertEqual(json.loads(runtime.intent.read_text())['status'],'halted')

    def test_uncertain_create_is_found_by_owned_name_and_stays_halted(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d));commands.fail='create'
            with ledger.claim(UUID):
                ledger.consume(UUID,plan)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            self.assertIsNone(commands.resource)
            self.assertFalse(commands.attached)
            self.assertTrue(runtime.halted)

    def test_foreign_owner_is_never_started_killed_or_removed(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d));commands.wrong_owner=True
            with ledger.claim(UUID):
                ledger.consume(UUID,plan)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            self.assertFalse(commands.attached)
            self.assertFalse(any(a[:2] in (['container','kill'],['container','rm']) for a in commands.calls))
            self.assertTrue(runtime.halted)

    def test_daemon_error_is_not_absence_and_intent_survives_restart(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d));commands.absence_error=True
            with ledger.claim(UUID):
                ledger.consume(UUID,plan)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            self.assertTrue(runtime.halted)
            with self.assertRaises(ValueError):c.ContainerRuntime(runtime.root,runtime.docker,commands,commands)

    def test_nonzero_container_exit_is_not_a_product_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            result,_,_=self.run_case(Path(d),lambda p,l,c,r:setattr(c,'fail','test'))
            self.assertEqual(result['exit_code'],1)
            self.assertTrue(result['container_clean'])
            self.assertNotIn('result',result)

    def test_initial_persistence_failure_never_contacts_daemon(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d))
            with ledger.claim(UUID),patch.object(runtime,'persist',side_effect=OSError('synthetic-private-error')):
                ledger.consume(UUID,plan)
                with self.assertRaisesRegex(ValueError,'halted'):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            self.assertFalse(commands.calls)

    def test_missing_bridge_or_reused_evidence_rejects_before_dispatch(self):
        for fault in ('bridge','evidence'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                root=Path(d);plan,ledger,commands,runtime=self.fixture(root)
                if fault=='bridge':(root/'bridge'/'web.sock').unlink()
                else:(root/'evidence'/'artifacts').mkdir(mode=0o700)
                with ledger.claim(UUID):
                    ledger.consume(UUID,plan)
                    with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
                self.assertFalse(commands.calls)

    def test_consumed_transport_cannot_be_replaced_or_extended(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d))
            with ledger.claim(UUID):
                ledger.consume(UUID,plan)
                changed=copy.deepcopy(plan);changed['approved_image_id']='sha256:'+'e'*64
                with self.assertRaises(ValueError):runtime.execute(changed,ledger,UUID,changed['approved_image_id'],60,10)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,61,10)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,11)
            self.assertFalse(commands.calls)

    def test_changed_actual_network_mount_or_command_never_starts(self):
        for fault in ('network','mount','command'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                plan,ledger,commands,runtime=self.fixture(Path(d));commands.tamper=fault
                with ledger.claim(UUID):
                    ledger.consume(UUID,plan)
                    with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
                self.assertFalse(commands.attached)
                self.assertTrue(runtime.halted)

    def test_checkpoint_failure_after_create_still_cleans_and_halts(self):
        with tempfile.TemporaryDirectory() as d:
            plan,ledger,commands,runtime=self.fixture(Path(d));persist=runtime.persist
            def broken(status,*args):
                if status=='created':raise OSError('synthetic-private-error')
                return persist(status,*args)
            with ledger.claim(UUID),patch.object(runtime,'persist',side_effect=broken):
                ledger.consume(UUID,plan)
                with self.assertRaises(ValueError):runtime.execute(plan,ledger,UUID,IMAGE,60,10)
            self.assertIsNone(commands.resource)
            self.assertEqual(json.loads(runtime.intent.read_text())['status'],'halted')


if __name__=='__main__':unittest.main()
