import tempfile
import unittest
from pathlib import Path
from reporting.data_provider import ReportDataProvider
from reporting.builders import build_report
from reporting.engine import generate
from reporting.qa import inspect

ROOT = Path(__file__).resolve().parents[1]


class ReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = ReportDataProvider(ROOT / "02 交付/半导体装备与材料产业图谱/data").snapshot()

    def test_all_types_keep_source_ids_and_table_widths(self):
        source_ids = {s["source_id"] for s in self.snapshot["sources"]["sources"]}
        for kind in ("overview", "equipment", "materials", "landscape"):
            model = build_report(self.snapshot, kind)
            self.assertTrue(model.sources)
            self.assertTrue(all(s["source_id"] in source_ids for s in model.sources))
            self.assertTrue(all(abs(sum(table.widths) - 16.2) < 0.001 for section in model.sections for table in section.tables))
            self.assertEqual(model.data_version, self.snapshot["data_version"])

    def test_unconfirmed_company_reports_and_invalid_filters_rejected(self):
        with self.assertRaises(ValueError):
            build_report(self.snapshot, "companies")
        with self.assertRaises(ValueError):
            build_report(self.snapshot, "overview", {"arbitrary": "query"})
        with self.assertRaises(ValueError):
            build_report(self.snapshot, "equipment", {"track_id": "missing"})

    def test_scientific_superscript_font_and_pagination(self):
        import os
        os.environ["REPORT_FONT_MODE"] = "bundled"
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="report-test-", dir=local) as temp:
            target = Path(temp) / "test.pdf"
            model = build_report(self.snapshot, "equipment", {"track_id": "eq-u-vacuum"})
            result = generate(model, target)
            self.assertEqual(result["font"], "NotoSansSC-Regular.ttf")
            checks = inspect(target, Path(temp) / "qa", dpi=72)
            self.assertFalse(checks["problems"], checks["problems"])
            self.assertGreater(checks["page_count"], 2)

    def test_korean_company_names_remain_readable_in_bundled_pdf(self):
        import os
        import pymupdf
        os.environ['REPORT_FONT_MODE'] = 'bundled'
        with tempfile.TemporaryDirectory(prefix='hangul-test-', dir=ROOT / '.local') as temp:
            target = Path(temp) / 'hangul.pdf'
            generate(build_report(self.snapshot, 'materials', {'track_id': 'ma-f-wafer'}), target)
            with pymupdf.open(target) as document:
                text = ''.join(page.get_text() for page in document)
            self.assertIn('실트론', text)
            self.assertNotIn('\x00', text)
            self.assertNotIn('\ufffd', text)


if __name__ == "__main__":
    unittest.main()
