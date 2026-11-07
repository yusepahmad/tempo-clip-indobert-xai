# Keputusan MICRO-E07 Joint QLoRA Smoke

**Status:** selesai — no-go untuk full five-fold

Kaggle version 4 menyelesaikan training, pemilihan epoch, reset adapter LoRA,
refit, dan inferensi test setelah bug reload state bitsandbytes diperbaiki.

## Hasil test smoke

| Task | Micro-F1 |
| --- | ---: |
| Task 1 | 0,6250 |
| Task 2 | 0,5417 |
| Task 3 | 0,4583 |
| Minimum | 0,4583 |

Hasil berasal dari 24 sampel outer-test fold 1, bukan 740 OOF. Karena minimum
smoke lebih rendah daripada minimum OOF MICRO-E11 (`0,5324`), E07 tidak
dipromosikan dan tidak dijalankan ke lima fold penuh. Skor validation Task 3
`0,7083` pada epoch 1 tidak boleh dipakai sebagai klaim target karena hanya
berasal dari 24 sampel inner-validation dan dua task lain tetap di bawah 0,70.

Artefak `predictions.csv` berisi 24 ID unik; Micro-F1 dihitung ulang dan cocok
dengan `result.json`. Hash `input_audit.jsonl` serta `predictions.csv` juga
cocok dengan nilai yang direkam oleh job Kaggle.
