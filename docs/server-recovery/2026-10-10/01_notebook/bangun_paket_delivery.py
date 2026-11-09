"""Bangun ZIP delivery dari source (plan docs/plans/2026-10-06-paket-delivery-final.md).

    venv/bin/python 01_notebook/bangun_paket_delivery.py [folder_keluaran]

Isi ZIP: folder DEMO_XAI_745_FULL/ tanpa environment, cache, job lokal dan
screenshot smoke selain run final, ditambah DELIVERY_MANIFEST.json (SHA256 tiap
berkas). Setelah ditulis, ZIP diperiksa: CRC, hash tiap berkas = manifest = source.
"""
import hashlib, json, sys, time, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMA = "TEMPO_XAI_DELIVERY_WEEK3_20261006"
KELUAR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "dist"
SMOKE_FINAL = "browser_smoke_20261006_audit"
DIKECUALIKAN = {
    "venv/": "environment lokal (dibuat ulang oleh setup)",
    "__pycache__/": "bytecode Python",
    ".pytest_cache/": "cache test",
    "02_web_demo/_cache/": "cache heatmap/unggahan lokal",
    "02_web_demo/_jobs/": "job batch lokal",
    "SERVER_HANDOFF_MANIFEST.json": "manifest handoff 6 Okt pagi; tidak lagi cocok dengan source",
    "04_hasil_eksperimen/revisi_week3/browser_smoke_*/ (kecuali run final)":
        f"screenshot smoke lama; JSON semua run disertakan, screenshot hanya {SMOKE_FINAL}",
}


def ikut(rel: str) -> bool:
    parts = rel.split("/")
    if parts[0] in ("venv", ".pytest_cache") or "__pycache__" in parts:
        return False
    if rel.startswith(("02_web_demo/_cache/", "02_web_demo/_jobs/")) or rel == "SERVER_HANDOFF_MANIFEST.json":
        return False
    if rel.endswith((".pyc", ".tmp")):
        return False
    if (len(parts) > 3 and parts[:2] == ["04_hasil_eksperimen", "revisi_week3"]
            and parts[2].startswith("browser_smoke_") and parts[2] != SMOKE_FINAL):
        return False
    return True


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    berkas = sorted(p for p in ROOT.rglob("*") if p.is_file() and ikut(p.relative_to(ROOT).as_posix()))
    isi = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in berkas}
    manifest = {"paket": NAMA, "dibuat": time.strftime("%Y-%m-%d %H:%M:%S"),
                "plan": "docs/plans/2026-10-06-paket-delivery-final.md",
                "jumlah_berkas": len(isi), "dikecualikan": DIKECUALIKAN,
                "berkas": {rel: {"sha256": sha(b), "bytes": len(b)} for rel, b in isi.items()}}
    mb = json.dumps(manifest, ensure_ascii=False, indent=1).encode("utf-8")
    KELUAR.mkdir(parents=True, exist_ok=True)
    zp = KELUAR / f"{NAMA}.zip"
    if zp.exists():
        zp.unlink()
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel, b in isi.items():
            st = (ROOT / rel).stat()
            zi = zipfile.ZipInfo(f"DEMO_XAI_745_FULL/{rel}", date_time=time.localtime(st.st_mtime)[:6])
            zi.compress_type = zipfile.ZIP_DEFLATED
            # Pertahankan izin (jalankan_linux.sh harus tetap dapat dieksekusi setelah unzip).
            zi.external_attr = ((st.st_mode & 0o777) | (0o111 if rel.endswith(".sh") else 0)) << 16
            z.writestr(zi, b)
        z.writestr("DEMO_XAI_745_FULL/DELIVERY_MANIFEST.json", mb)
    # Verifikasi: CRC, isi = manifest = source.
    with zipfile.ZipFile(zp) as z:
        assert z.testzip() is None, "CRC gagal"
        nama = set(z.namelist())
        m = json.loads(z.read("DEMO_XAI_745_FULL/DELIVERY_MANIFEST.json"))
        assert nama == {f"DEMO_XAI_745_FULL/{r}" for r in m["berkas"]} | {"DEMO_XAI_745_FULL/DELIVERY_MANIFEST.json"}
        for rel, info in m["berkas"].items():
            b = z.read(f"DEMO_XAI_745_FULL/{rel}")
            assert sha(b) == info["sha256"] == sha((ROOT / rel).read_bytes()), rel
    h = sha(zp.read_bytes())
    (KELUAR / f"{NAMA}.zip.sha256").write_text(f"{h}  {zp.name}\n")
    print(json.dumps({"zip": str(zp), "mb": round(zp.stat().st_size / 1e6, 1), "berkas": len(isi) + 1,
                      "sha256": h, "verifikasi": "CRC + hash isi = manifest = source lulus"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
