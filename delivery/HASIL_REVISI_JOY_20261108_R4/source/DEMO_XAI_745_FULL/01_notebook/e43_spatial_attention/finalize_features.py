"""Wait for specific extraction tmux to exit, then audit and package; never retry."""
import subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    start=time.monotonic()
    while subprocess.run(['tmux','has-session','-t','tempo-e43-regions'],capture_output=True).returncode==0:
        assert time.monotonic()-start<1800,'Extraction wait exceeded; no restart'
        time.sleep(10)
    assert (ROOT/'04_hasil_eksperimen/e43_spatial_attention/features_manifest.json').exists(),'Extraction terminal without completed manifest'
    source=Path(__file__).resolve().parent
    for name in ['verify_features.py','prepare.py']:
        subprocess.run([sys.executable,'-u',str(source/name)],cwd=ROOT,check=True)
    print('AUDITED PACKAGE READY; no GPU launched',flush=True)
if __name__=='__main__':main()
