import io
import json
from pathlib import Path
import queue
import stat
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from colab_e14_support import sha, extract_verified, checkpoint_preflight, wait_event, stop_process


class ColabSupportTests(unittest.TestCase):
    def archive(self, folder, content=None, extra=None, symlink=False):
        import hashlib
        path=Path(folder)/'test.zip'
        content=content or {'PACKAGE_STATE.json':b'{"checkpoint_verified":false}'}
        manifest={'files':{name:hashlib.sha256(data).hexdigest() for name,data in content.items()}}
        with zipfile.ZipFile(path,'w') as z:
            for name,data in content.items():z.writestr('tempo_colab_runtime/'+name,data)
            z.writestr('tempo_colab_runtime/MANIFEST_SHA256.json',json.dumps(manifest))
            if extra:z.writestr(extra,b'bad')
            if symlink:
                item=zipfile.ZipInfo('tempo_colab_runtime/link')
                item.external_attr=(stat.S_IFLNK|0o777)<<16
                z.writestr(item,b'/etc/passwd')
        return path

    def test_extract_and_pending_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            z=self.archive(folder)
            root=extract_verified(z,sha(z),folder)
            self.assertTrue((root/'PACKAGE_STATE.json').exists())
            with self.assertRaisesRegex(RuntimeError,'belum tersedia'):
                checkpoint_preflight(root)

    def test_wrong_zip_hash_does_not_extract(self):
        with tempfile.TemporaryDirectory() as folder:
            z=self.archive(folder)
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                extract_verified(z,'0'*64,folder)
            self.assertEqual(len(list(Path(folder).iterdir())),1)

    def test_traversal_absolute_duplicate_and_unknown(self):
        for name in ('../escape','/absolute','tempo_colab_runtime/../escape',
                     'tempo_colab_runtime\\escape','tempo_colab_runtime/unknown',
                     'tempo_colab_runtime/PACKAGE_STATE.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                z=self.archive(folder,extra=name)
                with self.assertRaises(ValueError):extract_verified(z,sha(z),folder)

    def test_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            z=self.archive(folder,symlink=True)
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                extract_verified(z,sha(z),folder)

    def test_manifest_content_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            z=self.archive(folder)
            # Valid ZIP hash, invalid internal content hash.
            replacement=Path(folder)/'bad.zip'
            with zipfile.ZipFile(z) as source,zipfile.ZipFile(replacement,'w') as target:
                for name in source.namelist():
                    data=source.read(name)
                    if name.endswith('PACKAGE_STATE.json'):data=b'tampered'
                    target.writestr(name,data)
            with self.assertRaisesRegex(ValueError,'Content SHA'):
                extract_verified(replacement,sha(replacement),folder)

    def test_worker_ready_error_and_timeout(self):
        events=queue.Queue()
        events.put({'event':'ready','models':{'backend':'micro-e14-qlora'}})
        self.assertEqual(wait_event(None,events,'ready',.1)['event'],'ready')
        events.put({'event':'error','error':'CUDA unavailable'})
        with self.assertRaisesRegex(RuntimeError,'CUDA'):
            wait_event(None,events,'prediction',.1)
        with self.assertRaises(TimeoutError):wait_event(None,events,'ready',.001)

    def test_stop_only_owned_process(self):
        process=Mock()
        process.poll.return_value=None
        log=Mock()
        stop_process(process,log)
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=10)
        log.close.assert_called_once()

    def test_native_protocol_predict_stop_without_http_or_gpu(self):
        import contextlib
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'DEMO_XAI_745_FULL/01_notebook/colab_micro_e14_runtime.py'
        spec=importlib.util.spec_from_file_location('colab_runtime_fixture',path)
        runtime=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        app=Mock()
        app.SAMPLE_IDS={'fixture'}
        response=Mock(status_code=200)
        response.get_json.return_value={'snapshot':{'model':'micro-e14-qlora-v1'}}
        app.app.test_client.return_value.post.return_value=response
        commands='\n'.join(json.dumps(c) for c in [
            {'action':'predict','sample_id':'fixture'}, {'action':'predict','sample_id':'bad'},
            {'action':'unknown'}, {'action':'stop'}])+'\n'
        output=io.StringIO()
        with patch.object(runtime,'load_app',return_value=(app,{'ready':True})),patch('sys.stdin',io.StringIO(commands)),contextlib.redirect_stdout(output):
            runtime.native()
        events=[json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([e['event'] for e in events],['ready','prediction','error','error','stopped'])
        app.app.test_client.return_value.post.assert_called_once_with('/api/analisis',data={'sample_id':'fixture'})

    def test_optional_web_gate_stays_false(self):
        import sys
        sys.path.insert(0,str(Path(__file__).parent))
        import build_colab_micro_e14 as builder
        nb=builder.notebook(Path('demo.zip'),'0'*64,{'checkpoint_verified':False})
        import nbformat
        nbformat.validate(nb)
        source='\n'.join(c.source for c in nb.cells if c.cell_type=='code')
        self.assertIn('WEB_MODE_ALLOWED_POSITIVE_COMPUTE_BALANCE = False',source)
        self.assertIn('serve_kernel_port_as_iframe',source)
        self.assertNotIn('ngrok',source)
        self.assertNotIn('cloudflared',source)
        self.assertNotIn('kaggle.json',source)
        for index,cell in enumerate(nb.cells):
            if cell.cell_type=='code':compile(cell.source,f'cell-{index}','exec')


if __name__=='__main__':unittest.main()
