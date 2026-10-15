"""发布后的HTTP、行情与PDF验收；不记录临时下载签名。"""
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def request(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "semi-industry-acceptance/1.1"})
    try:
        with urllib.request.urlopen(req, timeout=90) as result:
            return result.status, result.headers.get_content_type(), result.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get_content_type(), error.read()


def main():
    settings = json.loads((ROOT / ".local/environment.json").read_text(encoding="utf-8"))
    site, api = settings["site_url"], settings["api_base"]
    status, mime, html = request(site)
    assert status == 200 and mime == "text/html", "网站入口异常"
    html = html.decode("utf-8")
    assets = re.findall(r'(?:src|href)="(assets/[^\"]+)"', html)
    resources = []
    for resource in assets + ["data/" + name + ".json" for name in ("meta", "equipment", "materials", "sources")] + ["assets/发布校验.txt"]:
        url = urllib.parse.urljoin(site, urllib.parse.quote(resource, safe="/.-"))
        status, mime, content = request(url)
        expected = "application/json" if resource.endswith(".json") else "text/css" if resource.endswith(".css") else "text/plain" if resource.endswith(".txt") else None
        assert status == 200 and (mime == expected if expected else mime in ("text/javascript", "application/javascript")), "静态资源异常：" + resource
        if resource.endswith(".json"):
            json.loads(content.decode("utf-8-sig"))
        resources.append({"path": resource, "mime": mime, "bytes": len(content)})
    status, _, body = request(api + "/health")
    health = json.loads(body)
    assert status == 200 and health["ok"], "服务健康检查失败"
    status, _, body = request(api + "/api/quotes")
    quotes = json.loads(body)["quotes"]
    assert status == 200 and len(quotes) == 3 and all(q["price"] and q["price"] > 0 and q["quote_time"] and q["fetched_at"] for q in quotes), "三股行情异常"
    assert request(api + "/api/quotes?symbols=UNKNOWN")[0] == 400
    reports = []
    output = ROOT / "output/pdf"
    output.mkdir(parents=True, exist_ok=True)
    for kind in ("overview", "equipment", "materials", "landscape"):
        payload = {"report_type": kind, "filters": {}}
        status, _, body = request(api + "/api/reports", payload)
        assert status == 200, "报告生成失败：" + kind
        report = json.loads(body)
        status, mime, binary = request(report["download_url"])
        assert status == 200 and mime == "application/pdf" and binary.startswith(b"%PDF-"), "PDF下载异常：" + kind
        (output / ("cloud-" + kind + ".pdf")).write_bytes(binary)
        status, _, body = request(api + "/api/reports", payload)
        assert status == 200 and json.loads(body)["cached"], "PDF缓存未命中：" + kind
        url = report["download_url"]
        tampered = url[:-1] + ("0" if url[-1] != "0" else "1")
        assert request(tampered)[0] == 403, "无效签名未拒绝"
        reports.append({"report_type": kind, "bytes": len(binary), "mime": mime, "filename": report["filename"], "data_version": report["data_version"], "cached_second_call": True, "tamper_status": 403})
    result = {"site_url": site, "health": health, "resources": resources, "quotes": quotes, "reports": reports}
    (ROOT / ".local/online-checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"static_resources": len(resources), "quotes": len(quotes), "pdf_types": len(reports), "cache_and_tamper_checks": "passed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
