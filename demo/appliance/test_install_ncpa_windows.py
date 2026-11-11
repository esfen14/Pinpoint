"""Offline tests for the Windows NCPA install and registration; VBoxManage and Pinpoint are never contacted."""
from pathlib import Path
import hashlib
import io
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import install_ncpa_windows as ncpa

TOKEN='0123456789abcdef0123456789abcdef'
PASSWORD='Sup3r-Secret-Windows-Pass'
PINPOINT_PASSWORD='Pinpoint-Admin-Pass-9'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
        self.installer=self.dir/'ncpa-3.5.0.exe';self.installer.write_bytes(b'installer bytes')
        self.sha=hashlib.sha256(b'installer bytes').hexdigest()
        self.token_file=self.dir/'ncpa-token';self.token_file.write_text(TOKEN+'\n')
        self.password_file=self.dir/'login-password';self.password_file.write_text(PASSWORD+'\n')
        self.pinpoint_password_file=self.dir/'pinpoint-password';self.pinpoint_password_file.write_text(PINPOINT_PASSWORD+'\n')
    def tearDown(self):self.tmp.cleanup()
    def base_args(self,*extra):
        return ['--installer',str(self.installer),'--sha256',self.sha,'--token-file',str(self.token_file),
                '--windows-password-file',str(self.password_file),*extra]
    def run_main(self,argv,state='running',http=None,fail_on=None):
        calls=[];copied=[]
        def runner(command):
            calls.append(command)
            if command[:2]==['VBoxManage','showvminfo']:
                return 'VMState="%s"\n'%state if state else (_ for _ in ()).throw(ValueError('none'))
            if command[2:4]==[ncpa.WINDOWS_VM,'copyto']:
                target=command[-1]
                copied.append((command,Path(target).read_text() if Path(target).name.endswith('.cfg') else None))
            if fail_on and fail_on in ' '.join(command):raise ValueError('step failed')
            return ''
        out=io.StringIO();err=io.StringIO()
        code=ncpa.main(argv,runner=runner,out=out,err=err,http=http)
        return code,calls,out.getvalue(),err.getvalue(),copied


class CommandTests(Fixture):
    def test_guest_commands_take_the_windows_password_from_a_file(self):
        command=ncpa.guest_run(ncpa.WINDOWS_VM,self.password_file,'Get-Date')
        self.assertEqual(command[:4],['VBoxManage','guestcontrol',ncpa.WINDOWS_VM,'run'])
        self.assertIn('--passwordfile',command);self.assertIn(str(self.password_file),command)
        self.assertNotIn('--password',command)
        self.assertEqual(command[-1],'Get-Date')
    def test_address_script_sets_the_lab_address_without_a_default_route(self):
        script=ncpa.network_script()
        self.assertIn('10.77.1.3',script);self.assertIn('-PrefixLength 27',script)
        self.assertNotIn('DefaultGateway',script)
    def test_firewall_script_allows_only_the_appliance_on_the_port(self):
        script=ncpa.firewall_script(5693)
        self.assertIn('-LocalPort 5693',script);self.assertIn('-RemoteAddress 10.77.1.1',script)
        self.assertNotIn('Any',script)
    def test_hash_script_compares_the_expected_digest(self):
        script=ncpa.hash_script('ncpa-3.5.0.exe',self.sha)
        self.assertIn(self.sha,script);self.assertIn('Get-FileHash',script)
    def test_values_that_reach_powershell_are_validated(self):
        for name in ("a'b.exe",'a b.exe','x;y.exe','..\\x.exe','setup.msi'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):ncpa.validate_installer_name(name)
        with self.assertRaises(ValueError):ncpa.validate_sha256('abc')
        with self.assertRaises(ValueError):ncpa.validate_port(0)
        with self.assertRaises(ValueError):ncpa.validate_token('short')
    def test_config_snippet_carries_the_token_and_port(self):
        text=ncpa.config_snippet(TOKEN,5693)
        self.assertIn('community_string = '+TOKEN,text);self.assertIn('port = 5693',text)


