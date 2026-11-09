"""Standard-library safety/process helpers, embedded in Colab launcher."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import queue
import stat
import subprocess
import tempfile
import threading
import time
import zipfile


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for data in iter(lambda:handle.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()


def extract_verified(archive, expected_sha256, parent):
    """Reject untrusted archive layout before extracting into a NEW directory."""
    archive=Path(archive)
    if sha(archive) != expected_sha256:
        raise ValueError('SHA-256 ZIP tidak cocok; gunakan notebook dan ZIP dari build yang sama.')
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist()
        if len(entries)>2000 or sum(i.file_size for i in entries)>2*1024**3:
            raise ValueError('Archive exceeds demo size/count limits')
        names=[i.filename for i in entries]
        if len(names)!=len(set(names)):
            raise ValueError('Duplicate archive entries')
        for item in entries:
            p=PurePosixPath(item.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in item.filename
                or not p.parts or p.parts[0]!='tempo_colab_runtime'
                or str(p)!=item.filename or item.is_dir()
                or stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError('Unsafe archive path/type: '+item.filename)
        manifest_name='tempo_colab_runtime/MANIFEST_SHA256.json'
        if z.getinfo(manifest_name).file_size>2*1024**2:
            raise ValueError('Manifest too large')
        manifest=json.loads(z.read(manifest_name))
        expected={'tempo_colab_runtime/'+name for name in manifest['files']}
        if set(names)!=expected|{manifest_name}:
            raise ValueError('Archive file set does not match manifest')
        destination=Path(tempfile.mkdtemp(prefix='tempo_e14_',dir=parent))
        for item in entries:
            target=destination/item.filename
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(item) as src, target.open('xb') as dst:
                h=hashlib.sha256()
                for block in iter(lambda:src.read(1024*1024),b''):
                    dst.write(block)
                    h.update(block)
            if item.filename!=manifest_name:
                relative=str(PurePosixPath(item.filename).relative_to('tempo_colab_runtime'))
                if h.hexdigest()!=manifest['files'][relative]:
                    raise ValueError('Content SHA mismatch: '+relative)
    return destination/'tempo_colab_runtime'


def checkpoint_preflight(runtime):
    runtime=Path(runtime)
    state=json.loads((runtime/'PACKAGE_STATE.json').read_text())
    if not state['checkpoint_verified']:
        raise RuntimeError('Checkpoint deployment belum tersedia/verified pada paket ini. '
                           'Training tetap di Kaggle. Minta paket runtime setelah collect berhasil; '
                           'jangan jalankan model baseline sebagai E14.')
    package=runtime/'DEMO_XAI_745_FULL/06_models/micro-e14-qlora-v1'
    result=json.loads((package/'result.json').read_text())
    verified=json.loads((package/'verification.json').read_text())
    if verified['status']!='verified' or verified['result_sha256']!=sha(package/'result.json'):
        raise ValueError('Deployment verification does not match result')
    if result['status']!='complete' or result['version']!='micro-e14-qlora-v1':
        raise ValueError('Wrong checkpoint identity')
    if result['protocol_sha256']!=sha(package/'contract.json'):
        raise ValueError('Wrong deployment contract')
    for name,digest in result['artifacts'].items():
        target=package/name
        if target.resolve().parent != (package/'adapter').resolve() or sha(target)!=digest:
            raise ValueError('Adapter integrity failure')
    return state


def start_native(python, app, log_path):
    log=Path(log_path).open('a')
    process=subprocess.Popen([str(python),'-u',str(Path(app)/'01_notebook/colab_micro_e14_runtime.py'),'native'],
                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1)
    events=queue.Queue()
    def read():
        for line in process.stdout:
            try:events.put(json.loads(line))
            except json.JSONDecodeError:events.put({'event':'error','error':'Invalid worker protocol; inspect log'})
        events.put({'event':'exit','returncode':process.wait()})
    threading.Thread(target=read,daemon=True).start()
    return process,events,log


def wait_event(process, events, expected, timeout=1800):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:event=events.get(timeout=min(5,max(.01,deadline-time.monotonic())))
        except queue.Empty:
            continue
        if event['event'] in ('error','exit'):
            raise RuntimeError('Worker failed: '+json.dumps(event))
        if event['event']!=expected:
            raise RuntimeError('Unexpected worker event: '+json.dumps(event))
        return event
    raise TimeoutError('GPU worker timeout; inspect log, stop the process before retrying.')


def stop_process(process, log=None):
    """Only stop the process handle created by this notebook; never pkill."""
    if process is not None and process.poll() is None:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    if log is not None:log.close()
