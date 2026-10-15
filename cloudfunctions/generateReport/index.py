"""Python事件函数：只消费受控类型/筛选及服务器取回的行情快照。"""
import base64
from pathlib import Path
import tempfile
from reporting.data_provider import ReportDataProvider
from reporting.builders import build_report
from reporting.engine import generate


def main_handler(event, context):
    report_type = event.get("report_type", "overview")
    snapshot = ReportDataProvider(Path(__file__).parent / "data").snapshot()
    model = build_report(snapshot, report_type, event.get("filters", {}), event.get("quotes", []))
    with tempfile.TemporaryDirectory(dir="/tmp") as directory:
        destination = Path(directory) / "report.pdf"
        result = generate(model, destination)
        raw = destination.read_bytes()
        if len(raw) > 3_000_000:
            raise ValueError("报告过大，请缩小筛选范围")
        return {"pdf_base64": base64.b64encode(raw).decode("ascii"), "data_version": result["data_version"],
                "generated_at": result["generated_at"], "font": result["font"], "report_type": report_type}


# 部分管理工具将Python入口固定为index.main；同时提供兼容入口。
main = main_handler
