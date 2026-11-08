# Public export

This repository is a sanitized export of research source and analysis from server .31. Original server files remain unchanged. Credentials, coordinator control keys, participant registration, personal returned forms, runtime logs, environments, caches and large model blobs are not included. Research labels, folds, predictions and numeric metrics are preserved.

This is not a complete backup of the laptop or all private/model artifacts. Historical manifests inside source snapshots document their original scope; the current public analysis package has a separate rebuilt manifest.

## Published snapshot

- Public repository: https://github.com/yusepahmad/tempo-clip-indobert-xai
- R4 release: https://github.com/yusepahmad/tempo-clip-indobert-xai/releases/tag/v2026.11.08-r4
- ZIP: `TEMPO_REVISI_II_R4_PUBLIC_20261108.zip` (449,730,156 bytes).
- SHA-256: `a2c9a67f7ee02472f76a0581b364dfc96b6c7bd6584cb71a3cac5a090a8d2035`.
- Verified: 26 source tests, Run all of three notebooks from the extracted public ZIP, 2,421 manifest hashes and 234 metric rows from 78 sources. GitHub asset digests match local checksums; public access and checksum download were checked without authentication.
- Release tag points to the initial source snapshot; later main commits may update publication documentation. Snapshot R4 records 19/28 technical items complete; human evidence, actual Colab execution and the literal image+headline experiment were still pending.

## Current source after R4

Main includes the CLIP–IndoBERT rich256 web backend, pinned artifact manifest, preparation script, CPU dependency lock, serving tests and a credential-free public Colab launcher. This does not change the immutable R4 analysis snapshot or close missing Kaggle/human/actual-Colab evidence. Research model E42 and serving candidate RII_TAIL_RICH256 have distinct documented roles. See docs/WEB_RICH256.md and docs/STATUS_REVISI_TERKINI.md.
