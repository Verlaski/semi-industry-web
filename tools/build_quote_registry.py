"""依据正式公司主表 companies.json 生成行情证券注册表 backend/market/symbols.generated.js。
覆盖 A股(SH/SZ/BJ)、港股、美股（腾讯 gtimg 已实测支持这五类代码前缀）；
日股/欧股/韩股/台股不在供应商首批范围，不生成注册项（前端显示—）。
运行：python tools/build_quote_registry.py   （仓库根目录）"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ROOT / "02 交付" / "半导体装备与材料产业图谱" / "data" / "companies.json"
OUT = ROOT / "backend" / "market" / "symbols.generated.js"

EM_US = {"NASDAQ": "105", "NYSE": "106", "NYSE American": "107", "NYSEAmerican": "107"}


def entry(company, listing):
    ticker = listing.get("ticker") or ""
    if "." not in ticker:
        return None
    code, suffix = ticker.rsplit(".", 1)
    cid = company["company_id"]
    name = company.get("short_name") or company.get("name_cn") or company.get("name_en") or cid
    if suffix in ("SH", "SZ", "BJ"):
        em = ("1." if suffix == "SH" else "0.") + code
        tc = {"SH": "sh", "SZ": "sz", "BJ": "bj"}[suffix] + code
        return {"name": name, "market": "A股", "currency": "CNY", "zone": "Asia/Shanghai",
                "eastmoney": em, "tencent": tc, "listing_id": listing["listing_id"]}
    if suffix == "HK":
        provider_code = code.zfill(5)
        return {"name": name, "market": "港股", "currency": "HKD", "zone": "Asia/Hong_Kong",
                "eastmoney": "116." + provider_code, "tencent": "hk" + provider_code, "listing_id": listing["listing_id"]}
    if suffix == "US":
        em = EM_US.get(listing.get("exchange", ""), "105") + "." + code
        return {"name": name, "market": "美股", "currency": "USD", "zone": "America/New_York",
                "eastmoney": em, "tencent": "us" + code, "listing_id": listing["listing_id"]}
    return None


def main():
    companies = json.loads(COMPANIES.read_text(encoding="utf-8"))["companies"]
    registry, skipped = {}, []
    for c in companies:
        for l in c.get("listings") or []:
            e = entry(c, l)
            if e is None:
                if l.get("ticker"):
                    skipped.append(f"{l['ticker']}({c['company_id']})")
                continue
            if l["ticker"] in registry:
                raise SystemExit(f"注册表代码重复: {l['ticker']}（{c['company_id']}）")
            registry[l["ticker"]] = e
    # 三只试运行证券必须保留且字段一致（quotes_latest 缓存键为 symbol，不破坏可回退）
    for pilot in ("688012.SH", "00522.HK", "AMAT.US"):
        if pilot not in registry:
            raise SystemExit(f"试运行证券 {pilot} 未在注册表中，检查 companies.json")
    lines = ["// 由 tools/build_quote_registry.py 生成，请勿手改。", "module.exports = {"]
    for ticker in sorted(registry):
        e = registry[ticker]
        lines.append(
            f"  '{ticker}':{{name:{json.dumps(e['name'], ensure_ascii=False)},market:'{e['market']}',currency:'{e['currency']}',"
            f"zone:'{e['zone']}',eastmoney:'{e['eastmoney']}',tencent:'{e['tencent']}',listing_id:'{e['listing_id']}'}},")
    lines.append("};\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"注册表 {len(registry)} 只证券 -> {OUT.name}；跳过非首批市场 {len(skipped)} 个 ticker")
    if skipped:
        print("跳过:", ", ".join(skipped[:20]), "..." if len(skipped) > 20 else "")


if __name__ == "__main__":
    main()