class PlanTests(Fixture):
    def test_without_apply_nothing_runs_except_the_read_only_vm_check(self):
        code,calls,out,_,copied=self.run_main(self.base_args())
        self.assertEqual(code,0)
        self.assertEqual([c[1] for c in calls],['showvminfo'])
        self.assertEqual(copied,[]);self.assertIn('Nothing was changed',out)
        self.assertIn('10.77.1.3',out);self.assertIn('10.77.1.1',out)
    def test_plan_and_commands_never_contain_a_secret(self):
        _,calls,out,err,_=self.run_main(self.base_args('--apply'))
        text=out+err+'\n'.join(' '.join(c) for c in calls)
        for secret in (TOKEN,PASSWORD):self.assertNotIn(secret,text)
    def test_plan_works_when_the_installer_does_not_exist_yet(self):
        args=['--installer','/no/ncpa.exe','--sha256',self.sha,'--token-file','/no/token','--windows-password-file','/no/pw']
        code,calls,out,_,_=self.run_main(args)
        self.assertEqual(code,0);self.assertIn('Nothing was changed',out)


class ApplyTests(Fixture):
    def test_apply_runs_the_steps_in_order(self):
        code,calls,_,err,copied=self.run_main(self.base_args('--apply'))
        self.assertEqual(code,0,err)
        joined=[' '.join(c) for c in calls]
        def index(text):
            for position,line in enumerate(joined):
                if text in line:return position
            self.fail('missing step: '+text)
        order=[index('ncpa-3.5.0.exe'),index('Get-FileHash'),index('Start-Process'),index('ncpa.cfg.d'),
               index('New-NetIPAddress'),index('New-NetFirewallRule'),index('Invoke-WebRequest')]
        self.assertEqual(order,sorted(order))
    def test_token_reaches_the_guest_only_as_a_copied_file(self):
        _,calls,_,_,copied=self.run_main(self.base_args('--apply'))
        snippets=[text for _,text in copied if text]
        self.assertEqual(len(snippets),1);self.assertIn(TOKEN,snippets[0])
        self.assertFalse(Path(copied[-1][0][-1]).exists() if snippets else True)  # temporary snippet is removed
    def test_hash_mismatch_stops_before_anything_reaches_the_vm(self):
        bad=['--installer',str(self.installer),'--sha256','0'*64,'--token-file',str(self.token_file),
             '--windows-password-file',str(self.password_file),'--apply']
        code,calls,_,err,copied=self.run_main(bad)
        self.assertEqual(code,1);self.assertIn('does not match',err)
        self.assertEqual(copied,[]);self.assertFalse([c for c in calls if 'guestcontrol' in c])
    def test_apply_needs_the_expected_hash(self):
        args=['--installer',str(self.installer),'--token-file',str(self.token_file),'--windows-password-file',str(self.password_file),'--apply']
        code,calls,_,err,_=self.run_main(args)
        self.assertEqual(code,2);self.assertFalse([c for c in calls if 'guestcontrol' in c])
    def test_stopped_vm_is_reported_not_started(self):
        code,calls,_,err,_=self.run_main(self.base_args('--apply'),state='poweroff')
        self.assertEqual(code,1);self.assertIn('not running',err)
        self.assertFalse([c for c in calls if c[1] in {'startvm','guestcontrol'}])
    def test_missing_vm_is_reported(self):
        code,_,_,err,_=self.run_main(self.base_args('--apply'),state=None)
        self.assertEqual(code,1);self.assertIn('does not exist',err)
    def test_a_failing_guest_step_stops_the_run(self):
        code,calls,_,err,_=self.run_main(self.base_args('--apply'),fail_on='New-NetFirewallRule')
        self.assertEqual(code,1)
        self.assertFalse([c for c in calls if 'Invoke-WebRequest' in ' '.join(c)])
    def test_bad_token_file_is_rejected(self):
        self.token_file.write_text('not-a-token\n')
        code,calls,_,err,_=self.run_main(self.base_args('--apply'))
        self.assertEqual(code,2);self.assertFalse([c for c in calls if 'guestcontrol' in c])


