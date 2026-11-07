"""Independently audit copied caption/embedding evidence using only Python stdlib."""
import argparse
import array
import ast
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[1]
RECOVERY = SOURCE.parents[2] / 'docs/server-recovery/2026-10-11/e22_caption'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
lines = lambda p: [json.loads(line) for line in p.read_text().splitlines()]
textsha = lambda s: hashlib.sha256(s.encode()).hexdigest()


def npy(raw, shape):
    stream = io.BytesIO(raw)
    assert stream.read(6) == b'\x93NUMPY'
    version = tuple(stream.read(2)); assert version in ((1,0),(2,0),(3,0))
    count = struct.unpack('<H' if version == (1,0) else '<I', stream.read(2 if version == (1,0) else 4))[0]
    assert 0 < count < 1048576
    header = ast.literal_eval(stream.read(count).decode('utf-8' if version == (3,0) else 'latin1').strip())
    assert header['shape'] == shape and header['fortran_order'] is False
    dtype = header['descr']; data = stream.read()
    if dtype == '<f4':
        assert sys.byteorder == 'little' and len(data) == math.prod(shape)*4
        values = array.array('f'); values.frombytes(data)
        assert all(math.isfinite(x) for x in values)
        return values
    assert dtype.startswith('<U') and len(shape)==1
    width=int(dtype[2:]); assert 0<width<=256 and len(data)==shape[0]*width*4
    return [data[i*width*4:(i+1)*width*4].decode('utf-32-le').rstrip('\x00') for i in range(shape[0])]


def unit_error(values, rows, dimension):
    assert len(values)==rows*dimension
    error=max(abs(math.sqrt(sum(x*x for x in values[i*dimension:(i+1)*dimension]))-1) for i in range(rows))
    assert error<1e-5
    return error


