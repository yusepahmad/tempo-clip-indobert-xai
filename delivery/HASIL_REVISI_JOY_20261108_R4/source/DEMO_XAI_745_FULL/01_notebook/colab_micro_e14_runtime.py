"""Colab subprocess entry point: notebook-native inference or optional web.

No tunnels, credentials, cached OOF predictions, or fallback models.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import runpy
import sys

APP = Path(__file__).resolve().parents[1]


def load_app():
    os.environ['TEMPO_BACKEND'] = 'micro-e14-qlora'
    os.environ['TEMPO_HOST'] = '127.0.0.1'
    sys.path.insert(0,str(APP/'02_web_demo'))
    # Keep the JSON-lines protocol separate from model/library startup logs.
    with contextlib.redirect_stdout(sys.stderr):
        import app
    info = app.ENG.description()
    if not info.get('ready') or info.get('backend') != 'micro-e14-qlora':
        raise RuntimeError(info.get('unavailable_reason') or 'E14 not ready; no fallback')
    return app, info


def native():
    app, info = load_app()
    print(json.dumps({'event':'ready','models':info}),flush=True)
    client = app.app.test_client()
    for line in sys.stdin:
        try:
            command = json.loads(line)
            if command.get('action') == 'stop':
                print(json.dumps({'event':'stopped'}),flush=True)
                return
            if command.get('action') != 'predict':
                raise ValueError('Only predict/stop are supported')
            sample_id = command.get('sample_id')
            if sample_id not in app.SAMPLE_IDS:
                raise ValueError('Unknown dataset sample_id')
            with contextlib.redirect_stdout(sys.stderr):
                result = client.post('/api/analisis', data={'sample_id':sample_id})
            if result.status_code != 200:
                raise RuntimeError((result.get_json() or {}).get('error','Prediction failed'))
            print(json.dumps({'event':'prediction','result':result.get_json()}),flush=True)
        except Exception as e:
            print(json.dumps({'event':'error','error':str(e)}),flush=True)


def web():
    # Engine initializes + checks GPU smoke inside app.py before Flask starts.
    os.environ['TEMPO_BACKEND'] = 'micro-e14-qlora'
    os.environ['TEMPO_HOST'] = '127.0.0.1'
    os.environ.setdefault('TEMPO_PORT','7861')
    sys.path.insert(0,str(APP/'02_web_demo'))
    runpy.run_path(str(APP/'02_web_demo/app.py'),run_name='__main__')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['native','web'])
    args=parser.parse_args()
    {'native':native,'web':web}[args.mode]()
