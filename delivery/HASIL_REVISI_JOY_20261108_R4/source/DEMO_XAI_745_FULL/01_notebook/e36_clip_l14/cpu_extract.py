"""Label-free CPU fallback; calls the unchanged pinned E36 extractor."""
from pathlib import Path
import hashlib,json,os
from cpu_extract_impl import extract
ROOT=Path(__file__).resolve().parents[2]
if __name__=='__main__':
    csv=ROOT/'03_data/DATASET_740_TASK2_DOMAIN.csv'
    release=Path('/home/yusep/workspace/learn/delivery_week34_clip_indobert_20261012/DEMO_XAI_745_FULL/06_models/clip-indobert-mtl-v1/manifest.json')
    expected=json.loads(release.read_text())['data_sha256']['03_data/DATASET_740_TASK2_DOMAIN.csv']
    assert hashlib.sha256(csv.read_bytes()).hexdigest()==expected
    os.environ['TEMPO_EXPECTED_CSV_SHA']=expected
    pin=json.loads(Path(__file__).with_name('pinned_model.json').read_text())
    out=ROOT/'04_hasil_eksperimen/e36_clip_l14_cpu_fallback'
    assert not (out/'features.npz').exists(),'Do not overwrite completed fallback'
    extract(ROOT,out,pin,'cpu')
