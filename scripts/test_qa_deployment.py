"""Read-only deployment tooling against disposable Git/file/proc fixtures only."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('deployment',Path(__file__).with_name('qa_deployment.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


class DeploymentTests(unittest.TestCase):
    def fixture(self,root):
        app=root/'app';app.mkdir();(app/'server'/'app').mkdir(parents=True)
        (app/'client'/'src').mkdir(parents=True);(app/'client'/'dist'/'assets').mkdir(parents=True)
        files={'server/server.py':'from app import create_app\n', 'server/app/__init__.py':'# fixture\n',
            'server/config.py':'# public source only\n','server/requirements.txt':'flask==3.1.0\n',
            'client/src/main.ts':'// fixture\n','client/package.json':'{}',
            'client/dist/index.html':'<script src="/assets/fixture.js"></script>',
            'client/dist/assets/fixture.js':'// built fixture\n'}
        for path,text in files.items():(app/path).write_text(text)
        def git(*args):
            return subprocess.run(['git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',*args],cwd=app,capture_output=True,text=True,check=True,timeout=5).stdout.strip()
        git('init','-q');git('add','server','client/src','client/package.json')
        git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
        revision=git('rev-parse','HEAD')
        manifest=d.make_manifest(app,revision,app/'client'/'dist','Synthetic source/build review')
        proc=root/'proc';proc.mkdir();(proc/'stat').write_text(f'btime {int(time.time())-100}\n')
        return app,proc,manifest

    def test_git_object_bound_manifest_and_disk_matches_are_not_runtime_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            app,proc,manifest=self.fixture(Path(directory))
            result=d.observe(manifest,app,proc_root=proc)
            self.assertTrue(result['source_files_match']);self.assertTrue(result['frontend_files_match'])
            self.assertFalse(result['runtime_identity_verified']);self.assertFalse(result['live_authorized'])
            self.assertFalse(result['served_frontend_verified']);self.assertIsNone(result['verified_running_revision'])
            (app/'server'/'server.py').write_text('dirty working source')
            again=d.make_manifest(app,manifest['target_revision'],app/'client'/'dist','Synthetic source/build review')
            self.assertEqual(again['sources'],manifest['sources'],'Expected source must come from Git objects, not dirty files')

    def test_changed_source_extra_python_and_frontend_are_detected_without_reading_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            app,proc,manifest=self.fixture(Path(directory))
            secret=app/'server'/'.env';secret.write_text('private-fixture-password')
            original=d.file_observation
            def guarded(path):
                if path==secret:raise AssertionError('Private env must not be read')
                return original(path)
            with patch.object(d,'file_observation',side_effect=guarded):
                (app/'server'/'app'/'unexpected.py').write_text('# fixture')
                (app/'server'/'server.py').write_text('# changed')
                (app/'client'/'dist'/'assets'/'fixture.js').write_text('// changed')
                result=d.observe(manifest,app,proc_root=proc)
            self.assertFalse(result['source_files_match']);self.assertEqual(result['unexpected_python_count'],1)
            self.assertFalse(result['frontend_files_match']);self.assertNotIn('private-fixture-password',json.dumps(result))

    def test_invalid_manifest_paths_checksum_and_symlink_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            app,proc,manifest=self.fixture(Path(directory))
            for name in ('../outside','server/.env','client/dist/../secret'):
                altered=copy.deepcopy(manifest);altered['sources'][name]='a'*64;d.seal(altered)
                with self.assertRaises(ValueError):d.observe(altered,app,proc_root=proc)
            altered=copy.deepcopy(manifest);altered['target_revision']='b'*40
            with self.assertRaises(ValueError):d.observe(altered,app,proc_root=proc)
            path=app/'server'/'server.py';path.unlink();path.symlink_to(app/'server'/'config.py')
            with self.assertRaises(ValueError):d.observe(manifest,app,proc_root=proc)

    def test_process_metadata_is_rechecked_and_never_copies_command_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            app,proc,manifest=self.fixture(Path(directory));pid=proc/'42';pid.mkdir()
            (pid/'status').write_text(f'Name:\tgunicorn\nPPid:\t1\nUid:\t{os.getuid()} 0 0 0\n')
            (pid/'cmdline').write_bytes(b'gunicorn\x00--private-fixture-password\x00server:app\x00')
            (pid/'stat').write_text('42 (gunicorn) '+' '.join(['S','1']+['0']*17+['100']))
            (pid/'cwd').symlink_to(app/'server',target_is_directory=True)
            (pid/'exe').symlink_to(Path(sys.executable).resolve())
            result=d.observe(manifest,app,proc_root=proc)
            self.assertEqual(result['processes'][0]['pid'],42)
            self.assertEqual(result['processes'][0]['start_ticks'],100)
            self.assertNotIn('private-fixture-password',json.dumps(result))
            self.assertFalse(result['runtime_identity_verified'])

    def test_mid_observation_file_change_rejects_stale_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            app,proc,manifest=self.fixture(Path(directory))
            def change(*args,**kwargs):
                (app/'server'/'server.py').write_text('# changed during probe')
                return []
            with patch.object(d,'process_observations',side_effect=change):
                with self.assertRaises(ValueError):d.observe(manifest,app,proc_root=proc)

    def test_missing_or_incomplete_build_and_unreviewed_manifest_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            app,proc,manifest=self.fixture(Path(directory))
            with self.assertRaises(ValueError):d.make_manifest(app,manifest['target_revision'],app/'client'/'dist','')
            altered=copy.deepcopy(manifest);altered['frontend'].pop('index.html');d.seal(altered)
            with self.assertRaises(ValueError):d.observe(altered,app,proc_root=proc)


if __name__=='__main__':unittest.main()
