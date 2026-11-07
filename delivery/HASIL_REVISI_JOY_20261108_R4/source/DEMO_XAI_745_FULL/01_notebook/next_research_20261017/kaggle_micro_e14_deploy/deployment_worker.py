"""MICRO-E07: one Qwen3-VL LoRA adapter, three task objectives, nested outer fold."""
import gc
import hashlib
import json
import os
from pathlib import Path
import random
import time

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
os.environ["HF_HOME"] = "/tmp/tempo_hf_cache"

import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch import nn
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training

MODEL = "Qwen/Qwen3-VL-8B-Instruct"
REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
SMOKE = os.environ.get("E07_SMOKE", "1") == "1"
FOLD = int(os.environ.get("E07_FOLD", "1"))
assert 1 <= FOLD <= 5
OUT = Path("/kaggle/working/e07_smoke" if SMOKE else f"/kaggle/working/e07_fold{FOLD}")
OUT = Path("/kaggle/working/e14_deploy")
OUT.mkdir(exist_ok=True)
# One epoch alternates tasks, so each head sees roughly one third of the
# training set. E14 selects among three joint epochs (about one pass/task).
MAX_EPOCHS = 3
ACCUM = 8
TASKS = ("task1_issue", "task2_domain_sumber", "task3_primary_entity_type")
DEFINITIONS = {
    "task1_issue": {
        "corruption_and_bribery": "korupsi, suap, gratifikasi, atau penyalahgunaan dana dan jabatan",
        "economy_business_and_state_enterprise": "ekonomi, bisnis, keuangan, perusahaan, BUMN, pajak, atau perdagangan",
        "election_and_political_competition": "pemilu, pilkada, kampanye, koalisi, kandidat, atau kompetisi politik",
        "environment_and_natural_resources": "lingkungan, energi, tambang, hutan, lahan, air, atau sumber daya alam",
        "human_rights_and_social_conflict": "hak asasi, diskriminasi, kekerasan sosial, buruh, agama, atau konflik masyarakat",
        "law_and_justice": "hukum, pengadilan, polisi, kejaksaan, penyidikan, atau keadilan",
        "other_issue": "isu utama di luar sembilan kategori lain",
        "power_and_governance": "kekuasaan, pemerintahan, kabinet, birokrasi, kebijakan, atau kepemimpinan",
        "public_policy_health_and_disaster": "kesehatan, pendidikan, layanan publik, bencana, pandemi, atau kebijakan sosial",
        "security_defense_and_terrorism": "militer, pertahanan, keamanan nasional, intelijen, terorisme, atau perang",
    },
    "task2_domain_sumber": {
        "BENCANA_JERAT": "ancaman, bencana, perangkap, jerat, tekanan, atau keadaan terjepit sebagai kiasan",
        "HEWAN_TUBUH": "hewan, anatomi, penyakit, deformasi, atau perilaku biologis sebagai kiasan",
        "KONSUMSI_TRANSAKSI": "makanan, jamuan, selera, jual-beli, uang, atau pertukaran nilai sebagai kiasan",
        "LAINNYA": "metafora dengan domain sumber selain lima domain metaforis yang disebut",
        "MESIN_INFRASTRUKTUR": "mesin, alat, kendaraan, bangunan, wadah, atau mekanisme buatan sebagai kiasan",
        "NON_METAFORA": "adegan literal tanpa pemetaan metaforis",
        "PERMAINAN_KONTES": "permainan, pertandingan, kompetisi, pertunjukan, atau seni sebagai kiasan",
    },
    "task3_primary_entity_type": {
        "business": "perusahaan swasta, pengusaha, atau organisasi bisnis",
        "civil_society_or_media": "warga, aktivis, organisasi sipil, media, jurnalis, atau kelompok masyarakat",
        "government": "pemerintah, presiden sebagai institusi eksekutif, menteri, kabinet, birokrasi, atau lembaga negara umum",
        "individual": "satu orang tertentu sebagai sasaran utama",
        "judiciary_or_law_enforcement": "polisi, jaksa, hakim, pengadilan, KPK, atau lembaga penegak hukum",
        "legislature": "DPR, parlemen, legislator, atau lembaga legislatif",
        "multiple_or_other": "beberapa tipe sasaran sekaligus atau sasaran yang tidak termasuk kategori lain",
        "political_party": "partai politik atau organisasi politik partisan",
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_all(value):
    random.seed(value)
    np.random.seed(value)
    torch.manual_seed(value)
    torch.cuda.manual_seed_all(value)


def main():
    seed_all(42 + FOLD)
    run_started = time.monotonic()
    csv_paths = list(Path("/kaggle/input").rglob("DATASET_740_TASK2_DOMAIN.csv"))
    assert len(csv_paths) == 1
    csv_path = csv_paths[0]
    root = csv_path.parents[1]
    assert sha(csv_path) == "cba20f8250bcb59481ed2d3d7d5d42fb8242c96a7ba2d11a2cd02ad80862961a"
    frame = pd.read_csv(csv_path).fillna("")
    assert len(frame) == 740 and frame.sample_id.is_unique

    def aligned(name):
        paths = list(Path("/kaggle/input").rglob(name))
        assert len(paths) == 1
        rows = [json.loads(line) for line in paths[0].read_text().splitlines()]
        mapping = {row["sample_id"]: row for row in rows}
        assert len(mapping) == 740 and set(mapping) == set(frame.sample_id)
        return [mapping[sample_id] for sample_id in frame.sample_id], paths[0]

    descriptions, desc_path = aligned("deskripsi.jsonl")
    reasons, zero_path = aligned("zeroshot.jsonl")
    assert sha(desc_path) == "c75e8df3f9b71d6786462f8d0f1187ebe4234fb8dd079924f3f35707ff1b8cd2"
    assert sha(zero_path) == "10c07b06b13fbbf647f2b1ed12a722d9bff8f97caa6b621430d8bc0429ab38c9"

    classes = {task: sorted(DEFINITIONS[task]) for task in TASKS}
    truth = {task: pd.Categorical(frame[task], categories=classes[task]).codes.astype(np.int64) for task in TASKS}
    assert all((truth[task] >= 0).all() for task in TASKS)
    train = np.arange(len(frame))
    test = np.array([0], dtype=int)
    validation = np.array([], dtype=int)
    assert torch.cuda.is_available()
    device = torch.device("cuda:0")
    processor = AutoProcessor.from_pretrained(MODEL, revision=REVISION, min_pixels=128 * 128, max_pixels=384 * 384)
    processor.tokenizer.padding_side = "left"
    code_ids = {}
    for task in TASKS:
        ids = [processor.tokenizer.encode(letter, add_special_tokens=False) for letter in "ABCDEFGHIJ"[:len(classes[task])]]
        assert all(len(value) == 1 for value in ids) and len({value[0] for value in ids}) == len(ids)
        code_ids[task] = torch.tensor([value[0] for value in ids], device=device)

    required = sorted(set(train) | set(test) | set(validation))
    cached = {}
    audits = []
    for position, index in enumerate(required):
        row = frame.iloc[index]
        image_path = root / "05_gambar" / Path(row.image_path).name
        with Image.open(image_path) as original:
            image = original.convert("RGB")
            image.thumbnail((384, 384))
        common = (
            "Analisis sampul majalah Tempo tanpa memakai label anotasi. "
            f"Judul: {row.headline_verified}. Teks pendukung: {row.supporting_text_verified}. "
            f"Deskripsi visual: {descriptions[index]['deskripsi'][:1000]}. "
            f"Observasi sumber visual: {(reasons[index].get('sumber_visual') or '')[:250]}. "
            f"Alasan visual: {(reasons[index].get('alasan') or '')[:500]}."
        )
        cached[index] = {}
        for task in TASKS:
            options = "\n".join(
                f"{letter}: {label}: {DEFINITIONS[task][label]}"
                for letter, label in zip("ABCDEFGHIJ", classes[task])
            )
            question = {
                "task1_issue": "Pilih isu utama yang paling dominan.",
                "task2_domain_sumber": "Pilih domain SUMBER metafora visual-verbal, bukan isu politiknya.",
                "task3_primary_entity_type": "Pilih tipe entitas yang menjadi sasaran atau fokus kritik utama.",
            }[task]
            prompt = f"{common}\n{question}\n{options}\nJawab tepat satu kode huruf:"
            messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
            inputs = processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt")
            assert inputs["input_ids"].shape[1] <= 2048
            cached[index][task] = {name: value.cpu() for name, value in inputs.items()}
            audits.append({"sample_id": row.sample_id, "index": int(index), "task": task, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "image_sha256": sha(image_path), "tokens": int(inputs["input_ids"].shape[1])})
        if (position + 1) % 100 == 0:
            print("preprocessed", position + 1, flush=True)
    (OUT / "input_audit.jsonl").write_text("".join(json.dumps(row) + "\n" for row in audits))

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
    base = AutoModelForImageTextToText.from_pretrained(MODEL, revision=REVISION, quantization_config=quant, dtype=torch.float16, device_map={"": 0}, attn_implementation="sdpa")
    base.config.use_cache = False
    base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False})
    model = get_peft_model(base, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], bias="none", task_type=TaskType.CAUSAL_LM, revision=REVISION))
    trainable = [parameter for name, parameter in model.named_parameters() if parameter.requires_grad]
    assert trainable and all("lora_" in name for name, parameter in model.named_parameters() if parameter.requires_grad)
    for parameter in trainable:
        parameter.data = parameter.data.float()
    initial_state = capture_adapter(model)
    torch.save(initial_state, OUT / "initial_adapter_state.pt")

    def logits(index, task):
        inputs = {name: value.to(device) for name, value in cached[int(index)][task].items()}
        with torch.autocast("cuda", dtype=torch.float16):
            output = model(**inputs, logits_to_keep=1, use_cache=False, return_dict=True)
        selected = output.logits[:, -1, :].index_select(-1, code_ids[task]).float()
        assert selected.shape == (1, len(classes[task])) and torch.isfinite(selected).all()
        return selected

    def predict(indices):
        model.eval()
        result = {task: [] for task in TASKS}
        with torch.inference_mode():
            for index in indices:
                for task in TASKS:
                    result[task].append(logits(index, task).softmax(-1).cpu().numpy()[0])
        return {task: np.asarray(values) for task, values in result.items()}

    selected_epoch = 3
    seed_all(42001)
    optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", init_scale=128)
    criterion = nn.CrossEntropyLoss()
    rng = np.random.default_rng(42001)
    refit_history = []
    for epoch in range(1, selected_epoch + 1):
        model.train()
        order = rng.permutation(train)
        total = 0.0
        started = time.monotonic()
        for step, index in enumerate(order):
            if step % ACCUM == 0:
                optimizer.zero_grad(set_to_none=True)
            task = TASKS[(epoch + step) % len(TASKS)]
            target = torch.tensor([truth[task][index]], device=device)
            loss = criterion(logits(index, task), target)
            group_start = step // ACCUM * ACCUM
            group_size = min(ACCUM, len(order) - group_start)
            scaler.scale(loss / group_size).backward()
            total += float(loss.detach())
            if (step + 1) % ACCUM == 0 or step + 1 == len(order):
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(trainable, 1.0, error_if_nonfinite=True)
                scaler.step(optimizer)
                scaler.update()
        record = {"epoch": epoch, "loss": total / len(order), "seconds": time.monotonic() - started}
        refit_history.append(record)
        print("refit", json.dumps(record), flush=True)
        save_checkpoint("refit", epoch, model, optimizer, scaler, rng, refit_history)
    # In-sample smoke only: confirms persistence/reload, NOT accuracy.
    from peft import PeftModel
    before = predict(test)
    model.save_pretrained(OUT / "adapter", safe_serialization=True)
    del optimizer, scaler, model, base, trainable, initial_state
    gc.collect()
    torch.cuda.empty_cache()
    base = AutoModelForImageTextToText.from_pretrained(MODEL, revision=REVISION, quantization_config=quant, dtype=torch.float16, device_map={"": 0}, attn_implementation="sdpa")
    base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
    model = PeftModel.from_pretrained(base, OUT / "adapter", is_trainable=False)
    after = predict(test)
    differences = {task: float(np.max(np.abs(before[task] - after[task]))) for task in TASKS}
    assert all(value <= 1e-4 for value in differences.values()), differences
    artifact_hashes = {str(p.relative_to(OUT)): sha(p) for p in sorted((OUT / "adapter").iterdir()) if p.is_file()}
    result = dict(schema="tempo-micro-e14-deployment-result-v1", status="complete", version="micro-e14-qlora-v1",
        train_samples=len(train), epochs=selected_epoch, refit_history=refit_history,
        seconds=time.monotonic()-run_started, data_sha256=sha(csv_path),
        protocol_sha256=sha(Path("/kaggle/working/deployment_protocol.json")), source_sha256=sha(Path(__file__)),
        input_audit_sha256=sha(OUT / "input_audit.jsonl"),
        artifacts=artifact_hashes, classes=classes, deployment_benchmark="Not Evaluated",
        smoke=dict(kind="in-sample persistence/reload parity only, NOT benchmark", samples=len(test),
                   max_probability_difference=differences, probabilities={t: after[t].tolist() for t in TASKS}),
        gpu_name=torch.cuda.get_device_name(0), peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(0))
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("DEPLOYMENT_COMPLETE", json.dumps(result), flush=True)



