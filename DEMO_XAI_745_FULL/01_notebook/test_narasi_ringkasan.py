"""Ringkasan awam tiga task dan penjelasan task pilihan (plan 2026-10-06-narasi-ringkasan-penjelasan)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02_web_demo"))
from explanation_evidence import explain, ringkas

T1, T2, T3 = "task1_issue", "task2_domain_sumber", "task3_primary_entity_type"
PRED = {T1: {"prediksi": "election_and_political_competition", "probabilitas": .33},
        T2: {"prediksi": "PERMAINAN_KONTES", "probabilitas": .39},
        T3: {"prediksi": "individual", "probabilitas": .38}}
DEFS = {"PERMAINAN_KONTES": "Domain sumber berupa permainan atau kompetisi."}
CATATAN = {"entitas": "Akbar Tanjung", "sumber_metafora": "Sudut ruang dan posisi fisik terjepit",
           "pemetaan_makna": "Posisi di sudut menggambarkan tekanan politik."}
LABEL = {T1: "law_and_justice", T2: "BENCANA_JERAT", T3: "individual"}
KEPALA = lambda cam: ("kepala sampul (logo dan judul kecil)", 1, {})
TENGAH = lambda cam: ("bagian tengah (umumnya ilustrasi)", 1, {})
OBJEK = ("wajah", "orang", "tokoh di", "logo tempo terlihat", "ilustrasi akbar")


class Ringkasan(unittest.TestCase):
    def test_tiga_aspek_dan_anotator(self):
        r = ringkas(PRED, "AKBAR TERPOJOK SIAPA SENANG", label=LABEL, catatan=CATATAN)
        teks = r["paragraf"]
        self.assertIn("pemilu dan persaingan politik", teks)       # Task 1, '&' -> 'dan'
        self.assertIn("seorang tokoh", teks)                       # Task 3
        self.assertIn("perumpamaan permainan", teks)               # Task 2
        self.assertIn("kiasan semacam ini biasanya", teks)         # makna umum, bukan klaim sampul
        self.assertEqual(r["keyakinan"], "belum_dikalibrasi")
        self.assertIn("Skor ketiga task belum dikalibrasi", teks)
        self.assertEqual([b["asal"] for b in r["bagian"]], ["MODEL", "ANOTATOR"])
        self.assertIn("Hukum & Peradilan", r["bagian"][1]["teks"])
        self.assertIn("Bencana & Jerat", r["bagian"][1]["teks"])
        self.assertNotIn("Perorangan", r["bagian"][1]["teks"])     # aspek yang sama tidak disebut berbeda
        self.assertIn("tekanan politik", r["bagian"][1]["teks"])

    def test_unggahan_tanpa_anotator_dan_akronim(self):
        pred = {T1: {"prediksi": "economy_business_and_state_enterprise", "probabilitas": .7},
                T2: {"prediksi": "NON_METAFORA", "probabilitas": .65}, T3: {"prediksi": "business", "probabilitas": .8}}
        r = ringkas(pred, "JUDUL")
        self.assertIn("ekonomi, bisnis dan BUMN", r["paragraf"])
        self.assertIn("tanpa kiasan", r["paragraf"])
        self.assertEqual(r["keyakinan"], "belum_dikalibrasi")
        self.assertEqual([b["asal"] for b in r["bagian"]], ["MODEL"])

    def test_label_semua_sama(self):
        label = {t: PRED[t]["prediksi"] for t in PRED}
        r = ringkas(PRED, "X Y", label=label)
        self.assertIn("sejalan dengan label anotator", r["paragraf"])


class Penjelasan(unittest.TestCase):
    def test_terikat_task_dan_berbeda_dari_ringkasan(self):
        kata = [{"kata": "AKBAR", "kontribusi": .021}, {"kata": "SIAPA", "kontribusi": -.023},
                {"kata": "SENANG", "kontribusi": .02}]
        r = explain(PRED, T2, kata, CATATAN, 1, "AKBAR TERPOJOK SIAPA SENANG", DEFS, KEPALA, label=LABEL)
        self.assertEqual([b["label"] for b in r["blok"]], ["Mengapa Permainan & Kontes?", "Arti kelas ini", "Catatan anotator"])
        mengapa = r["blok"][0]["teks"]
        self.assertIn("‘AKBAR’ dan ‘SENANG’ paling mendorong", mengapa)
        self.assertIn("‘SIAPA’ justru menariknya", mengapa)
        self.assertIn("bagian atas sampul", mengapa)
        self.assertNotIn("isu utama", r["paragraf"].lower())
        self.assertNotIn("sasaran kritik", r["paragraf"].lower())
        self.assertTrue(any("Label anotator berbeda (Bencana & Jerat)" in c for c in r["cek"]))
        self.assertTrue(any("rendah" in c for c in r["cek"]))
        self.assertNotEqual(r["paragraf"], ringkas(PRED, "AKBAR TERPOJOK SIAPA SENANG", LABEL, CATATAN)["paragraf"])
        self.assertFalse(any(o in r["paragraf"].lower() for o in OBJEK))
        # Peringatan tidak lagi diulang di setiap kalimat.
        self.assertNotIn("tidak mengidentifikasi objek", r["paragraf"])
        self.assertEqual(r["paragraf"].count("belum dikalibrasi"), 1)

    def test_tanpa_kata_positif(self):
        kata = [{"kata": "GULA-GULA", "kontribusi": -.003}, {"kata": "DEMO", "kontribusi": -.011},
                {"kata": "BURUH", "kontribusi": -.015}]
        pred = {**PRED, T2: {"prediksi": "PERMAINAN_KONTES", "probabilitas": .46}}
        r = explain(pred, T2, kata, None, 1, "GULA-GULA DEMO BURUH", DEFS, KEPALA)
        self.assertIn("Tidak ada kata di judul yang mendorong pilihan ini", r["blok"][0]["teks"])
        self.assertIn("Tidak ada kata dengan kontribusi positif untuk kelas yang dijelaskan.", r["cek"])
        self.assertFalse(any(b["asal"] == "ANOTATOR" for b in r["blok"]))

    def test_zona_tengah_tanpa_peringatan_zona(self):
        pred = {**PRED, T2: {"prediksi": "PERMAINAN_KONTES", "probabilitas": .8}}
        r = explain(pred, T2, [{"kata": "KONTES", "kontribusi": .1}], None, 1, "JUDUL KONTES", DEFS, TENGAH)
        self.assertIn("bagian tengah sampul, tempat ilustrasi biasanya berada.", r["blok"][0]["teks"])
        self.assertFalse(any("luar bagian tengah" in c for c in r["cek"]))


class AuditKode(unittest.TestCase):
    """Temuan audit kode 6 Okt (plan 2026-10-06-audit-bug-kode)."""
    def test_catatan_anotator_hanya_milik_task(self):
        r1 = explain(PRED, T1, [], CATATAN, None, "A B", {}, KEPALA, label=LABEL)
        teks1 = r1["paragraf"]
        self.assertNotIn("sumber kiasannya", teks1)
        self.assertNotIn("Akbar Tanjung", teks1)
        self.assertIn("Label anotator untuk aspek ini berbeda: Hukum & Peradilan", teks1)
        r3 = explain(PRED, T3, [], CATATAN, None, "A B", {}, KEPALA, label=LABEL)
        self.assertIn("Akbar Tanjung", r3["paragraf"])
        self.assertNotIn("sumber kiasannya", r3["paragraf"])
        ann = [e for e in r3["bukti"] if e["source"] == "ANOTATOR"]
        self.assertEqual(ann[0]["task_id"], T3)
        self.assertEqual(set(ann[0]["value"]), {"entitas"})

    def test_peta_datar_tanpa_klaim_zona(self):
        import numpy as np
        r = explain(PRED, T2, [{"kata": "A", "kontribusi": .1}], None, np.zeros((7, 7)), "A B", DEFS, KEPALA)
        self.assertNotIn("bagian atas sampul", r["paragraf"])

    def test_kata_kembar_dan_kutip_ganda(self):
        kata = [{"kata": "JANJI", "kontribusi": .2}, {"kata": "JANJI", "kontribusi": .1}, {"kata": "'Suap'", "kontribusi": -.1}]
        r = explain(PRED, T2, kata, None, None, "JANJI JANJI 'Suap'", DEFS, KEPALA)
        self.assertIn("kata ‘JANJI’ paling mendorong", r["paragraf"])
        self.assertIn("‘Suap’ justru", r["paragraf"])

    def test_label_sebagian_dan_akronim_definisi(self):
        r = ringkas(PRED, "X", label={T2: "PERMAINAN_KONTES", T1: "nan"})
        self.assertIn("sejalan dengan label anotator untuk domain sumber metafora", r["paragraf"])
        self.assertNotIn("ketiga aspek", r["paragraf"])
        pred = {**PRED, T1: {"prediksi": "economy_business_and_state_enterprise", "probabilitas": .5}}
        r = explain(pred, T1, [], None, None, "A B", {"economy_business_and_state_enterprise": "BUMN dan bisnis negara."}, KEPALA)
        self.assertIn("berarti: BUMN dan bisnis negara.", r["paragraf"])


if __name__ == "__main__":
    unittest.main()
