# -*- coding: utf-8 -*-
"""独立遍历原始leader验证候选池。Error非零退出，Review正常退出。

python "03 研究工作区/validate_company_pool.py"
python "03 研究工作区/validate_company_pool.py" --self-test
源覆盖枚举和并列数量核对独立实现，不调用提取器的遍历/分句函数。
"""
from __future__ import annotations
import argparse
import collections
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import unicodedata

from extract_companies import COUNTRY_MAP, CATEGORIES, extract, parse_name

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "02 交付" / "半导体装备与材料产业图谱" / "data"


def canonical(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).upper() if c.isalnum() or c in "&/-")


def expected_pieces(text):
    """独立扫描遮蔽括号，按原文偏移计算公司名称片段。"""
    masked, depth = [], 0
    for char in text:
        if char in "(（":
            depth += 1
            masked.append(" ")
        elif char in ")）":
            depth -= 1
            if depth < 0:
                raise ValueError(f"源名称括号异常：{text}")
            masked.append(" ")
        else:
            masked.append(" " if depth else char)
    if depth:
        raise ValueError(f"源名称括号异常：{text}")
    visible = "".join(masked)
    boundaries = [0] + [m.end() for m in re.finditer(r"[;；]", visible)]
    ends = [m.start() for m in re.finditer(r"[;；]", visible)] + [len(text)]
    result = []
    has_description = bool(re.search(r"[:：]", visible))
    for ci, (start, end) in enumerate(zip(boundaries, ends)):
        colon = re.search(r"[:：]", visible[start:end])
        if ci and colon is None and has_description:
            continue
        name_end = start + colon.start() if colon else end
        dividers = list(re.finditer(r"[、·]", visible[start:name_end]))
        lefts = [start] + [start + m.end() for m in dividers]
        rights = [start + m.start() for m in dividers] + [name_end]
        result.extend(text[a:b].strip() for a, b in zip(lefts, rights) if text[a:b].strip())
    return result


def source_index(sources):
    expected, raw_counts, track_ids = {}, collections.Counter(), set()
    for ds in ("equipment", "materials"):
        data = sources.get(ds)
        if not isinstance(data, dict) or not isinstance(data.get("tracks"), list):
            raise ValueError(f"{ds}: tracks类型错误")
        for ti, track in enumerate(data["tracks"]):
            if not isinstance(track, dict) or not isinstance(track.get("id"), str) or not track["id"]:
                raise ValueError(f"{ds}/tracks/{ti}: 无有效赛道ID")
            tid = track["id"]
            if (ds, tid) in track_ids:
                raise ValueError(f"{ds}: 重复赛道ID {tid}")
            track_ids.add((ds, tid))
            subs = track.get("subs", [])
            if not isinstance(subs, list):
                raise ValueError(f"{ds}/{tid}: subs类型错误")
            scopes = [(None, track)] + list(enumerate(subs))
            for si, obj in scopes:
                if not isinstance(obj, dict) or (si is not None and not isinstance(obj.get("name"), str)):
                    raise ValueError(f"{ds}/{tid}: 二级细分类型错误")
                prefix = f"/tracks/{ti}" + (f"/subs/{si}" if si is not None else "")
                for role in ("global", "china"):
                    field = role + "_leaders"
                    entries = obj.get(field, [])
                    if not isinstance(entries, list):
                        raise ValueError(f"{ds}{prefix}/{field}: 源leader非数组")
                    for li, entry in enumerate(entries):
                        pointer = f"{prefix}/{field}/{li}"
                        if isinstance(entry, str):
                            text, country, metadata = entry, "", {}
                        elif isinstance(entry, dict):
                            text, country = entry.get("name"), entry.get("country", "")
                            metadata = {k: v for k, v in entry.items() if k not in ("name", "country")}
                        else:
                            raise ValueError(f"{ds}{pointer}: 源leader类型错误")
                        if not isinstance(text, str) or not text.strip() or not isinstance(country, str):
                            raise ValueError(f"{ds}{pointer}: 源name/country异常")
                        level = 1 if si is None else 2
                        raw_counts[f"{ds}/L{level}/{role}"] += 1
                        pieces = expected_pieces(text)
                        if not pieces:
                            raise ValueError(f"{ds}{pointer}: 未发现可提取名称")
                        for pi, piece in enumerate(pieces):
                            expected[(ds, pointer, pi)] = dict(
                                dataset=ds, track_id=tid, sub_name="" if si is None else obj["name"],
                                sub_index=si, level=level, role=role, leader_index=li,
                                piece_index=pi, source_pointer=pointer, source_text=text,
                                raw_name=piece, country_raw=country, source_metadata=metadata)
    return expected, raw_counts, track_ids


