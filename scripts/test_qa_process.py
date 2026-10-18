"""Local Python child-process fixtures only; never invoke Docker, SSH or browsers."""
import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('process',Path(__file__).with_name('qa_process.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
# The fixture uses the Linux system interpreter so an empty environment does not
# depend on hosted-toolcache loader variables; the helper itself runs in CI Python.
PYTHON=str(Path("/usr/bin/python3").resolve())


class ProcessTests(unittest.TestCase):
    def runner(self,root):return p.GroupRunner(root,{PYTHON},grace_seconds=0.15)

    def test_private_nonoverwriting_raw_logs_and_exit_status(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            result=runner.run([PYTHON,'-c','import sys; from pathlib import Path; Path("child-artifact").write_text("fixture"); print("synthetic secret");sys.stderr.write("private error");sys.exit(7)'],{},2,'one')
            self.assertEqual(result['returncode'],7)
            self.assertIn('synthetic secret',(root/'one.stdout').read_text())
            self.assertEqual((root/'one.stderr').stat().st_mode & 0o777,0o600)
            self.assertEqual((root/'child-artifact').stat().st_mode & 0o777,0o600)
            self.assertNotIn('synthetic secret',str(result))
            with self.assertRaises(ValueError):runner.run([PYTHON,'-c','pass'],{},2,'one')

    def test_unknown_executable_relative_command_environment_and_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            for argv,env,timeout,label in [(['sh','-c','true'],{},1,'one'),
                (['/bin/sh','-c','true'],{},1,'two'),([PYTHON,'-c','pass'],{'PYTHONPATH':'unsafe'},1,'three'),
                ([PYTHON,'-c','pass'],{},0,'four'),([PYTHON,'-c','pass'],{},1,'../escape')]:
                with self.subTest(label=label),self.assertRaises(ValueError):runner.run(argv,env,timeout,label)
            self.assertFalse(list(root.iterdir()))

    def test_timeout_kills_term_ignoring_process_and_does_not_expose_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            started=time.monotonic()
            with self.assertRaisesRegex(p.ProcessFailure,'timeout') as failure:
                runner.run([PYTHON,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("private",flush=True);time.sleep(30)'],{},0.3,'timeout')
            self.assertLess(time.monotonic()-started,3)
            self.assertNotIn('private',str(failure.exception))
            self.assertTrue(runner.idle())

    def test_parent_exit_cannot_leave_a_running_child_in_the_group(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            code='import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)'
            runner.run([PYTHON,'-c',code],{},2,'child')
            self.assertTrue(runner.idle())

    def test_output_limit_cancels_and_preserves_only_bounded_private_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            with self.assertRaisesRegex(p.ProcessFailure,'output limit'):
                runner.run([PYTHON,'-c','import os;os.write(1,b"x"*1000000)'],{},2,'limit',max_output_bytes=4096)
            self.assertLessEqual(sum((root/f'limit.{name}').stat().st_size for name in ['stdout','stderr']),4096)
            self.assertTrue(runner.idle())

    def test_uncertain_cleanup_cannot_silently_reset_runner(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            with patch.object(runner,'cancel',side_effect=p.ProcessFailure('unavailable identity')):
                with self.assertRaisesRegex(p.ProcessFailure,'cleanup unresolved'):
                    runner.run([PYTHON,'-c','pass'],{},2,'cleanup')
            self.assertFalse(runner.idle())
            with self.assertRaises(ValueError):runner.run([PYTHON,'-c','pass'],{},2,'next')

    def test_output_persistence_failure_halts_instead_of_losing_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o700);runner=self.runner(root)
            with patch.object(p.os,'fsync',side_effect=OSError('synthetic private persistence detail')):
                with self.assertRaisesRegex(p.ProcessFailure,'persistence unresolved') as error:
                    runner.run([PYTHON,'-c','print("fixture")'],{},2,'persist')
            self.assertNotIn('synthetic private',str(error.exception))
            self.assertFalse(runner.idle())

    def test_private_root_and_symlink_log_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.chmod(0o755)
            with self.assertRaises(ValueError):self.runner(root)
            root.chmod(0o700);target=root/'keep';target.write_text('unchanged')
            (root/'one.stdout').symlink_to(target)
            with self.assertRaises(ValueError):self.runner(root).run([PYTHON,'-c','pass'],{},2,'one')
            self.assertEqual(target.read_text(),'unchanged')


if __name__=='__main__':unittest.main()
