"""Protect human evidence when extending an existing analysis release."""
from pathlib import Path
import tempfile
import unittest
import build_technical_delivery as delivery

class HumanReturnPreservationTests(unittest.TestCase):
    def test_existing_human_returns_and_notes_survive_release_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);human=root/'UNTUK_MANUSIA';(human/'PAKET_PENILAI').mkdir(parents=True)
            names=['REGISTRASI_PARTISIPAN.csv','R22_REVIEW_MANUSIA_20.csv','RIWAYAT_KORPUS_PER_ID.csv','RIWAYAT_KORPUS.md','CATATAN_UNTUK_PEMBIMBING.md']
            for name in names:(human/name).write_text('TEST FIXTURE: existing return '+name)
            result=delivery.human_handoff(root)
            for name in names:self.assertEqual((human/name).read_text(),'TEST FIXTURE: existing return '+name)
            self.assertFalse(result['human_ratings_generated_by_agent'])
            self.assertTrue(result['existing_return_files_preserved'])

if __name__=='__main__':unittest.main()
