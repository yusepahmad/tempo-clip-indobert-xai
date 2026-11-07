"""Check portable main-model package without downloading encoders."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'02_web_demo'))
from mtl_engine import MTLDeliveryEngine
from xai_core import MTLHead,TASKS
engine=MTLDeliveryEngine()
for name,digest in engine.manifest['data_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert len(engine.df)==740 and engine.X.shape==(740,1280)
engine.train()
assert isinstance(engine.model,MTLHead) and set(engine.model.heads)==set(TASKS)
pred=engine.predict_vector(engine.X[0])
assert all(p['model_version']=='clip-indobert-mtl-v1' for p in pred.values())
assert not any(name in sys.modules for name in ['semantic_features','model_backend','delivery_engine'])
print('CLIP–IndoBERT joint MTL package verified')
