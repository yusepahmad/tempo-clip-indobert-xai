"""Serving checkpoint asli E42 untuk dataset dan unggahan baru."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from label_display import nama_task, tampil
from tail_rich_engine import TailRichEngine, sha
from xai_core import TASKS

ROOT = Path(__file__).resolve().parent.parent
BACKEND = "e42-tail-grid"
VERSION = "e42-tail-grid-v1"


class E42Engine(TailRichEngine):
    """E42 outer-fold serving tanpa melatih ulang checkpoint saat startup."""

    def __init__(self):
        torch.set_num_threads(max(1, min(8, int(os.environ.get("TEMPO_CPU_THREADS", "4")))))
        self.assets = Path(os.environ.get("TEMPO_E42_ASSET_DIR") or ROOT / "06_models" / VERSION)
        self.manifest = __import__("json").loads((ROOT / "06_models" / VERSION / "manifest.json").read_text())
        for name, digest in self.manifest["asset_sha256"].items():
            path = self.assets / name
            if not path.is_file() or sha(path) != digest:
                raise ValueError("Artefak E42 tidak cocok atau belum tersedia: " + name)
        dataset = ROOT / "03_data" / "DATASET_740_TASK2_DOMAIN.csv"
        if sha(dataset) != self.manifest["dataset_sha256"]:
            raise ValueError("Dataset tidak cocok dengan checkpoint E42")
        self.df = pd.read_csv(dataset).fillna("")
        self.tasks = list(TASKS)
        spec = importlib.util.spec_from_file_location("_tempo_e42_model", ROOT / "01_notebook/e42_tail_grid/tail_model.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._tm = module
        self._models = {}
        self._fold_for_id = {}
        covered = set()
        for fold in range(1, 6):
            cp = torch.load(self.assets / f"fold{fold}.pt", map_location="cpu", weights_only=True)
            if cp["cache_manifest_sha256"] != self.manifest["cache_manifest_sha256"]:
                raise ValueError("Checkpoint E42 memakai cache yang berbeda")
            maps = cp["classes"]
            if fold == 1:
                self.maps = maps
                self.ncls = {task: len(maps[task]) for task in self.tasks}
            if maps != self.maps:
                raise ValueError("Label checkpoint E42 tidak konsisten")
            train, test = set(cp["train_indices"]), set(cp["test_indices"])
            if train & test or train | test != set(range(len(self.df))) or covered & test:
                raise ValueError("Split outer-fold E42 tidak sah")
            covered |= test
            for index in test:
                self._fold_for_id[str(self.df.iloc[index].sample_id)] = fold
            model = module.TailMTL(self.ncls, self.assets)
            model.load_state_dict(cp["state_dict"], strict=True)
            model.eval()
            for parameter in model.parameters():
                parameter.requires_grad_(False)
            self._models[fold] = model
        if covered != set(range(740)):
            raise ValueError("Cakupan checkpoint E42 harus 740 ID unik")
        self.y = {
            task: self.df[task].map({label: i for i, label in enumerate(self.maps[task])}).to_numpy()
            for task in self.tasks
        }
        self.cache = dict(np.load(self.assets / "front_cache.npz", allow_pickle=False))
        if self.cache["sample_ids"].tolist() != self.df.sample_id.tolist():
            raise ValueError("Urutan cache E42 berbeda dari dataset")
        self._visual = self._front = self._tok = self._preprocess = None
        self._active = []
        self._context = None
        self.ready = True
        self.model = None
        self.dim_img = 1536
        self.X = np.hstack([self.cache["visual"] * 2, self.cache["base_mean"]]).astype(np.float32)

    def description(self):
        return dict(
            self.manifest,
            ready=True,
            tasks=self.tasks,
            device="cpu",
            dataset_protocol="checkpoint outer-fold E42 yang tidak melatih ID dataset tersebut",
            upload_protocol="rerata probabilitas lima checkpoint E42; belum dievaluasi terpisah",
            upload_requires=[],
            batch_upload_supported=True,
            text_xai="perturbasi headline; supporting text tetap",
        )

    @staticmethod
    def rich_text(headline, supporting, _fields=None):
        return f"{headline} [SEP] {supporting}".strip()

    def prepare_analysis(self, image_path, headline, supporting, sample_id=None, fields=None, cancel=None):
        if cancel:
            cancel()
        if sample_id:
            if sample_id not in self._fold_for_id:
                raise ValueError("ID dataset tidak dikenal")
            index = int(self.df.index[self.df.sample_id == sample_id][0])
            if sha(image_path) != self.df.iloc[index].image_sha256:
                raise ValueError("Gambar dataset berbeda dari sumber evaluasi")
            self._active = [self._fold_for_id[sample_id]]
            row = self.df.iloc[index]
            visual = self.cache["visual"][index].copy()
            canonical = headline == str(row.headline_verified) and supporting == str(row.supporting_text_verified)
            if canonical:
                ix = np.array([index])
                hidden, attention, pool, _ = self._tm.batch_tensors(self.cache, ix, "cpu")
            else:
                hidden, attention, pool = self._front_inputs([self.rich_text(headline, supporting)])
            protocol = f"dataset outer-fold E42 {self._active[0]}; held-out ID; " + (
                "input canonical" if canonical else "teks diedit; bukan benchmark baru"
            )
        else:
            self._active = list(range(1, 6))
            self._ensure_visual()
            with torch.no_grad():
                encoded = self._visual(self._images(image_path))
                encoded = torch.nn.functional.normalize(encoded.float(), p=2, dim=1)
                visual = encoded.reshape(-1).numpy()
            hidden, attention, pool = self._front_inputs([self.rich_text(headline, supporting)])
            protocol = "unggahan baru; ensemble probabilitas lima fold E42; belum dievaluasi terpisah"
        with torch.no_grad():
            vectors = {
                fold: self._models[fold].features(
                    hidden, attention, pool, torch.tensor(visual).reshape(1, -1)
                )[0].numpy()
                for fold in self._active
            }
        self._context = dict(
            image_path=Path(image_path), headline=headline, supporting=supporting,
            fields={}, visual=visual, vectors=vectors, protocol=protocol, sample_id=sample_id,
        )
        self.model = self._models[self._active[0]].head
        if cancel:
            cancel()
        vector = vectors[self._active[0]]
        return visual, vector[1536:], vector

    def _result(self, probabilities):
        output = {}
        for task in self.tasks:
            probability = probabilities[task]
            order = np.argsort(probability)[::-1]
            label = self.maps[task][int(order[0])]
            output[task] = dict(
                nama_task=TASKS[task], nama_task_mudah=nama_task(task),
                prediksi=label, prediksi_tampil=tampil(label), probabilitas=float(probability[order[0]]),
                semua=[dict(kelas=self.maps[task][int(i)], kelas_tampil=tampil(self.maps[task][int(i)]), prob=float(probability[i])) for i in order],
                backend=BACKEND, model_version=VERSION, score_kind="softmax_uncalibrated",
                score_label="Skor E42 (belum dikalibrasi)", evaluation_mode=self._context["protocol"],
                evaluation=dict(protocol=self.manifest["evaluation"]["protocol"], samples=740,
                                macro_f1=self.manifest["evaluation"]["macro_f1"][task]),
            )
        return output

    def xai_contract(self, task):
        return dict(
            model_version=VERSION, task=task, folds=self._active, evaluation_mode=self._context["protocol"],
            visual_method="CLIP-L14 full/crop gradient × activation melalui checkpoint E42 aktif",
            text_method="occlusion headline melalui IndoBERT dan trained tail E42; supporting text tetap",
            score_kind="softmax_uncalibrated",
            limitation="Sensitivitas model, bukan bukti kausal; ensemble unggahan belum menjadi benchmark baru.",
        )
