import json
from pathlib import Path
here=Path(__file__).resolve().parent
target=here/'kernel';target.mkdir(exist_ok=True)
source=(here/'launch.py').read_text().replace('worker.write_text(WORKER_SOURCE)', 'worker.write_text('+repr((here/'worker.py').read_text())+')')
(target/'launch.py').write_text(source)
(target/'kernel-metadata.json').write_text(json.dumps({
    'id':'yusepmuhamadzazuli/tempo-e06-semantic','title':'Tempo E06 Semantic',
    'code_file':'launch.py','language':'python','kernel_type':'script','is_private':True,
    'enable_gpu':True,'enable_internet':True,
    'dataset_sources':['yusepmuhamadzazuli/tempo-benchmark-20261005'],
    'kernel_sources':['yusepmuhamadzazuli/tempo-e01-vlm'],
    'competition_sources':[],'model_sources':[]},indent=2))
print(target)
