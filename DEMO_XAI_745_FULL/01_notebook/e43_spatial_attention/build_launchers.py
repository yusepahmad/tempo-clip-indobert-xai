"""Build private offline Kaggle launchers from exact audited source bytes."""
import sys,json,hashlib
from pathlib import Path
def main():
    package=Path(sys.argv[1]);source=Path(__file__).resolve().parent
    manifest=json.loads((package/'manifest.json').read_text());assert manifest['status']=='audited_package'
    for n,h in manifest['files'].items():assert hashlib.sha256((package/n).read_bytes()).hexdigest()==h
    digest=hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest()
    dataset='research-account/tempo-e43-spatial-features-20261013'
    (package/'dataset-metadata.json').write_text(json.dumps(dict(title='Tempo E43 Spatial Features 20261013',id=dataset,licenses=[dict(name='other')]),indent=2)+'\n')
    for kind in ['smoke','full']:
        folder=source/kind;folder.mkdir(exist_ok=True)
        meta=dict(id=f'research-account/tempo-e43-spatial-{kind}',title=f'Tempo E43 Spatial {kind.title()}',code_file='launch.py',language='python',kernel_type='script',is_private=True,enable_gpu=True,enable_internet=False,machine_shape='NvidiaTeslaT4',dataset_sources=[dataset],competition_sources=[],kernel_sources=[],model_sources=[])
        (folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
        code="import os,sys,subprocess\nfrom pathlib import Path\n"
        code+=f"os.environ['TEMPO_PACKAGE_SHA']={digest!r}\nos.environ['TEMPO_SMOKE']={'1' if kind=='smoke' else '0'!r}\n"
        for name in ['model.py','worker.py']:code+=f"Path('/kaggle/working/{name}').write_text({(source/name).read_text()!r})\n"
        code+="subprocess.run([sys.executable,'-u','/kaggle/working/worker.py'],check=True)\n"
        compile(code,'launch.py','exec');(folder/'launch.py').write_text(code)
    print('PRIVATE OFFLINE LAUNCHERS READY; no upload/job launched')
if __name__=='__main__':main()
