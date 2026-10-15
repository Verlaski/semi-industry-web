import unittest
from tools.build_quote_registry import entry


class RegistryTests(unittest.TestCase):
    def test_hong_kong_provider_codes_use_five_digits_without_changing_listing_id(self):
        company = {'company_id': 'CCTC', 'name_cn': '三环集团'}
        for ticker, code in [('6951.HK', '06951'), ('00522.HK', '00522')]:
            spec = entry(company, {'ticker': ticker, 'listing_id': 'listing-fixture'})
            self.assertEqual(spec['tencent'], 'hk' + code)
            self.assertEqual(spec['eastmoney'], '116.' + code)
            self.assertEqual(spec['listing_id'], 'listing-fixture')
