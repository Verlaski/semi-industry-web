# -*- coding: utf-8 -*-
"""离线提取研究候选池，只写同目录三个草稿，不分配最终company_id。

python "03 研究工作区/extract_companies.py"
相同中/英文清洗名粗去重；品牌、母子公司和简称包含关系不武断合并。
"""
from __future__ import annotations
import collections
import json
from pathlib import Path
import re
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "02 交付" / "半导体装备与材料产业图谱" / "data"
COUNTRY_MAP = {
    "中": "中国", "中国": "中国", "中国大陆": "中国", "美": "美国", "美国": "美国",
    "日": "日本", "日本": "日本", "韩": "韩国", "韩国": "韩国", "台": "中国台湾",
    "中国台湾": "中国台湾", "港": "中国香港", "中国香港": "中国香港", "荷": "荷兰",
    "荷兰": "荷兰", "德": "德国", "德国": "德国", "英": "英国", "英国": "英国",
    "法": "法国", "法国": "法国", "瑞士": "瑞士", "瑞典": "瑞典", "新": "新加坡",
    "新加坡": "新加坡", "奥": "奥地利", "奥地利": "奥地利", "以色列": "以色列",
    "意": "意大利", "意大利": "意大利", "加": "加拿大", "加拿大": "加拿大",
    "马来": "马来西亚", "马来西亚": "马来西亚",
}
CATEGORIES = {
    "duplicate": "疑似重复主体", "slash": "斜杠组合企业",
    "relationship": "母公司 / 子公司 / 品牌关系", "ticker": "股票代码异常或待确认",
    "country": "国家地区缺失", "name": "中文英文名称无法可靠对应",
    "ticker_collision": "同一 ticker_hint 对应多个候选主体", "other": "其他无法机械判断的问题",
}
CJK = re.compile(r"[\u3400-\u9fff]")
BRACKET = re.compile(r"[（(]([^（）()]*)[）)]")
TICKER = re.compile(r"(?<![A-Za-z0-9])(?:[A-Z]\d{5,6}|\d{4,6}(?:\.[A-Z]{1,6})?)(?![A-Za-z0-9])")


def key_for(value):
    """草稿辅助键，保留变音字母、&、/、-，不是最终主键。"""
    value = unicodedata.normalize("NFKC", value).upper()
    return "".join(c for c in value if c.isalnum() or c in "&/-")


def split_top(text, separators):
    pieces, start, depth = [], 0, 0
    for i, char in enumerate(text):
        if char in "(（":
            depth += 1
        elif char in ")）":
            depth -= 1
            if depth < 0:
                raise ValueError(f"括号不配对：{text}")
        elif depth == 0 and char in separators:
            pieces.append(text[start:i].strip())
            start = i + 1
    if depth:
        raise ValueError(f"括号不配对：{text}")
    pieces.append(text[start:].strip())
    return [p for p in pieces if p]


def country_parts(raw):
    return [COUNTRY_MAP.get(x.strip(), x.strip()) for x in re.split(r"[/／]", raw) if x.strip()]


def reference_pieces(text):
    """拆明确并列、剥离冒号后说明；斜杠整体保留待研究。"""
    pieces = []
    for index, clause in enumerate(split_top(text, ";；")):
        parts = split_top(clause, ":：")
        # 冒号后的分号常延续说明，如“；TCB约17%”或“；大陆首家…”。
        # 新企业分句须有独立冒号；其余内容仍完整留在source_text。
        if index and len(parts) == 1 and len(split_top(text, ":：")) > 1:
            continue
        head = parts[0]
        pieces.extend(split_top(head, "、·"))
    return pieces