def capture_adapter(model):
    return {name: value.detach().cpu().clone() for name, value in model.named_parameters() if value.requires_grad}


def restore_adapter(model, state):
    parameters = {name: value for name, value in model.named_parameters() if value.requires_grad}
    assert set(parameters) == set(state)
    with torch.no_grad():
        for name, value in state.items():
            parameter = parameters[name]
            assert parameter.shape == value.shape
            parameter.copy_(value.to(device=parameter.device, dtype=parameter.dtype))
    assert all(torch.equal(parameters[name].detach().cpu(), value) for name, value in state.items())


def save_checkpoint(phase, epoch, model, optimizer, scaler, rng, history):
    payload = {"phase": phase, "epoch": epoch, "adapter": capture_adapter(model),
               "optimizer": optimizer.state_dict(), "scaler": scaler.state_dict(),
               "numpy_rng": rng.bit_generator.state, "torch_rng": torch.get_rng_state(),
               "cuda_rng": torch.cuda.get_rng_state_all(), "python_rng": random.getstate(),
               "history": history, "protocol_sha256": sha(Path("/kaggle/working/deployment_protocol.json")),
               "source_sha256": sha(Path(__file__)), "deployment": True}
    temporary = OUT / f"{phase}_checkpoint.tmp"
    torch.save(payload, temporary)
    temporary.replace(OUT / f"{phase}_checkpoint.pt")
    (OUT / "progress.json").write_text(json.dumps({"phase":phase, "epoch":epoch, "fold":FOLD,
                                                  "history":history, "status":"running"},indent=2))


if __name__ == "__main__":
    main()
