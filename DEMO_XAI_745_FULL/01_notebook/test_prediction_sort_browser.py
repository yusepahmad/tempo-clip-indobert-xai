"""Real Chromium UI regression with mocked requests; no model/server required."""
from pathlib import Path
import unittest
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright
from test_audit_frontend import hasil_palsu, XSS

PAGE = Path(__file__).resolve().parents[1] / '02_web_demo/index.html'


class PredictionSortBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def check_viewport(self, width, height, mode_data):
        errors = []
        with self.browser.new_context(viewport={'width': width, 'height': height}) as context:
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))

            def respond(route):
                path = urlparse(route.request.url).path
                if path == '/':
                    route.fulfill(content_type='text/html', body=PAGE.read_text(encoding='utf-8'))
                elif path == '/api/samples':
                    route.fulfill(json=[{'sample_id': 'fixture', 'headline': 'Contoh', 'supporting': ''}])
                elif path == '/api/catalog':
                    route.fulfill(json=[])
                elif path == '/api/models':
                    route.fulfill(json={})
                elif path.startswith('/api/image/'):
                    route.fulfill(status=204)
                else:
                    self.fail('Unexpected request; inference must not run: ' + path)

            context.route('**/*', respond)
            page.goto('http://tempo.test/')
            page.wait_for_function("document.getElementById('sample').options.length===1")
            result = hasil_palsu()
            names = ['Isu utama', 'Domain sumber metafora', 'Sasaran kritik']
            for (task, pred), name, score in zip(result['prediksi'].items(), names, [0.177, 0.304, 0.27]):
                pred['nama_task_mudah'] = name
                pred['prediksi_tampil'] = 'Label ' + task
                pred['probabilitas'] = score
            page.evaluate('([result,mode])=>tampil(result,mode)', [result, mode_data])
            table_rows = page.locator('#tabelPred tr').all()[1:]
            self.assertEqual([r.locator('td').nth(0).inner_text() for r in table_rows], [names[1], names[2], names[0]])
            for row, index, pct in zip(table_rows, [1, 2, 0], ['30.4', '27.0', '17.7']):
                task = list(result['prediksi'])[index]
                self.assertIn('Label ' + task, row.locator('td').nth(1).inner_text())
                self.assertTrue(row.locator('td').nth(2).inner_text().startswith(pct + '%'))
                self.assertEqual(row.locator('.bar i').get_attribute('style'), 'width:' + pct + '%')
            self.assertIn('tertinggi ke terendah', page.inner_text('#tabelPred'))
            self.assertTrue(page.is_visible('#tabelPred'))
            # Changing row order must not change the selected explanation/task.
            self.assertIn(result['task_xai'], page.inner_text('#ringkas'))
            xss_result = hasil_palsu(XSS)
            xss_result['prediksi']['task2_domain_sumber']['probabilitas'] = 0.9
            page.evaluate('result=>tampil(result,true)', xss_result)
            self.assertEqual(page.locator('#tabelPred [data-xss]').count(), 0)
            self.assertIsNone(page.evaluate('window.__xss'))
            self.assertIn('<img src=x', page.inner_text('#tabelPred'))
            self.assertEqual(errors, [])

    def test_desktop_dataset(self):
        self.check_viewport(1440, 1000, True)

    def test_mobile_upload_result(self):
        self.check_viewport(390, 844, False)


if __name__ == '__main__':
    unittest.main()