def parse_name(raw, country_raw=""):
    notes, tickers, countries = [], [], country_parts(country_raw)

    def remove_bracket(match):
        inner = match.group(1).strip()
        tokens = re.split(r"[，,]", inner, maxsplit=1)
        first = tokens[0].strip()
        regions = first.split("/")
        if first in COUNTRY_MAP or all(x in COUNTRY_MAP for x in regions):
            countries.extend(COUNTRY_MAP[x] for x in regions)
            if len(tokens) > 1:
                notes.append(tokens[1].strip())
        elif "/" in first and first.split("/")[0] in COUNTRY_MAP:
            countries.append(COUNTRY_MAP[first.split("/")[0]])
            notes.append(inner)
        else:
            tickers.extend(TICKER.findall(inner))
            rest = TICKER.sub("", inner).strip(" ，,")
            if rest:
                notes.append(rest)
        return " "

    cleaned = BRACKET.sub(remove_bracket, raw)
    tickers.extend(TICKER.findall(cleaned))
    cleaned = " ".join(TICKER.sub("", cleaned).split()).strip()
    cn = en = ""
    if "/" in cleaned or "／" in cleaned:
        # 组合中英名称不能可靠一对一对应，保留整段而不制造配对。
        if CJK.search(cleaned):
            cn = cleaned
        else:
            en = cleaned
    elif CJK.search(cleaned):
        first_cjk = CJK.search(cleaned).start()
        # JX金属 JX Metals 是中文在前；KLA科磊无空格也可拆开。
        cn_first = re.match(r"^(.+?[\u3400-\u9fff][^\s]*)\s+([A-Za-z].*)$", cleaned)
        if cn_first and not CJK.search(cn_first.group(2)):
            cn, en = cn_first.groups()
        elif first_cjk > 0:
            en, cn = cleaned[:first_cjk].strip(), cleaned[first_cjk:].strip()
        else:
            cn = cleaned
    else:
        en = cleaned
    return dict(name_cn=cn, name_en=en, cleaned_name=cleaned,
                ticker_hints=sorted(set(tickers)), notes=notes, country_regions=sorted(set(countries)))


def load_sources():
    return {ds: json.loads((BASE / f"{ds}.json").read_text(encoding="utf-8-sig"))
            for ds in ("equipment", "materials")}


def iter_leaders(sources):
    """遇到新结构或错误类型直接失败，避免静默跳过。"""
    for ds, data in sources.items():
        if not isinstance(data, dict) or not isinstance(data.get("tracks"), list):
            raise ValueError(f"{ds}: tracks 必须为数组")
        seen = set()
        for ti, track in enumerate(data["tracks"]):
            if not isinstance(track, dict) or not isinstance(track.get("id"), str) or not track["id"]:
                raise ValueError(f"{ds}/tracks/{ti}: 赛道结构异常")
            if track["id"] in seen:
                raise ValueError(f"{ds}: 重复 track_id {track['id']}")
            seen.add(track["id"])
            subs = track.get("subs", [])
            if not isinstance(subs, list):
                raise ValueError(f"{ds}/{track['id']}: subs 必须为数组")
            containers = [(track, None, f"/tracks/{ti}")]
            containers.extend((s, si, f"/tracks/{ti}/subs/{si}") for si, s in enumerate(subs))
            for obj, si, pointer in containers:
                if not isinstance(obj, dict) or (si is not None and not isinstance(obj.get("name"), str)):
                    raise ValueError(f"{ds}{pointer}: 细分结构异常")
                for role in ("global", "china"):
                    field = f"{role}_leaders"
                    leaders = obj.get(field, [])
                    if not isinstance(leaders, list):
                        raise ValueError(f"{ds}{pointer}/{field}: 必须为数组")
                    for li, leader in enumerate(leaders):
                        if isinstance(leader, str):
                            text, country, metadata = leader, "", {}
                        elif isinstance(leader, dict):
                            text, country = leader.get("name"), leader.get("country", "")
                            metadata = {k: v for k, v in leader.items() if k not in ("name", "country")}
                        else:
                            raise ValueError(f"{ds}{pointer}/{field}/{li}: 龙头类型异常")
                        if not isinstance(text, str) or not text.strip() or not isinstance(country, str):
                            raise ValueError(f"{ds}{pointer}/{field}/{li}: name/country 类型异常或名称为空")
                        yield dict(dataset=ds, track_id=track["id"], sub_name="" if si is None else obj["name"],
                                   sub_index=si, level=1 if si is None else 2, role=role, leader_index=li,
                                   source_pointer=f"{pointer}/{field}/{li}", source_text=text,
                                   country_raw=country, source_metadata=metadata)


def add_review(company, category, reason):
    item = dict(category=category, reason=reason)
    if item not in company["review_reasons"]:
        company["review_reasons"].append(item)


