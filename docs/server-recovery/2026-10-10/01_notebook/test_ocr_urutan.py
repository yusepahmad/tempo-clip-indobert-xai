"""Urutan baca OCR dan penyambungan judul (plan 2026-10-06-audit-ocr-urutan-kata)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02_web_demo"))
from ocr_headline import pilih_headline


def b(teks, atas, kiri, kanan, tinggi, yakin=.95):
    return {"teks": teks, "atas": atas, "kiri": kiri, "kanan": kanan, "bawah": atas + tinggi,
            "tinggi": tinggi, "yakin": yakin}


H = 780
TEASER = [b("YANG LENYAP DI", 13, 125, 287, 20), b("MENTERI BARU", 13, 333, 481, 20),
          b("MUSEUM BAHARI", 30, 122, 290, 24), b("DEMI PEMILU", 30, 342, 474, 24),
          b("TEMPO", 50, 90, 527, 125)]


class UrutanBaca(unittest.TestCase):
    def test_teaser_dua_kolom_tidak_menyelip_dan_deck_lebih_dulu(self):
        blok = TEASER + [b("KISRUH", 234, 62, 352, 100), b("BERAS", 406, 66, 328, 100),
                         b("KEPUTUSAN PEMERINTAH", 515, 68, 273, 20), b("MEMBUKA KERAN IMPOR", 535, 68, 326, 22)]
        r = pilih_headline(blok, H)
        self.assertEqual(r["headline"], "KISRUH BERAS")
        self.assertEqual(r["pendukung"], "KEPUTUSAN PEMERINTAH MEMBUKA KERAN IMPOR; "
                                         "YANG LENYAP DI MUSEUM BAHARI; MENTERI BARU DEMI PEMILU")

    def test_kolom_bercelah_sempit_tidak_digabung_sebaris(self):
        blok = [b("BARTER POLITIK", 14, 509, 733, 36), b("KEMATIAN MISTERIUS", 18, 94, 390, 32),
                b("PENGACARA LINGKUNGAN", 45, 65, 421, 39), b("AMENDEMEN KONSTITUSI", 48, 450, 792, 32),
                b("TERORIS", 544, 438, 770, 78)]
        r = pilih_headline(blok, 1000)
        self.assertEqual(r["pendukung"], "KEMATIAN MISTERIUS PENGACARA LINGKUNGAN; BARTER POLITIK AMENDEMEN KONSTITUSI")

    def test_potongan_paragraf_rata_kiri_kanan_kembali_ke_barisnya(self):
        blok = [b("MAKAR", 300, 50, 400, 80),
                b("Mengapa Tim Barito tak", 420, 50, 260, 20), b("mampu", 446, 50, 110, 9),
                b("mempertahankan", 442, 114, 300, 18),
                b("posisi Setya Novanto sebagai", 464, 50, 500, 20), b("Ketua DPR.", 486, 50, 200, 20)]
        r = pilih_headline(blok, 1000)
        self.assertEqual(r["pendukung"], "Mengapa Tim Barito tak mampu mempertahankan posisi Setya Novanto sebagai Ketua DPR.")

    def test_kata_sebaris_diurutkan_kiri_ke_kanan(self):
        # "SENANG" (kanan) sedikit lebih tinggi posisinya daripada "SIAPA" (kiri) padahal sebaris.
        blok = [b("SENANG", 497, 300, 520, 60), b("SIAPA", 503, 60, 280, 60), b("AKBAR", 420, 60, 300, 62)]
        self.assertEqual(pilih_headline(blok, H)["headline"], "AKBAR SIAPA SENANG")

    def test_baris_lanjutan_berkeyakinan_rendah_disambung_dan_ditandai(self):
        blok = TEASER + [b("TM MAWAR DAN", 271, 63, 557, 60, .54), b("RUSUH SARIA", 318, 68, 551, 66, .26),
                         b("Pr75", 163, 339, 557, 64, .01)]
        r = pilih_headline(blok, H)
        self.assertEqual(r["headline"], "TM MAWAR DAN RUSUH SARIA")
        self.assertIn("RUSUH SARIA", r["catatan"])

    def test_sisa_logo_dan_tagline_berjarak_tidak_masuk(self):
        blok = [b("sTEMPO", 40, 27, 368, 88, .93), b("MAKAR", 159, 47, 253, 60, 1.0),
                b("E N A K", 100, 60, 200, 20, .5), b("P E R L U", 100, 300, 400, 20, .4),
                b("POLISI MEMATAHKAN RENCANA", 215, 45, 219, 16, .8)]
        r = pilih_headline(blok, 541)
        self.assertEqual(r["headline"], "MAKAR")
        self.assertNotIn("E N A K", r["pendukung"])
        self.assertNotIn("TEMPO", r["pendukung"].upper())

    def test_logo_salah_baca_tidak_jadi_judul(self):
        for logo in ("TFMPO", "TEMPQ", "TEMFO", "TEMPC", "TRMPO"):
            blok = [b(logo, 50, 90, 527, 125), b("OLAH-OLAH BAHLIL", 560, 60, 500, 60)]
            r = pilih_headline(blok, H)
            self.assertEqual(r["headline"], "OLAH-OLAH BAHLIL", logo)
            self.assertNotIn(logo, r["pendukung"])
        # Kata sah di bawah sampul tidak ikut terbuang.
        self.assertEqual(pilih_headline([b("TEMBO", 560, 60, 300, 60)], H)["headline"], "TEMBO")

    def test_kicker_kecil_berkeyakinan_rendah_tidak_ikut_judul(self):
        blok = [b("TEMPO", 73, 114, 625, 144, 1.0), b("5uth!", 203, 437, 615, 38, .20),
                b("BERTARUH", 268, 340, 642, 54, .78), b("PADA", 316, 480, 642, 54, .91),
                b("VAKSIN", 364, 426, 642, 56, .99)]
        self.assertEqual(pilih_headline(blok, 922)["headline"], "BERTARUH PADA VAKSIN")

    def test_baris_tengah_judul_berleading_rapat_tidak_hilang(self):
        blok = [b("KORUPSI", 240, 183, 415, 86, .94), b("BANsOS", 283, 197, 412, 80, .42),
                b("KUBU", 329, 237, 384, 70, .88), b("BANTENG", 363, 196, 441, 87, .99)]
        self.assertEqual(pilih_headline(blok, 779)["headline"], "KORUPSI BANsOS KUBU BANTENG")

    def test_baris_bertumpuk_berkotak_tinggi_tidak_dianggap_sebaris(self):
        blok = [b("TEMPO", 141, 68, 823, 211, .82), b("OBAT", 921, 257, 487, 168, 1.0),
                b("PENCABUT", 976, 226, 651, 281, 1.0), b("NYAWA", 1043, 195, 500, 210, 1.0)]
        # Urutan tidak lagi tertukar ("NYAWA PENCABUT"). "OBAT" (0,60× kotak "PENCABUT" yang membengkak)
        # masih di bawah ambang ukuran 0,62×; menurunkan ambang memicu regresi di set audit lain.
        self.assertEqual(pilih_headline(blok, 1500)["headline"], "PENCABUT NYAWA")

    def test_judul_lima_baris_berleading_rapat_utuh(self):
        blok = [b("SELINGKUH", 373, 151, 354, 114, .72), b("FATHANAH", 411, 153, 345, 112, .98),
                b("DAN", 450, 156, 248, 70, 1.0), b("PARTAI", 485, 157, 290, 88, .93), b("DAKWAH", 519, 157, 318, 102, .99)]
        self.assertEqual(pilih_headline(blok, 780)["headline"], "SELINGKUH FATHANAH DAN PARTAI DAKWAH")

    def test_sampah_teks_baku_dibuang_teks_sah_dipertahankan(self):
        from ocr_headline import _bukan_teks_sampul
        blk = lambda t, y=.5, atas=500, t_=20: {"teks": t, "atas": atas, "kiri": 0, "kanan": 100, "tinggi": t_, "yakin": y}
        sampah = [("MAJALAHTEMPOCO", .9), ("TEMPOCO/MINGGUAN", .9), ("TEMPOCOIMINGGUAN", .8), ("TENPOCO/MINGGUAN", .6),
                  ("MAJALAHTEMPO,CO", .9), ("AGUSTUS 2025 TEMPOCOIMINGGUAN", .8), ("MINGGUAN", .9), ("INVES AGASI", .9),
                  ("RP'5OESOOBER", .33), ("RP 45 Doo", .5), ("ISSM 012", .31), ("SN: Olze", .4),
                  ("7uizo", .32), ("Doo10", .39), ("XI7Va", .34)]
        sah = [("DPR", .89), ("KPK", 1), ("BPJs", .33), ("OBAT", 1), ("Rp 36 miliar", .95), ("RP77 TRILIUN", .66),
               ("INVESTIGASI: CUKONG TKI", .9), ("COVID-19", .6), ("G20", .6), ("MINGGU INI", .9), ("WAWANCARA BeKAS", .8)]
        for t, y in sampah:
            self.assertTrue(_bukan_teks_sampul(blk(t, y), 1000), t)
        for t, y in sah:
            self.assertFalse(_bukan_teks_sampul(blk(t, y), 1000), t)
        # Pecahan logo raksasa di 4-10% teratas dibuang; judul yang letaknya tinggi tidak.
        self.assertTrue(_bukan_teks_sampul(blk("APO", .68, 80, 108), 1000))
        self.assertFalse(_bukan_teks_sampul(blk("DAI", .98, 270, 124), 1000))

    def test_audit_kode_rubrik_edisi_rentang_dan_masukan_tepi(self):
        from ocr_headline import _bukan_teks_sampul
        self.assertEqual(pilih_headline([b("JEBAKAN", 500, 50, 400, 60), b("INVESTASI", 565, 50, 450, 60),
                                         b("BODONG", 630, 50, 400, 60)], 1000)["headline"], "JEBAKAN INVESTASI BODONG")
        self.assertEqual(pilih_headline([b("SERANGAN", 500, 50, 400, 60), b("BALIK GUS DUR", 565, 50, 450, 60)], 1000)["headline"],
                         "SERANGAN BALIK GUS DUR")
        blk = lambda t: b(t, 600, 0, 300, 20)
        self.assertFalse(_bukan_teks_sampul(blk("EDISI KHUSUS KEMERDEKAAN MOHAMMAD HOESNI THAMRIN"), 1000))
        self.assertTrue(_bukan_teks_sampul(blk("EDISI 3-9 SEPTEMBER 2012"), 1000))
        self.assertFalse(_bukan_teks_sampul(blk("1903-1962"), 1000))
        self.assertTrue(_bukan_teks_sampul(blk("22-28 JANUARI 2018"), 1000))
        self.assertTrue(_bukan_teks_sampul(blk("10-16"), 1000))
        # Masukan tidak lengkap tidak boleh crash.
        r = pilih_headline([{"teks": "JUDUL", "atas": 500, "kiri": 0, "tinggi": 60},
                            {"teks": None, "atas": 10, "kiri": 0, "tinggi": 10, "yakin": None}], None)
        self.assertEqual(r["headline"], "JUDUL")

    def test_jalur_tanpa_kandidat_tetap_bersih(self):
        r = pilih_headline([b("TEMPO", 50, 90, 527, 125), b("MAJALAH BERITA MINGGUAN", 700, 300, 500, 14),
                            b("TEMPOCO/MINGGUAN", 720, 300, 500, 14), b("Kr", 400, 10, 30, 12)], H)
        self.assertEqual(r["headline"], "")
        self.assertNotIn("TEMPO", r["pendukung"].upper())
        self.assertEqual(r["kandidat_headline"], [])

    def test_tanda_baca_antar_kelompok_dan_potong_kata(self):
        from ocr_headline import _gabung_kelompok, _potong, _rangkai
        self.assertEqual(_gabung_kelompok([{"teks": "Siapa mereka?"}, {"teks": "PELB"}, {"teks": "X"}]), "Siapa mereka? PELB; X")
        self.assertEqual(_rangkai(["31 OKTOBER -", "6 NOVEMBER"]), "31 OKTOBER - 6 NOVEMBER")
        self.assertEqual(_rangkai(["ANCANG-", "ANCANG JOKOWI"]), "ANCANG-ANCANG JOKOWI")
        self.assertEqual(_rangkai(["GAYA -", "GAYAAN KHILAFAH"]), "GAYA-GAYAAN KHILAFAH")
        self.assertEqual(_potong("kata " * 120), ("kata " * 100).strip())

    def test_teks_lain_seukuran_di_kolom_lain_tidak_ikut_judul(self):
        blok = [b("PERANG BUBAT", 1021, 467, 799, 60, 1.0), b("D] TANAH JAIVIA", 1090, 206, 1064, 144, .25),
                b("25 FEBRUARI-3 MARET 2019", 1435, 334, 546, 30, .79)]
        r = pilih_headline(blok, 1624)
        self.assertEqual(r["headline"], "PERANG BUBAT D] TANAH JAIVIA")
        self.assertNotIn("FEBRUARI", r["headline"])


if __name__ == "__main__":
    unittest.main()
