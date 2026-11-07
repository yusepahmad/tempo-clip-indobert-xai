import json, pathlib, subprocess, shutil
import torch
r={"torch":torch.__version__,"cuda_available":torch.cuda.is_available(),"torch_cuda":torch.version.cuda,"devices":[str(p) for p in pathlib.Path("/dev").glob("nvidia*")]}
r["nvidia_smi_path"]=shutil.which("nvidia-smi")
if r["nvidia_smi_path"]:
 p=subprocess.run(["nvidia-smi"],capture_output=True,text=True);r["nvidia_smi"]=p.stdout+p.stderr
print(json.dumps(r,indent=2),flush=True)
pathlib.Path("/kaggle/working/gpu_diagnostic.json").write_text(json.dumps(r,indent=2))