class FakeHttp:
    def __init__(self,candidates,register_status=200):
        self.requests=[];self.candidates=candidates;self.register_status=register_status
    def __call__(self,method,url,body=None):
        self.requests.append((method,url,body))
        if url.endswith('/api/user/login'):return 200,{'success':True}
        if url.endswith('/register-candidates'):return 200,{'success':True,'data':{'devices':self.candidates}}
        if url.endswith('/register'):return self.register_status,{'success':self.register_status==200,'message':'agent said no'}
        if url.endswith('/api/user/logout'):return 200,{'success':True}
        return 404,{}


class RegistrationTests(Fixture):
    def register_args(self):
        return self.base_args('--apply','--register','--pinpoint-email','admin@example.com',
                              '--pinpoint-password-file',str(self.pinpoint_password_file))
    def test_registers_the_device_at_the_windows_address(self):
        http=FakeHttp([{'device_id':7,'ip_address':'10.77.1.9'},{'device_id':12,'ip_address':'10.77.1.3'}])
        code,_,out,err,_=self.run_main(self.register_args(),http=http)
        self.assertEqual(code,0,err)
        posts=[r for r in http.requests if r[1].endswith('/12/register')]
        self.assertEqual(len(posts),1);self.assertEqual(posts[0][2],{'token':TOKEN,'port':5693})
        self.assertIn('registered',out.lower())
    def test_login_uses_the_password_file_and_the_secret_is_never_printed(self):
        http=FakeHttp([{'device_id':12,'ip_address':'10.77.1.3'}])
        _,_,out,err,_=self.run_main(self.register_args(),http=http)
        login=[r for r in http.requests if r[1].endswith('/api/user/login')][0]
        self.assertEqual(login[2],{'email':'admin@example.com','password':PINPOINT_PASSWORD})
        for secret in (TOKEN,PINPOINT_PASSWORD,PASSWORD):self.assertNotIn(secret,out+err)
    def test_device_not_discovered_yet_is_a_clear_error(self):
        http=FakeHttp([{'device_id':7,'ip_address':'10.77.1.9'}])
        code,_,_,err,_=self.run_main(self.register_args(),http=http)
        self.assertEqual(code,1);self.assertIn('Rescan',err)
    def test_already_registered_is_success_so_the_run_can_repeat(self):
        http=FakeHttp([{'device_id':12,'ip_address':'10.77.1.3'}],register_status=409)
        code,_,out,_,_=self.run_main(self.register_args(),http=http)
        self.assertEqual(code,0);self.assertIn('already',out.lower())
    def test_agent_refusal_is_reported(self):
        http=FakeHttp([{'device_id':12,'ip_address':'10.77.1.3'}],register_status=502)
        code,_,_,err,_=self.run_main(self.register_args(),http=http)
        self.assertEqual(code,1);self.assertIn('agent said no',err)
    def test_register_without_apply_makes_no_http_calls(self):
        http=FakeHttp([])
        code,_,out,_,_=self.run_main(self.base_args('--register','--pinpoint-email','a@example.com','--pinpoint-password-file',str(self.pinpoint_password_file)),http=http)
        self.assertEqual(code,0);self.assertEqual(http.requests,[]);self.assertIn('register',out.lower())
    def test_register_needs_email_and_password_file(self):
        code,_,_,_,_=self.run_main(self.base_args('--apply','--register'),http=FakeHttp([]))
        self.assertEqual(code,2)
    def test_no_register_option_means_no_http(self):
        http=FakeHttp([])
        self.run_main(self.base_args('--apply'),http=http)
        self.assertEqual(http.requests,[])


if __name__=='__main__':unittest.main()