def extract(sources):
    references = list(iter_leaders(sources))
    records = []
    for ref in references:
        for pi, piece in enumerate(reference_pieces(ref["source_text"])):
            parsed = parse_name(piece, ref["country_raw"])
            if not parsed["cleaned_name"]:
                raise ValueError(f"清洗后名称为空：{ref['dataset']}{ref['source_pointer']}")
            records.append({**parsed, "occurrence": {**ref, "piece_index": pi, "raw_name": piece,
                                                     "country_regions": parsed["country_regions"]}})
    parents = list(range(len(records)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    aliases = {}
    for i, record in enumerate(records):
        combo = "/" in record["cleaned_name"] or "／" in record["cleaned_name"]
        tokens = [("full", key_for(record["cleaned_name"]))] if combo else [
            (lang, key_for(record[field])) for lang, field in (("cn", "name_cn"), ("en", "name_en")) if record[field]]
        for token in tokens:
            if token in aliases:
                parents[find(i)] = find(aliases[token])
            else:
                aliases[token] = i
    groups = collections.defaultdict(list)
    for i, record in enumerate(records):
        groups[find(i)].append(record)
    companies = []
    for group in groups.values():
        cn = sorted({r["name_cn"] for r in group if r["name_cn"]}, key=lambda s: (-len(s), s))
        en = sorted({r["name_en"] for r in group if r["name_en"]}, key=lambda s: (-len(s), s))
        countries = sorted({v for r in group for v in r["country_regions"]})
        tickers = sorted({v for r in group for v in r["ticker_hints"]})
        c = dict(raw_names=sorted({r["occurrence"]["raw_name"] for r in group}),
                 name_cn=cn[0] if cn else "", name_en=en[0] if en else "",
                 name_cn_variants=cn, name_en_variants=en,
                 normalized_key=key_for(en[0] if en else cn[0]),
                 country_region="/".join(countries), country_regions=countries,
                 country_basis="原始country或名称括号；同名引用汇总，不按china角色推定注册地",
                 ticker_hint=tickers[0] if len(tickers) == 1 else "", ticker_hints=tickers,
                 notes=sorted({n for r in group for n in r["notes"]}),
                 occurrences=[r["occurrence"] for r in group],
                 review_required=False, review_reason="", review_reasons=[])
        if any("/" in r["cleaned_name"] or "／" in r["cleaned_name"] for r in group):
            add_review(c, "slash", "斜杠可能连接不同主体、品牌或别名；保留组合，待逐一判断")
        if not countries:
            add_review(c, "country", "所有引用均无明确国家地区；china角色不等同注册地证明")
        if len(countries) > 1:
            add_review(c, "other", f"原始地区多值或冲突：{' / '.join(countries)}；不得任择一项")
        if any(v not in COUNTRY_MAP.values() for v in countries):
            add_review(c, "other", "存在未识别的国家地区原文，需确认映射")
        if tickers or any(re.search(r"IPO|辅导|上市", n, re.I) for n in c["notes"]):
            add_review(c, "ticker", "原始代码/上市状态仅作线索，未核验交易所、主体及当前状态")
        if any(not re.fullmatch(r"\d{6}", t) for t in tickers):
            add_review(c, "ticker", "包含非六位数字代码（如辅导编号）；不可直接作为证券代码")
        if len(tickers) > 1:
            add_review(c, "ticker", "同名候选存在多个代码提示，保留全部待核验")
        context = " ".join(c["notes"] + [o["source_text"] + " " + str(o["source_metadata"].get("tag", "")) for o in c["occurrences"]])
        if re.search(r"旗下|子公司|收购|并购|并入|控股|集团|原日立|现属|原汉高|背靠", context):
            add_review(c, "relationship", "名称备注或龙头tag涉及集团、子公司、收购或历史名称，需核对法人/品牌/上市母公司边界")
        if c["notes"]:
            add_review(c, "name", "括号包含别名、业务线或身份备注；保留原文，未强配中英文主体")
        if len(cn) > 1 or len(en) > 1:
            add_review(c, "name", "同一清洗名连接多种中英文写法；仅粗去重，仍需核验别名对应")
        companies.append(c)
    # 名称包含关系仅提供线索，不自动合并。
    for i, left in enumerate(companies):
        for right in companies[i + 1:]:
            reasons = []
            for field in ("name_cn_variants", "name_en_variants"):
                for a in left[field]:
                    for b in right[field]:
                        ka, kb = key_for(a), key_for(b)
                        if field == "name_en_variants":
                            # 用完整词边界，避免TEL误中Stella、AMAT误中Hana Materials。
                            aa, bb = a.upper(), b.upper()
                            similar = min(len(ka), len(kb)) >= 3 and (
                                re.search(r"(?<!\w)" + re.escape(aa) + r"(?!\w)", bb)
                                or re.search(r"(?<!\w)" + re.escape(bb) + r"(?!\w)", aa))
                        else:
                            similar = min(len(ka), len(kb)) >= 3 and (ka in kb or kb in ka)
                        if similar:
                            reasons.append(f"名称片段相近：{a} / {b}")
            if reasons:
                reason = "；".join(sorted(set(reasons)))
                add_review(left, "duplicate", f"与 {right['normalized_key']} {reason}；不自动合并")
                add_review(right, "duplicate", f"与 {left['normalized_key']} {reason}；不自动合并")
    owners = collections.defaultdict(list)
    for c in companies:
        for ticker in c["ticker_hints"]:
            owners[ticker].append(c)
    for ticker, group in owners.items():
        if len(group) > 1:
            for c in group:
                add_review(c, "ticker_collision", f"{ticker} 同时对应：" + " / ".join(x["normalized_key"] for x in group))
    if len({c["normalized_key"] for c in companies}) != len(companies):
        raise ValueError("粗去重后 normalized_key 冲突，需调整名称归并规则")
    for c in companies:
        c["review_required"] = bool(c["review_reasons"])
        c["review_reason"] = "；".join(r["reason"] for r in c["review_reasons"])
    companies.sort(key=lambda c: (c["country_region"], c["normalized_key"]))
    stats = dict(raw_leader_references=len(references),
                 raw_by_level=dict(collections.Counter(str(r["level"]) for r in references)),
                 raw_by_dataset_level_role=dict(sorted(collections.Counter(f"{r['dataset']}/L{r['level']}/{r['role']}" for r in references).items())),
                 records_before_dedup=len(records), candidate_companies=len(companies),
                 duplicate_records_merged=len(records)-len(companies),
                 review_companies=sum(c["review_required"] for c in companies))
    return dict(schema_version="company-pool-draft-1", stage="仅提取、粗去重和质量检查；不含最终company_id", statistics=stats, companies=companies)


def md(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def location(c):
    return "；".join(f"{o['dataset']}{o['source_pointer']}#{o['piece_index']}" for o in c["occurrences"])


def review_text(pool):
    lines = ["# 龙头公司候选池复核清单", "", "用途：交接无法机械决定的主体及数据问题。读者：人工/研究Agent。",
             "最后更新时间：2026-10-15。对应版本：V1.1 研究准备。", "",
             "本清单从本地数据生成，未做上市核验；分类可交叉。normalized_key不是最终主键。每行列出全部位置，#后为并列拆分序号（从0起）。", ""]
    for i, (cat, title) in enumerate(CATEGORIES.items(), 1):
        entries = [(c, [r["reason"] for r in c["review_reasons"] if r["category"] == cat]) for c in pool["companies"]]
        entries = [(c, reasons) for c, reasons in entries if reasons]
        lines += [f"## {i}. {title}", "", f"涉及 {len(entries)} 个候选行。", ""]
        if not entries:
            lines += ["当前自动检查未检出；不等于已完成主体核验。", ""]
            continue
        lines += ["| 候选辅助键 | 原始名称 | 复核原因 | 完整引用位置 |", "| --- | --- | --- | --- |"]
        lines += [f"| {md(c['normalized_key'])} | {md('；'.join(c['raw_names']))} | {md('；'.join(rs))} | {md(location(c))} |" for c, rs in entries]
        lines.append("")
    return "\n".join(lines)


def report_text(pool):
    companies, stats = pool["companies"], pool["statistics"]
    regions = collections.Counter(c["country_region"] or "缺失" for c in companies)
    levels = {c["normalized_key"]: {o["level"] for o in c["occurrences"]} for c in companies}
    only1 = [c for c in companies if levels[c["normalized_key"]] == {1}]
    only2 = [c for c in companies if levels[c["normalized_key"]] == {2}]
    both = [c for c in companies if levels[c["normalized_key"]] == {1, 2}]
    counts = {cat: sum(any(r["category"] == cat for r in c["review_reasons"]) for c in companies) for cat in CATEGORIES}
    lines = ["# 龙头公司候选池统计与研究准备", "", "用途：说明提取覆盖、统计口径及下一步调研。读者：项目负责人及研究人员。",
             "最后更新时间：2026-10-15。对应版本：V1.1 研究准备（非正式公司库）。", "",
             "本轮仅处理本地源数据，未开展上市信息外部核验。候选行可能仍是组合主体，数量不等于经核实法人数量。", "",
             "## 统计结果", "", "| 指标 | 数量 |", "| --- | ---: |"]
    metrics = [("一级/二级 leader 原始数组引用", stats["raw_leader_references"]),
               ("一级原始引用", stats["raw_by_level"].get("1", 0)), ("二级原始引用", stats["raw_by_level"].get("2", 0)),
               ("明确并列拆开后记录（粗去重前）", stats["records_before_dedup"]),
               ("粗去重后候选公司行", len(companies)), ("自动折叠重复记录（前者减后者）", stats["duplicate_records_merged"]),
               ("不同原始名称写法", len({n for c in companies for n in c["raw_names"]})),
               ("需要复核的候选行", stats["review_companies"]),
               ("含ticker_hint/ticker_hints的候选", sum(bool(c["ticker_hints"]) for c in companies)),
               ("仅一级出现", len(only1)), ("仅二级新增发现", len(only2)), ("一级和二级均出现", len(both))]
    lines += [f"| {k} | {v} |" for k, v in metrics]
    lines += ["", "原始引用按数组元素计数；明确顿号、分号并列可拆出多个occurrence。斜杠不自动拆主体。合并数是重复记录数，不是已验证别名企业对数。", "",
              "| 原始数据/层级/角色 | 引用数 |", "| --- | ---: |"]
    lines += [f"| {k} | {v} |" for k, v in stats["raw_by_dataset_level_role"].items()]
    lines += ["", "| 角色 | 候选行（可交叉） | 拆分后引用 |", "| --- | ---: | ---: |"]
    for role in ("global", "china"):
        lines.append(f"| {role} leader | {sum(any(o['role'] == role for o in c['occurrences']) for c in companies)} | {sum(o['role'] == role for c in companies for o in c['occurrences'])} |")
    lines += ["", "## 国家地区", "", "仅汇总原country和名称明确地区；不按china角色补注册地，多值不任选一项。", "", "| 证据汇总地区 | 候选行 |", "| --- | ---: |"]
    for country in ["中国", "美国", "日本", "韩国", "中国台湾", "荷兰", "德国", "英国", "法国", "瑞士", "奥地利", "新加坡", "中国香港", "其他", "缺失"]:
        lines.append(f"| {country} | {regions.pop(country, 0)} |")
    lines += [f"| 多值/其他原文：{k} | {v} |" for k, v in sorted(regions.items())]
    lines += ["", "## 主要公司主数据脏点", "", "分类可交叉，按涉及候选行数排序。", "", "| 问题类别 | 候选行 |", "| --- | ---: |"]
    lines += [f"| {CATEGORIES[k]} | {v} |" for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
    lines += ["", "核心问题是公司身份和赛道说明混写、国内龙头常缺注册地、简称与全称并存、斜杠多主体，以及母子公司/品牌/收购前后名称边界不清。", "",
              "## 仅一级出现的候选", "", "、".join(c["normalized_key"] for c in only1), "",
              "## 仅二级新增发现的候选", "", "、".join(c["normalized_key"] for c in only2), "",
              "## 处理规则与实施验证", "",
              "1. 读取现有源文件，一级/二级字符串或字典均支持，类型异常立即报错。",
              "2. 拆开明确并列、剥离冒号后说明，提取代码提示，完整保留备注和引用原文；斜杠组合只标记。",
              "3. 相同中/英文清洗名粗去重；所有名称变体、代码、地区和逐条引用均保留，简称包含关系只列复核。",
              "4. 生成草稿、八类复核清单和统计，再独立遍历原始数据校验覆盖、类型及定位。",
              "5. 限定文件范围后本地提交，不推送或合并。", "",
              "原脚本实跑得到285行，含说明文本导致的伪公司，不能当作有效主体数。未发现阻止运行的语法错误；发现逻辑问题：二级字符串仅按中点拆分，说明混入名称；漏拆顿号/分号并列；二级字典被忽略；仅识别末尾括号，中途代码残留；代码备注整体塞入ticker；国内缺地区；中国香港/新加坡被武断归新加坡；只留首个名称、代码、地区及角色；tracks集合丢失逐条原文和位置；正则过滤变音字符。", "",
              "根目录无README.md，以交付目录现有README为准。Windows命令行使用UTF-8及PYTHONIOENCODING=utf-8，脚本也会设置输出编码。", "",
              "## 草稿新增字段说明", "",
              "| 字段 | 类型 | 含义 |", "| --- | --- | --- |",
              "| normalized_key | string | 清洗和粗去重辅助键；不是最终company_id |",
              "| name_cn_variants / name_en_variants | string[] | 同组全部清洗名，代表名称只取其中一项 |",
              "| country_regions / country_region | string[] / string | 全部地区证据；显示值用斜杠连接，多值保留复核 |",
              "| country_basis | string | 地区取值依据，不将china角色当作注册地 |",
              "| ticker_hints / ticker_hint | string[] / string | 全部代码线索；只有唯一值时填单值；未经证券代码核验 |",
              "| review_reasons | object[] | category为八类问题代码，reason为具体原因；与review_required及review_reason同步 |",
              "| occurrences | object[] | 每次有效引用；同一位置并列多家公司分别保留一条 |",
              "| occurrence.dataset / track_id / sub_name / role | string | 数据集、赛道、细分名称、global或china角色 |",
              "| occurrence.level / sub_index / leader_index / piece_index | int / int或null / int / int | 层级1或2；数组位置从0起；一级sub_index为null |",
              "| occurrence.source_pointer | string | 原始JSON中leader元素的精确路径，配合dataset及piece_index定位 |",
              "| occurrence.source_text / raw_name | string | 完整原始leader文字 / 剥离说明后的名称片段 |",
              "| occurrence.country_raw / country_regions | string / string[] | 原始country字段和本次引用的地区证据 |",
              "| occurrence.source_metadata | object | 原始share、tag、products、source_id等赛道关系属性，仅存引用内 |",
              "| statistics | object | 原始引用、拆分记录、候选和复核数量，校验时独立重算 |", "",
              "无最终company_id、上市状态或证券市场确认字段。空地区与组合主体属于已登记Review，结构/覆盖错误属于Error。", "",
              "## 下一阶段上市信息调研批次", "",
              "先解决主体边界及疑似重复，再按国家/市场分批。常规每批15—25个候选，复杂关系每批8—12个。先确定归属，避免交叉领用。", "",
              "1. 主体关系批：斜杠组合、品牌/子公司、收购及疑似重复，先确定拆分、关联或合并。",
              "2. 代码线索批：含代码、IPO或辅导编号，核验法定名称、交易所、代码性质及有效日期。",
              "3. 地区缺失批：用官网或交易所披露确认注册主体/地区，再分配上市研究。",
              "4. 已有地区海外批：日本；美国；中国台湾/韩国；欧洲；其他及多地区分别处理。",
              "5. 整合批：同ticker、多地上市和历史别名交叉核验，最后才确定company_id。", "",
              "每项保留候选辅助键、全部原始引用、确认主体、来源网址、访问日期和结论。normalized_key随清洗规则变化，不是最终company_id。", "",
              "## 范围与复现", "",
              '`python "03 研究工作区/extract_companies.py"` 生成三个草稿；',
              '`python "03 研究工作区/validate_company_pool.py"` 校验。Error非零退出，已列明Review不影响通过。', "",
              "自由文本note中偶然提及的企业未全量识别；括号内收购对象/品牌保留为线索，不自动生成主体。材料二级目前只有note，无结构化leader；未向正式数据补写。", ""]
    return "\n".join(lines)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        pool = extract(load_sources())
        (HERE / "company_pool_draft.json").write_text(json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (HERE / "company_pool_review.md").write_text(review_text(pool), encoding="utf-8")
        (HERE / "company_pool_report.md").write_text(report_text(pool), encoding="utf-8")
        print(json.dumps(pool["statistics"], ensure_ascii=False, indent=2))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
