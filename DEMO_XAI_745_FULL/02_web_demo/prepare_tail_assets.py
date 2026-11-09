"""Fetch/verify the pinned serving artifacts; never trains a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
MODEL = HERE.parent / '06_models/clip-indobert-tail-rich256-v1'


def sha(path):
    value = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def install_archive(archive, destination, expected):
    # Only explicitly named regular files may leave the archive. Validate the
    # entire staging directory before replacing any existing model artifact.
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination, prefix='.prepare-') as tmp:
        stage = Path(tmp)
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            if len(names) != len(expected) or set(names) != set(expected):
                raise ValueError('Archive contents differ from the model manifest')
            for name, digest in expected.items():
                if Path(name).name != name:
                    raise ValueError('Nested artifact paths are not supported')
                with bundle.open(name) as source, open(stage/name, 'wb') as target:
                    shutil.copyfileobj(source, target)
                if sha(stage/name) != digest:
                    raise ValueError('Artifact hash mismatch: '+name)
        for name in expected:
            os.replace(stage/name, destination/name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--archive', type=Path, help='Local verified model ZIP')
    source.add_argument('--download', action='store_true', help='Download the model ZIP from the documented GitHub release')
    parser.add_argument('--asset-dir', type=Path, default=Path(os.environ.get('TEMPO_TAIL_ASSET_DIR') or MODEL))
    parser.add_argument('--check-only', action='store_true', help='Offline verification, including pinned encoder files')
    args = parser.parse_args()
    if args.check_only and (args.archive or args.download):
        parser.error('--check-only cannot install artifacts')
    manifest = json.loads((MODEL/'manifest.json').read_text())
    if args.download:
        release = json.loads((MODEL/'release.json').read_text())
        with tempfile.TemporaryDirectory(prefix='tempo-model-') as tmp:
            archive = Path(tmp)/'model.zip'
            try:
                urllib.request.urlretrieve(release['url'], archive)
            except urllib.error.HTTPError as error:
                if error.code in (401, 403, 404):
                    parser.error('Release requires GitHub access or is unavailable. Download '+release['file']+' from the Release while logged in (or use gh release download), then run --archive /path/to/file.zip. No repository visibility change is needed.')
                raise
            if sha(archive) != release['sha256']:
                raise ValueError('Release archive SHA-256 mismatch')
            install_archive(archive, args.asset_dir, manifest['asset_sha256'])
    elif args.archive:
        install_archive(args.archive, args.asset_dir, manifest['asset_sha256'])
    for name, digest in manifest['asset_sha256'].items():
        if sha(args.asset_dir/name) != digest:
            raise ValueError('Missing or mismatched model artifact: '+name)
    from huggingface_hub import hf_hub_download
    for key in ('clip', 'indobert'):
        pin = manifest[key]
        files = dict(pin.get('files', {}))
        if key == 'clip':
            files.update({pin['file']:pin['sha256'], 'open_clip_config.json':None})
        for name, digest in files.items():
            path = hf_hub_download(pin['repo'], name, revision=pin['revision'], local_files_only=args.check_only)
            if digest and sha(path) != digest:
                raise ValueError('Backbone hash mismatch: '+key+'/'+name)
    print(json.dumps({'status':'verified', 'model':manifest['version'], 'asset_files':len(manifest['asset_sha256']), 'offline':args.check_only}))


if __name__ == '__main__':
    main()
