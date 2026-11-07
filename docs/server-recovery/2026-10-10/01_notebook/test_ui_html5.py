"""HTML5 parsing regression: textarea must not swallow workspace/batch controls."""
from pathlib import Path
import re
import unittest
from bs4 import BeautifulSoup

PAGE = Path(__file__).resolve().parents[1] / '02_web_demo/index.html'

class Html5UiTests(unittest.TestCase):
    def setUp(self):
        self.source=PAGE.read_text(encoding='utf-8')
        self.dom=BeautifulSoup(self.source,'html5lib')

    def test_ids_survive_browser_parsing(self):
        expected={x['id'] for x in BeautifulSoup(self.source,'html.parser').select('[id]')}
        actual=[x['id'] for x in self.dom.select('[id]')]
        self.assertEqual(expected,set(actual))
        self.assertEqual(len(actual),len(set(actual)))

    def test_textareas_are_closed_and_empty(self):
        self.assertIsNone(re.search(r'<textarea\b[^>]*?/>',self.source))
        for key in ['dataSupporting','supporting','batchIds']:
            node=self.dom.find(id=key)
            self.assertEqual(node.name,'textarea')
            self.assertEqual(node.get_text(),'')

    def test_workspace_and_views_are_separate(self):
        self.assertIsNotNone(self.dom.select_one('.dashboard > #workspace'))
        self.assertIsNotNone(self.dom.select_one('.input-panel #task'))
        self.assertIsNotNone(self.dom.select_one('.input-panel #jalan'))
        for key in ['batch','panduan']:
            self.assertIn('wrap',self.dom.find(id=key).parent.get('class',[]))
        self.assertIsNotNone(self.dom.body.find('script',recursive=False))

    def test_original_failure_fixture_is_detected(self):
        broken=self.source.replace('rows="5"></textarea>','rows="5"/>')
        self.assertNotEqual(broken,self.source)
        dom=BeautifulSoup(broken,'html5lib')
        self.assertIsNone(dom.find(id='workspace'))

if __name__=='__main__': unittest.main()
