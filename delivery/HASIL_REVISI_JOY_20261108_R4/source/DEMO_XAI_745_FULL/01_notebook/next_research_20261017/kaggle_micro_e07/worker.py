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
os.environ["HF_HOME"] = "/kaggle/working/.cache/huggingface"

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
OUT.mkdir(exist_ok=True)
# One epoch alternates tasks, so each head sees roughly one third of the
# training set. Twelve joint epochs equal about four effective passes/task.
MAX_EPOCHS = 2 if SMOKE else 12
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
    task1 = truth["task1_issue"]
    counts = np.bincount(task1)
    strat = np.array([value if counts[value] >= 5 else -1 for value in task1])
    train, test = list(StratifiedKFold(5, shuffle=True, random_state=42).split(np.zeros(740), strat))[FOLD - 1]
    inner, validation = train_test_split(train, test_size=0.2, stratify=strat[train], random_state=42 + FOLD)
    if SMOKE:
        rng = np.random.default_rng(4200 + FOLD)
        inner = np.sort(rng.choice(inner, 48, replace=False))
        validation = np.sort(rng.choice(validation, 24, replace=False))
        test = np.sort(rng.choice(test, 24, replace=False))
        train = np.concatenate((inner, validation))
    assert not set(train) & set(test) and not set(inner) & set(validation)

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
    initial_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}

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

    seed_all(42 + FOLD)
    optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", init_scale=128)
    criterion = nn.CrossEntropyLoss()
    rng = np.random.default_rng(42 + FOLD)
    best = -1.0
    selected_epoch = 1
    best_state = None
    history = []
    stale = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        order = rng.permutation(inner)
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
        probabilities = predict(validation)
        scores = {task: float(f1_score(truth[task][validation], probabilities[task].argmax(1), average="micro")) for task in TASKS}
        score = min(scores.values())
        record = {"epoch": epoch, "loss": total / len(order), "validation_micro_f1": scores, "minimum": score, "seconds": time.monotonic() - started}
        history.append(record)
        print(json.dumps(record), flush=True)
        if score > best + 1e-9:
            best, selected_epoch, stale = score, epoch, 0
            best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}
        else:
            stale += 1
        if stale >= 2:
            break
    assert best_state
    # Refit from the exact initial adapter on all outer-training rows for the
    # inner-selected number of epochs. Outer-test labels remain untouched.
    # Restore only trainable LoRA tensors. Loading the complete quantized
    # state_dict re-introduces bitsandbytes auxiliary keys (absmax/quant_map)
    # that PeftModel correctly rejects as unexpected on reload.
    named_parameters = dict(model.named_parameters())
    assert set(initial_state).issubset(named_parameters)
    with torch.no_grad():
        for name, value in initial_state.items():
            parameter = named_parameters[name]
            parameter.copy_(value.to(device=parameter.device, dtype=parameter.dtype))
    del optimizer, scaler
    optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", init_scale=128)
    rng = np.random.default_rng(42000 + FOLD)
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
    final_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items() if "lora_" in name}
    probabilities = predict(test)
    predictions = {task: probabilities[task].argmax(1) for task in TASKS}
    micro = {task: float(f1_score(truth[task][test], predictions[task], average="micro")) for task in TASKS}

    output = pd.DataFrame({"sample_id": frame.sample_id.iloc[test].to_numpy(), "index": test, "fold": FOLD})
    for task in TASKS:
        output[task + "_truth"] = np.asarray(classes[task])[truth[task][test]]
        output[task + "_pred"] = np.asarray(classes[task])[predictions[task]]
        for class_index, label in enumerate(classes[task]):
            output[f"{task}_p_{label}"] = probabilities[task][:, class_index]
    output.to_csv(OUT / "predictions.csv", index=False)
    torch.save(final_state, OUT / "adapter_state.pt")
    result = {
        "status": "complete", "smoke": SMOKE, "fold": FOLD,
        "model_contract": "one shared Qwen3-VL LoRA adapter with three prompted objectives",
        "selected_epoch": selected_epoch, "micro_f1": micro,
        "minimum_micro_f1": min(micro.values()), "all_tasks_at_least_0_70": min(micro.values()) >= 0.70,
        "samples": len(test), "train_samples": len(inner), "validation_samples": len(validation),
        "history": history, "refit_history": refit_history, "classes": classes, "data_sha256": sha(csv_path),
        "input_audit_sha256": sha(OUT / "input_audit.jsonl"), "predictions_sha256": sha(OUT / "predictions.csv"),
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("COMPLETE", json.dumps(micro), flush=True)
    del optimizer, scaler, model
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
