"""Regression tests for request evidence, OCR selector and persisted batch."""
import sys, tempfile, time, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"02_web_demo"))
from ocr_headline import pilih_headline, _layak
from explanation_evidence import explain
from batch_jobs import BatchJobs

class Revisions(unittest.TestCase):
    def test_batch_utf8_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            jobs=BatchJobs(directory,lambda *args: {})
            job=jobs.create([{"name":"Ā — judul Indonesia", "status":"needs_review"}],"task1_issue","occlusion")
            self.assertEqual(jobs.get(job["id"])["items"][0]["name"],"Ā — judul Indonesia")
            self.assertIn("Ā",(Path(directory)/job["id"]/"manifest.json").read_text(encoding="utf-8"))
            jobs.pool.shutdown()
    def test_logo_multiline(self):
        def b(t,y,h=40):return {"teks":t,"atas":y,"kiri":10,"tinggi":h,"yakin":.95}
        blocks=[b("TEMPO5",10,150),b("CUKAI ABAL-ABAL",750),b("ROKOK ILEGAL",795)]
        r=pilih_headline(blocks,1000)
        self.assertEqual(r["headline"],"CUKAI ABAL-ABAL ROKOK ILEGAL")
        self.assertIn("TEMPO5",r["semua"])
        self.assertFalse(_layak(b("TEMPO 5",10),1000))
        self.assertEqual(r["status_headline"],"perlu_pemeriksaan")
        for t in ("TEMPE","MOMEN","NONTON"):self.assertTrue(_layak(b(t,800),1000))
    def test_five_strategies_and_task_binding(self):
        task="task2_domain_sumber";pred={task:{"prediksi":"PERMAINAN_KONTES","probabilitas":.8}}
        defs={"PERMAINAN_KONTES":{"definisi":"Konsep permainan."}}
        word=[{"kata":"KONTES","kontribusi":.1}]
        zone=lambda x:("tengah sampul (ilustrasi)",1,{})
        cases=[(word,None,None,"bukti_teks"),([],None,1,"bukti_visual"),([],{"sumber_metafora":"Manusia"},None,"perbandingan_anotasi"),([],None,None,"penjelasan_kelas"),(word,None,1,"bukti_gabungan_terbatas")]
        for words,notes,cam,strategy in cases:
            r=explain(pred,task,words,notes,cam,"JUDUL KONTES",defs,zone)
            self.assertEqual(r["strategi"],strategy)
            self.assertEqual(r["task_id"],task)
            self.assertNotIn("isu utama",r["paragraf"].lower())
            self.assertTrue(all(x.get("task_id",task)==task for x in r["bukti"]))
        r=explain(pred,task,[{"kata":"BURUH","kontribusi":-.1}],None,None,"DEMO BURUH",defs,zone)
        self.assertTrue(r["alasan_ragu"])
        self.assertFalse(any(x["source"]=="ANOTATOR" for x in r["bukti"]))
    def test_batch_error_isolation_review_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            def runner(j,x,p):
                if x["name"]=="bad":raise ValueError("broken")
                if not x.get("reviewed"):return {"status":"needs_review","headline":"OCR JUDUL"}
                return {"status":"success","result":{"headline":x["headline"]}}
            jobs=BatchJobs(directory,runner)
            j=jobs.create([{"name":"bad","status":"queued"},{"name":"good","status":"queued"}],"task1_issue","occlusion")
            jobs.start(j["id"])
            for _ in range(200):
                if j["id"] not in jobs.active:break
                time.sleep(.01)
            j=jobs.get(j["id"]);self.assertEqual([x["status"] for x in j["items"]],["failed","needs_review"])
            jobs.review(j["id"],1,"MANUAL FINAL","")
            for _ in range(200):
                if j["id"] not in jobs.active:break
                time.sleep(.01)
            j=jobs.get(j["id"]);self.assertEqual(j["items"][1]["result"]["headline"],"MANUAL FINAL")
            self.assertIn("MANUAL FINAL",jobs.export_csv(j))
            jobs.pool.shutdown()
            j["status"]="running";j["items"][0]["status"]="running";jobs.save(j)
            restored=BatchJobs(directory,runner);self.assertEqual(restored.get(j["id"])["status"],"interrupted");restored.pool.shutdown()

if __name__=="__main__":unittest.main()
