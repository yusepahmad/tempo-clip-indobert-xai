"""Pesan gagal item batch tidak memuat path absolut server (plan 2026-10-06-sinkronisasi-docs-dan-catatan-minor)."""
import json, sys, tempfile, time, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"02_web_demo"))
from PIL import UnidentifiedImageError
from batch_jobs import BatchJobs, pesan_gagal

class BatchErrorMessage(unittest.TestCase):
    def test_helper(self):
        self.assertEqual(pesan_gagal(UnidentifiedImageError("cannot identify image file '/srv/x/_jobs/ab/input_0.bin'")),
                         "Gambar tidak terbaca: format berkas tidak dikenali")
        self.assertEqual(pesan_gagal(OSError("tidak ada '/home/u/_jobs/ab/input_1.bin' atau C:\\Users\\u\\a.png")),
                         "OSError: tidak ada 'input_1.bin' atau a.png")
        self.assertEqual(pesan_gagal(ValueError("judul kosong/invalid, skor 4/5")),"ValueError: judul kosong/invalid, skor 4/5")
    def test_manifest_and_csv_without_server_path(self):
        with tempfile.TemporaryDirectory() as directory:
            def runner(job,item,folder):
                raise UnidentifiedImageError(f"cannot identify image file '{folder/'input_0.bin'}'")
            jobs=BatchJobs(directory,runner)
            job=jobs.create([{"name":"rusak.png","status":"queued"}],"task2_domain_sumber","occlusion")
            jobs.start(job["id"])
            for _ in range(100):
                if jobs.get(job["id"])["status"]!="queued" and job["id"] not in jobs.active:break
                time.sleep(.05)
            j=jobs.get(job["id"]);item=j["items"][0]
            self.assertEqual(item["status"],"failed")
            self.assertEqual(item["error"],"Gambar tidak terbaca: format berkas tidak dikenali")
            self.assertNotIn(directory,json.dumps(j))
            self.assertNotIn(directory,jobs.export_csv(j))
            jobs.pool.shutdown()

if __name__=="__main__":
    unittest.main()