def main():
    cap=RECOVERY/'full_caption_cache'; emb=RECOVERY/'full_embeddings'
    verified=read(cap/'verification.json')
    assert verified['status']=='verified' and verified['samples']==740
    assert verified['verifier_sha256']==sha(SOURCE/'verify.py')
    for name,digest in verified['sha256'].items(): assert sha(cap/name)==digest
    assert len(verified['sha256'])==742
    for name,digest in verified['prepared_sha256'].items(): assert sha(RECOVERY/name)==digest
    config=read(cap/'run_config.json'); prepared=read(RECOVERY/'config.json')
    assert config==read(RECOVERY/'low_smoke_cache/run_config.json')
    assert config['quota_source_sha256']==sha(SOURCE.parent/'e18_hosted/quota.py')
    assert config['worker_sha256']==sha(SOURCE/'run.py')
    assert config['preparation_sha256']==sha(SOURCE.parent/'e22_caption/prepare.py')
    assert config['inputs_sha256']==sha(RECOVERY/'inputs.jsonl') and config['config_sha256']==sha(RECOVERY/'config.json')
    assert config['reasoning_effort']=='low' and config['max_image_side']==768 and config['max_tokens']==4096
    csv_path=PROJECT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    assert sha(csv_path)==prepared['csv_sha256']=='cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a'
    df=list(csv.DictReader(csv_path.open(encoding='utf-8-sig')))
    captions=lines(cap/'captions.jsonl'); inputs=lines(RECOVERY/'inputs.jsonl')
    assert len(df)==len(captions)==len(inputs)==740
    ids=[r['sample_id'] for r in df];assert len(set(ids))==740
    cost=0
    for i,(row,caption,request) in enumerate(zip(df,captions,inputs)):
        record=read(cap/'records'/f'{i:04d}.json')
        assert record['status']=='complete' and record['index']==caption['index']==request['index']==i
        assert record['sample_id']==caption['sample_id']==request['sample_id']==row['sample_id']
        assert record['run_config_sha256']==sha(cap/'run_config.json') and record['http_status']==200
        assert record['model']==config['model']==record['response']['model']
        for name in ('image_sha256','transmitted_image_sha256','image_size','prompt_sha256'):
            assert record[name]==request[name]
        assert request['prompt_sha256']==textsha(request['prompt'])
        assert len(record['response']['choices'])==1
        choice=record['response']['choices'][0]
        assert record['caption']==caption['caption']==choice['message']['content'].strip()
        assert len(caption['caption'])>=40 and record['finish_reason']==choice['finish_reason']=='stop' and record['usable'] is True
        usage=record['response']['usage']; pricing=usage['cost']
        value=(pricing['input_tokens_cost_nanodollars']+pricing['output_tokens_cost_nanodollars'])/1e9
        assert 0<=value<=.05 and abs(value-record['cost_usd'])<1e-12
        assert usage['prompt_tokens']>0 and usage['completion_tokens']>=0
        assert len(record['quota_before'])==len(record['quota_after'])==2
        for before,after in zip(record['quota_before'],record['quota_after']):
            assert before['period']==after['period'] and abs(after['used']-before['used']-value)<1e-6 and after['remaining']>=.10
        cost+=value
    assert abs(cost-verified['cost_usd'])<1e-12 and cost<=config['budget_usd']==6
    v=read(emb/'verification.json');meta=read(emb/'meta.json');signature=meta['signature']
    assert v['status']=='verified' and v['samples']==740 and v['dimension']==1024
    assert v['verifier_sha256']==sha(SOURCE/'verify_embeddings.py')
    assert len(v['sha256'])==4
    for name,digest in v['sha256'].items():assert sha(emb/name)==digest
    assert signature==read(emb/'protocol.json') and signature['worker_sha256']==sha(SOURCE/'embed.py')
    assert signature['captions_verification_sha256']==sha(cap/'verification.json') and signature['captions_sha256']==sha(cap/'captions.jsonl')
    assert signature['csv_sha256']==sha(csv_path) and signature['model']=='BAAI/bge-m3'
    assert signature['revision']=='5617a9f61b028005a4858fdac845db406aefb181'
    assert signature['model_snapshot']==read(RECOVERY/'model_preparation.json')['model']
    assert signature['pooling']=='CLS then L2' and signature['prefix']=='' and signature['max_length']==1024
    assert meta['status']=='complete' and meta['samples']==740 and meta['dimension']==1024
    assert meta['embeddings_sha256']==sha(emb/'embeddings.npz') and meta['input_audit_sha256']==sha(emb/'input_audit.jsonl')
    audit=lines(emb/'input_audit.jsonl');assert len(audit)==1480
    views=['caption','caption_context']; assert signature['views']==views
    for j,view in enumerate(views):
        for i,(row,caption) in enumerate(zip(df,captions)):
            text=caption['caption'] if j==0 else caption['caption']+'\n'+row['headline_verified']+' '+row['supporting_text_verified']
            a=audit[j*740+i]
            assert a['view']==view and a['index']==i and a['sample_id']==ids[i] and a['text_sha256']==textsha(text)
            assert isinstance(a['untruncated_tokens'],int) and a['untruncated_tokens']>0
            assert a['truncated']==(a['untruncated_tokens']>1024)
        assert meta['truncated_by_view'][view]==sum(a['truncated'] for a in audit if a['view']==view)
    norms={}
    with zipfile.ZipFile(emb/'embeddings.npz') as archive:
        assert set(archive.namelist())=={'sample_id.npy','caption.npy','caption_context.npy'}
        assert all(a.file_size<20000000 for a in archive.infolist())
        assert npy(archive.read('sample_id.npy'),(740,))==ids
        for name in views:norms[name]=unit_error(npy(archive.read(name+'.npy'),(740,1024)),740,1024)
    assert v['sampled_indices']==[0,1,37,123,369,739]
    assert set(v['maximum_absolute_errors'])==set(views) and all(0<=e<1e-5 for e in v['maximum_absolute_errors'].values())
    report=dict(status='verified',samples=740,caption_cost_quota_usd=cost,dimension=1024,
        caption_verification_sha256=sha(cap/'verification.json'),embedding_verification_sha256=sha(emb/'verification.json'),
        verifier_sha256=sha(Path(__file__)),maximum_norm_errors=norms,
        checks=['all742 caption manifest hashes/current worker/verifier/preparation pins','all740 rawcaption/ID/prompt/imageprovenance/usage/quota','embedding4manifest/source/model/snapshot/caption CSV pins','all1480 inputtext hashes/truncation metadata','independent nonpickle NPY float32finite/unit and740UnicodeIDs'],
        limitations=['imagePNG reconstruction and12 sampled embeddingforwards performed by inspected server auditor, not rerun here','tokenization counts server-reconstructed; root verifies text hashes and truncation logic','semantic caption accuracy not certified; no Task2 quality score'])
    target=RECOVERY/'root_full_feature_verification.json'
    assert not target.exists(),'Existing report needs inspection; no automatic overwrite'
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def selftest():
    def packet(dtype,shape,data):
        header=repr(dict(descr=dtype,fortran_order=False,shape=shape)).encode()+b'\n'
        return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(header))+header+data
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z:z.writestr('fixture.npy',packet('<f4',(2,2),struct.pack('<4f',1,0,0,1)))
    with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as z:a=npy(z.read('fixture.npy'),(2,2))
    assert unit_error(a,2,2)==0
    assert npy(packet('<U2',(2,), 'A\x00BC'.encode('utf-32-le')),(2,))==['A','BC']
    failures=[lambda:npy(packet('|O',(1,),b'1234'),(1,)),lambda:npy(packet('<f4',(1,),struct.pack('<f',float('nan'))),(1,)),
              lambda:unit_error([0,0],1,2),lambda:npy(packet('<f4',(1,),struct.pack('<f',1)),(2,)),
              lambda:npy(b'invalid',(1,))]
    for f in failures:
        try:f()
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Invalid fixture accepted')
    assert not (RECOVERY/'full_caption_cache/verification.json').exists(),'Missing-gate fixture requires pending fullcache'
    try:main()
    except FileNotFoundError:pass
    else:raise AssertionError('Expected missing-fullcache rejection')
    print('PASS stdlib float/Unicode/unit parsing,5 invalid fixtures,missing-fullcache gate')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--selftest',action='store_true');args=parser.parse_args()
    selftest() if args.selftest else main()