def validate(pool, sources):
    errors, reviews = [], []
    expected, raw_counts, track_ids = source_index(sources)
    if not isinstance(pool, dict) or not isinstance(pool.get("companies"), list):
        return ["根结构错误：companies必须是数组"], []
    if pool.get("schema_version") != "company-pool-draft-1" or not isinstance(pool.get("stage"), str):
        errors.append("根schema_version/stage异常")
    seen_keys, seen_occ, ticker_owners = {}, {}, collections.defaultdict(list)
    companies = pool["companies"]
    for ci, c in enumerate(companies):
        label = f"companies[{ci}]"
        if not isinstance(c, dict):
            errors.append(f"{label}: 必须是对象")
            continue
        if "company_id" in c:
            errors.append(f"{label}: 本阶段不允许最终company_id")
        valid = True
        for field in ("normalized_key", "name_cn", "name_en", "country_region", "country_basis", "ticker_hint", "review_reason"):
            if not isinstance(c.get(field), str):
                errors.append(f"{label}.{field}: 必须为字符串")
                valid = False
        for field in ("raw_names", "name_cn_variants", "name_en_variants", "country_regions", "ticker_hints", "notes"):
            values = c.get(field)
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                errors.append(f"{label}.{field}: 必须为字符串数组")
                valid = False
            elif len(values) != len(set(values)):
                errors.append(f"{label}.{field}: 含重复元素")
        if type(c.get("review_required")) is not bool:
            errors.append(f"{label}.review_required: 必须为bool")
            valid = False
        reasons = c.get("review_reasons")
        if not isinstance(reasons, list) or any(not isinstance(r, dict) or not isinstance(r.get("category"), str) or r["category"] not in CATEGORIES
                                               or not isinstance(r.get("reason"), str) or not r["reason"] for r in reasons):
            errors.append(f"{label}.review_reasons: 类型或类别异常")
            valid = False
        if not isinstance(c.get("occurrences"), list) or not c["occurrences"]:
            errors.append(f"{label}.occurrences: 必须为非空数组")
            valid = False
        if not valid:
            continue
        key = c["normalized_key"]
        label += f"({key})"
        if not key.strip():
            errors.append(f"{label}: normalized_key为空")
        if key != canonical(c["name_en"] or c["name_cn"]):
            errors.append(f"{label}: normalized_key与清洗名称不符")
        collision_key = canonical(key)
        if collision_key in seen_keys:
            errors.append(f"{label}: 明显重复normalized_key，与{seen_keys[collision_key]}冲突")
        seen_keys[collision_key] = key
        if not (c["name_cn"] or c["name_en"]):
            errors.append(f"{label}: 中英文名称均为空")
        for field in ("name_cn", "name_en", "name_cn_variants", "name_en_variants"):
            texts = c[field] if isinstance(c[field], list) else [c[field]]
            for text in texts:
                if re.search(r"(?<![A-Za-z0-9])(?:[A-Z]\d{5,6}|\d{4,6}(?:\.[A-Z]{1,6})?)(?![A-Za-z0-9])", text):
                    errors.append(f"{label}.{field}: 名称混有明显代码 {text}")
                if re.search(r"[：:;%％]|市占率|在手订单|大陆首家|约\d", text):
                    errors.append(f"{label}.{field}: 名称疑似混入业务说明 {text}")
        categories = {r["category"] for r in reasons}
        if c["review_required"] != bool(reasons) or c["review_reason"] != "；".join(r["reason"] for r in reasons):
            errors.append(f"{label}: review标记、原因及明细不一致")

        def needs_review(category, message):
            if not c["review_required"] or category not in categories:
                errors.append(f"{label}: {message}但未标记{category}复核")
            else:
                reviews.append(f"{key}: {message}")

        if not c["country_region"]:
            needs_review("country", "国家地区缺失")
        if len(c["country_regions"]) > 1:
            needs_review("other", "同一normalized_key有多地区/冲突：" + "/".join(c["country_regions"]))
        if any(v not in COUNTRY_MAP.values() for v in c["country_regions"]):
            needs_review("other", "国家地区映射待确认")
        if any("/" in n or "／" in n for n in (c["name_cn"], c["name_en"])):
            needs_review("slash", "斜杠组合主体待判断")
        if c["country_region"] != "/".join(sorted(c["country_regions"])):
            errors.append(f"{label}: country_region与地区明细不一致")
        ticker_hint = c["ticker_hints"][0] if len(c["ticker_hints"]) == 1 else ""
        if c["ticker_hint"] != ticker_hint:
            errors.append(f"{label}: ticker_hint与ticker_hints不一致")
        for ticker in c["ticker_hints"]:
            if not re.fullmatch(r"(?:[A-Z]\d{5,6}|\d{4,6}(?:\.[A-Z]{1,6})?)", ticker):
                errors.append(f"{label}: ticker_hint格式异常 {ticker}")
            ticker_owners[ticker].append((key, categories))
        raw_names, countries, tickers, cn_variants, en_variants, notes = set(), set(), set(), set(), set(), set()
        for oi, occurrence in enumerate(c["occurrences"]):
            ol = f"{label}.occurrences[{oi}]"
            if not isinstance(occurrence, dict):
                errors.append(f"{ol}: 必须为对象")
                continue
            typed = True
            for field in ("dataset", "track_id", "sub_name", "role", "source_pointer", "source_text", "raw_name", "country_raw"):
                if not isinstance(occurrence.get(field), str):
                    errors.append(f"{ol}.{field}: 必须为字符串")
                    typed = False
            for field in ("level", "leader_index", "piece_index"):
                if type(occurrence.get(field)) is not int or occurrence[field] < 0:
                    errors.append(f"{ol}.{field}: 必须为非负整数")
                    typed = False
            if "sub_index" not in occurrence:
                errors.append(f"{ol}: 缺少sub_index字段")
            si = occurrence.get("sub_index")
            if si is not None and (type(si) is not int or si < 0):
                errors.append(f"{ol}.sub_index: 必须为null或非负整数")
                typed = False
            regions = occurrence.get("country_regions")
            if not isinstance(regions, list) or any(not isinstance(v, str) for v in regions):
                errors.append(f"{ol}.country_regions: 必须为字符串数组")
                typed = False
            if not isinstance(occurrence.get("source_metadata"), dict):
                errors.append(f"{ol}.source_metadata: 必须为对象")
                typed = False
            if not typed:
                continue
            identifier = (occurrence["dataset"], occurrence["source_pointer"], occurrence["piece_index"])
            if identifier in seen_occ:
                errors.append(f"{ol}: occurrence重复，与{seen_occ[identifier]}重复")
            seen_occ[identifier] = key
            if (occurrence["dataset"], occurrence["track_id"]) not in track_ids:
                errors.append(f"{ol}: track_id不存在")
            original = expected.get(identifier)
            if original is None:
                errors.append(f"{ol}: 原始引用不存在或并列序号越界 {identifier}")
                continue
            for field, value in original.items():
                if occurrence.get(field) != value:
                    errors.append(f"{ol}.{field}: 与原始引用不符")
            parsed = parse_name(original["raw_name"], original["country_raw"])
            if regions != parsed["country_regions"]:
                errors.append(f"{ol}: 地区证据与原始引用不一致")
            raw_names.add(original["raw_name"])
            countries.update(parsed["country_regions"])
            tickers.update(parsed["ticker_hints"])
            notes.update(parsed["notes"])
            if parsed["name_cn"]:
                cn_variants.add(parsed["name_cn"])
            if parsed["name_en"]:
                en_variants.add(parsed["name_en"])
        aggregates = dict(raw_names=raw_names, country_regions=countries, ticker_hints=tickers,
                          name_cn_variants=cn_variants, name_en_variants=en_variants, notes=notes)
        for field, values in aggregates.items():
            if set(c[field]) != values:
                errors.append(f"{label}.{field}: 与全部原始引用汇总不符")
        for field, variants in (("name_cn", cn_variants), ("name_en", en_variants)):
            if c[field] and c[field] not in variants:
                errors.append(f"{label}.{field}: 名称无原始引用支持")
    for identifier, item in expected.items():
        if identifier not in seen_occ:
            errors.append(f"L{item['level']}遗漏：{identifier} {item['raw_name']}")
    for ticker, owners in ticker_owners.items():
        if len(owners) > 1:
            message = f"同一ticker_hint {ticker} 对应多个候选：" + "/".join(k for k, _ in owners)
            if any("ticker_collision" not in categories for _, categories in owners):
                errors.append(message + "，未完整标记复核")
            else:
                reviews.append(message)
    raw_level = collections.Counter()
    for key, count in raw_counts.items():
        raw_level[key.split("/")[1][1:]] += count
    stats = pool.get("statistics")
    expected_stats = dict(raw_leader_references=sum(raw_counts.values()), raw_by_level=dict(raw_level),
                          raw_by_dataset_level_role=dict(raw_counts), records_before_dedup=len(expected),
                          candidate_companies=len(companies), duplicate_records_merged=len(expected)-len(companies),
                          review_companies=sum(isinstance(c, dict) and c.get("review_required") is True for c in companies))
    if not isinstance(stats, dict) or stats != expected_stats:
        errors.append("statistics与独立核对结果不一致")
    elif any(type(stats.get(k)) is not int for k in ("raw_leader_references", "records_before_dedup", "candidate_companies", "duplicate_records_merged", "review_companies")):
        errors.append("statistics数量必须为整数")
    elif any(type(v) is not int for field in ("raw_by_level", "raw_by_dataset_level_role") for v in stats[field].values()):
        errors.append("statistics分组数量必须为整数")
    return errors, reviews


