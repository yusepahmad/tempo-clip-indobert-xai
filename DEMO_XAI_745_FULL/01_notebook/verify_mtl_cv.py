"""Reproduce fusion-only CV; preserve all historical result files."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'02_web_demo'))
from mtl_engine import MTLDeliveryEngine
from run_evaluation import evaluasi
engine=MTLDeliveryEngine();start=time.monotonic()
metrics,predictions=evaluasi(engine.X,engine.y,engine.ncls)
historical=json.loads((ROOT/'04_hasil_eksperimen/hasil_mtl_740_task2domain.json').read_text())['fusion MTL (CLIP+IndoBERT)']
report=dict(status='completed',protocol=engine.manifest['evaluation']['protocol'],metrics=metrics,historical=historical,
    identical_to_historical=metrics==historical,seconds=time.monotonic()-start,
    note='Rerun on server environment; hardware/library differences can change scores. Historical files untouched.')
(ROOT/'07_delivery_evidence/cv_reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
(ROOT/'07_delivery_evidence/cv_oof_predictions.json').write_text(json.dumps({t:arr.tolist() for t,arr in predictions.items()}))
print(json.dumps(report,indent=2))
