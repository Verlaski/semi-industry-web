import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.build_offline import ASSETS, SITE, build, make_files, public_bundle


class OfflinePackageTest(unittest.TestCase):
    def test_strict_file_allowlist_and_embedded_data(self):
        with tempfile.TemporaryDirectory() as target:
            result = build(target)
            with zipfile.ZipFile(Path(target) / result['filename']) as package:
                expected = {'semi-industry-offline/' + name for name in (*ASSETS, 'index.html', 'assets/js/config.js')}
                self.assertEqual(set(package.namelist()), expected)
                self.assertIsNone(package.testzip())
                config = package.read('semi-industry-offline/assets/js/config.js').decode()
                self.assertNotIn('apiBase', config)
                self.assertNotIn('offlineDownload', config)
                self.assertIn('"offline": true', config)
                html = package.read('semi-industry-offline/index.html').decode()
                self.assertNotIn('id="offline-save"', html)
                self.assertIn("connect-src 'none'", html)
                payload = re.search(r'<script id="offline-data" type="application/json">(.*?)</script>', html, re.S)[1]
                self.assertEqual(json.loads(payload), public_bundle())
                self.assertNotIn('<', payload)

    def test_company_projection_retains_repository_fields_only(self):
        bundle = public_bundle()
        raw = json.loads((SITE / 'data/companies.json').read_text(encoding='utf-8'))
        self.assertEqual([c['company_id'] for c in raw['companies']], [c['company_id'] for c in bundle['companies']['companies']])
        for company in bundle['companies']['companies']:
            self.assertNotIn('unresolved', company)
            self.assertNotIn('entity_decision', company)
            for listing in company['listings']:
                self.assertNotIn('provider_symbols', listing)
                self.assertIn('ticker', listing)

    def test_database_script_injection_is_escaped(self):
        # Names and source descriptions can contain markup; no executable script may escape the JSON block.
        from unittest.mock import patch
        bundle = public_bundle()
        bundle['companies']['companies'][0]['name_cn'] = '</script><script>alert(1)</script>'
        with patch('tools.build_offline.public_bundle', return_value=bundle):
            files, _ = make_files()
        html = files['index.html'].decode()
        self.assertNotIn('</script><script>alert(1)', html)
        payload = re.search(r'<script id="offline-data" type="application/json">(.*?)</script>', html, re.S)[1]
        self.assertEqual(json.loads(payload)['companies']['companies'][0]['name_cn'], bundle['companies']['companies'][0]['name_cn'])


if __name__ == '__main__':
    unittest.main()