def self_test():
    """固定真实边界案例及破坏性负例；不写入正式数据或临时文件。"""
    source = {
        "equipment": {"tracks": [{"id": "eq-test", "global_leaders": [
            {"name": "阿斯麦 ASML", "country": "荷"},
            {"name": "Edwards 爱德华（Atlas Copco旗下）", "country": "英"},
            {"name": "Nikon/Canon", "country": "日"},
            {"name": "TRUMPF Hüttinger 霍廷格", "country": "德"},
            {"name": "先进封装材料国际 AAMI", "country": "中国香港/新加坡"}],
            "china_leaders": [{"name": "中科仪(920186)"}, {"name": "华卓精科(A04100，IPO辅导中)"},
                              {"name": "甲公司(002158)"}, {"name": "乙公司(002158)"},
                              {"name": "英杰电气(300820)/英杰晨晖"}],
            "subs": [{"name": "细分", "global_leaders": ["ASML（荷）", {"name": "荏原 Ebara", "country": "日"},
                "K&S：TCB约27%；EVG(奥)/SUSS(德)：晶圆级键合",
                "Besi(荷)：混合键合份额约67%；TCB约17%", "旺矽科技、惠特科技(中国台湾)"],
                "china_leaders": ["华卓精科、青禾晶元、吾拾微、芯睿科技", "矽电股份：市占率25%；大陆首家12英寸厂商",
                                  "芯源微：临时键合机；2024年报在手订单近20台"]}]}]},
        "materials": {"tracks": [{"id": "ma-test", "global_leaders": [{"name": "ASML", "country": "荷"}], "china_leaders": []}]},
    }
    good = extract(source)
    errors, reviews = validate(good, source)
    assert not errors, errors
    companies = good["companies"]
    asml = next(c for c in companies if c["normalized_key"] == "ASML")
    assert len(asml["occurrences"]) == 3
    assert next(c for c in companies if c["name_cn"] == "中科仪")["ticker_hint"] == "920186"
    assert next(c for c in companies if c["name_cn"] == "华卓精科")["ticker_hint"] == "A04100"
    assert next(c for c in companies if c["normalized_key"] == "NIKON/CANON")["review_required"]
    assert next(c for c in companies if c["normalized_key"] == "AAMI")["country_region"] == "中国香港/新加坡"
    assert any(c["normalized_key"] == "TRUMPFHÜTTINGER" for c in companies)
    assert all(not re.search(r"大陆首家|在手订单|约17", c["name_cn"] + c["name_en"]) for c in companies)
    assert any("同一ticker_hint" in r for r in reviews)
    assert expected_pieces("甲公司；乙公司") == ["甲公司", "乙公司"]
    probes = [
        ("空辅助键", lambda p: p["companies"][0].update(normalized_key="")),
        ("重复辅助键", lambda p: p["companies"].append(deepcopy(p["companies"][0]))),
        ("名称残留代码", lambda p: p["companies"][0].update(name_cn="甲公司(002158)")),
        ("国家类型错误", lambda p: p["companies"][0].update(country_region=[])),
        ("occurrence类型错误", lambda p: p["companies"][0].update(occurrences="bad")),
        ("原始记录缺失", lambda p: p["companies"].pop()),
        ("occurrence重复", lambda p: p["companies"][0]["occurrences"].append(deepcopy(p["companies"][0]["occurrences"][0]))),
        ("引用错误赛道", lambda p: p["companies"][0]["occurrences"][0].update(track_id="missing")),
        ("引用错误子级", lambda p: p["companies"][0]["occurrences"][0].update(sub_index=True)),
        ("遗漏全部原文", lambda p: p["companies"][0].update(raw_names=[])),
        ("错误统计", lambda p: p["statistics"].update(candidate_companies=999)),
        ("类型为bool的统计", lambda p: p["statistics"].update(candidate_companies=True)),
        ("未授权最终ID", lambda p: p["companies"][0].update(company_id="FINAL")),
        ("多地区证据丢失", lambda p: next(c for c in p["companies"] if c["normalized_key"] == "AAMI").update(country_regions=["新加坡"], country_region="新加坡")),
        ("隐藏复核问题", lambda p: p["companies"][0].update(review_required=False, review_reason="", review_reasons=[])),
    ]
    for name, mutate in probes:
        broken = deepcopy(good)
        mutate(broken)
        problems, _ = validate(broken, source)
        assert problems, f"负例未拦截：{name}"
    for level in (1, 2):
        broken = deepcopy(good)
        for c in broken["companies"]:
            c["occurrences"] = [o for o in c["occurrences"] if o["level"] != level]
        problems, _ = validate(broken, source)
        assert any(f"L{level}遗漏" in p for p in problems)
    invalid_source = deepcopy(source)
    invalid_source["equipment"]["tracks"][0]["subs"][0]["global_leaders"] = "错误类型"
    for action in (source_index, extract):
        try:
            action(invalid_source)
        except ValueError:
            pass
        else:
            raise AssertionError("源leader非数组未拦截")
    print(f"SELF-TEST PASS：真实边界案例、{len(probes)}项破坏性负例、一级/二级遗漏与源类型异常")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="运行内存边界及负例测试")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        pool = json.loads((HERE / "company_pool_draft.json").read_text(encoding="utf-8-sig"))
        sources = {ds: json.loads((BASE / f"{ds}.json").read_text(encoding="utf-8-sig")) for ds in ("equipment", "materials")}
        errors, reviews = validate(pool, sources)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: 文件加载/源结构错误：{exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}")
    company_rows = pool.get("companies", []) if isinstance(pool, dict) else []
    if not isinstance(company_rows, list):
        company_rows = []
    review_companies = sum(isinstance(c, dict) and c.get("review_required") is True for c in company_rows)
    print(f"Review: {review_companies}个候选需研究复核，明细见company_pool_review.md")
    for item in reviews:
        print(f"REVIEW: {item}")
    if errors:
        print(f"FAIL: {len(errors)}个Error")
        return 1
    print(f"PASS: {len(company_rows)}个候选；一级/二级引用全覆盖、类型、代码、地区、重复及JSON重载校验通过（exit code 0）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
