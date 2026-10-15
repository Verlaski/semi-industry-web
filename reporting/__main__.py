import argparse
import json
from pathlib import Path
from .builders import build_report
from .data_provider import ReportDataProvider
from .engine import generate

parser = argparse.ArgumentParser(description="从研究JSON生成中文PDF")
parser.add_argument("report_type", choices=["overview", "equipment", "materials", "landscape"])
parser.add_argument("--data", default=str(Path(__file__).resolve().parents[1] / "02 交付/半导体装备与材料产业图谱/data"))
parser.add_argument("--output", default="output/pdf")
parser.add_argument("--track-id")
args = parser.parse_args()
model = build_report(ReportDataProvider(args.data).snapshot(), args.report_type, {"track_id": args.track_id} if args.track_id else {})
print(json.dumps(generate(model, Path(args.output) / (args.report_type + ".pdf")), ensure_ascii=False))
