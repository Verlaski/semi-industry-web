"""所有文件读取集中在Provider；Builder只消费规范化快照。"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path


class ReportDataProvider:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def snapshot(self):
        data, digest = {}, hashlib.sha256()
        for name in ("meta", "equipment", "materials", "sources"):
            raw = (self.data_dir / (name + ".json")).read_bytes()
            digest.update(name.encode() + b"\0" + raw)
            data[name] = json.loads(raw.decode("utf-8-sig"))
        company_path = self.data_dir / "companies.json"
        if company_path.exists():
            raw = company_path.read_bytes()
            digest.update(raw)
            data["companies"] = json.loads(raw.decode("utf-8-sig"))
        data["data_version"] = str(data["meta"].get("version", "未知")) + "-" + digest.hexdigest()[:12]
        data["tracks"] = [{**deepcopy(t), "dataset": dataset} for dataset in ("equipment", "materials") for t in data[dataset]["tracks"]]
        return data
