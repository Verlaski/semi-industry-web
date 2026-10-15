"""报告结构与内容由底层数据构造，不保存每份报告的硬编码正文。"""
from collections import Counter
from datetime import datetime, timezone, timedelta
from .models import ReportModel, SectionModel, TableModel

TITLES = {"overview": "半导体装备与材料产业链总览", "equipment": "半导体装备产业图谱", "materials": "半导体材料产业图谱", "landscape": "半导体竞争格局与国产化"}


def value(v):
    return "" if v is None else str(v)


def leaders(track):
    rows = []
    for role, field in (("全球", "global_leaders"), ("中国", "china_leaders")):
        for leader in track.get(field, []):
            if isinstance(leader, str):
                rows.append([role, leader, "待补充", ""])
            else:
                identity = leader.get("name") or leader.get("company_id", "待补充")
                description = "；".join(leader[k] for k in ("share", "products", "tag") if leader.get(k))
                rows.append([role, identity, leader.get("country", "待补充"), description])
    return rows


def source_ids(obj):
    found = set()
    def walk(v):
        if isinstance(v, dict):
            for k, item in v.items():
                if k == "source_id" and isinstance(item, str):
                    found.add(item)
                elif k == "source_ids" and isinstance(item, list):
                    found.update(item)
                else:
                    walk(item)
        elif isinstance(v, list):
            for item in v:
                walk(item)
    walk(obj)
    return found


def build_report(snapshot, report_type, filters=None, quotes=None, generated_at=None):
    if report_type not in TITLES:
        raise ValueError("暂不支持该报告类型；公司报告需等待正式公司数据库")
    filters = filters or {}
    if set(filters) - {"track_id", "stage"}:
        raise ValueError("不支持的报告筛选字段")
    tracks = snapshot["tracks"]
    if report_type in ("equipment", "materials"):
        tracks = [t for t in tracks if t["dataset"] == report_type]
    if filters.get("track_id"):
        tracks = [t for t in tracks if t["id"] == filters["track_id"]]
    if filters.get("stage"):
        tracks = [t for t in tracks if t.get("localization", {}).get("stage") == filters["stage"]]
    if not tracks:
        raise ValueError("筛选条件下没有赛道")
    sections, used = [], set()
    count = Counter(t.get("localization", {}).get("stage", "待补充") for t in tracks)
    summary = ["装备链与材料链作为两条并行投入链，汇入晶圆制造与封装测试。",
               f"本报告覆盖{len(tracks)}个一级赛道；研究数据更新日期为{snapshot['meta'].get('updated', '待补充')}。",
               "国产化阶段分布：" + "、".join(f"{k}{v}个赛道" for k, v in count.items()) + "。",
               "公司名单、份额及排名按原始赛道口径展示；上市身份和组合主体待正式公司主数据库核验。"]
    if report_type == "overview":
        for dataset, label in (("equipment", "装备链"), ("materials", "材料链")):
            selected = [t for t in tracks if t["dataset"] == dataset]
            rows = [[t["group"], t["name"], t.get("localization", {}).get("stage", "待补充"),
                     "、".join(x.get("name", x.get("company_id", "")) if isinstance(x, dict) else x for x in t.get("global_leaders", [])),
                     "、".join(x.get("name", x.get("company_id", "")) if isinstance(x, dict) else x for x in t.get("china_leaders", []))] for t in selected]
            used.update(source_ids(selected))
            sections.append(SectionModel(label + "赛道总览", [snapshot[dataset].get("intro", "")],
                [TableModel(["分组", "赛道", "国产化", "全球龙头", "中国龙头"], rows, [2.0, 2.8, 1.6, 5.2, 4.6])], sorted(source_ids(selected)), True))
    elif report_type == "landscape":
        rows = [[t["name"], t.get("localization", {}).get("stage", "待补充"), t.get("localization", {}).get("scope", ""), t.get("localization", {}).get("evidence", "")] for t in tracks]
        used.update(source_ids(tracks))
        sections.append(SectionModel("国产化阶段矩阵", [], [TableModel(["赛道", "阶段", "适用范围", "判断依据"], rows, [3.0, 1.8, 4.4, 7.0])], sorted(used), True))
        trends = snapshot["meta"].get("trend_notes", [])
        sections.append(SectionModel("格局变化与技术趋势", [x.get("text", "") if isinstance(x, dict) else x for x in trends], [], sorted(source_ids(trends)), True))
        used.update(source_ids(trends))
    else:
        prior_group = None
        for t in tracks:
            paragraphs = ["产业链位置：" + t.get("chain_position", "") + "；分组：" + t.get("group", "")]
            scale = t.get("market_size", {})
            if scale:
                paragraphs.append("市场规模：" + value(scale.get("value")) + scale.get("unit", "") + "；年份：" + value(scale.get("year")) + "；范围：" + scale.get("scope", ""))
            loc = t.get("localization", {})
            paragraphs += ["国产化阶段：" + loc.get("stage", "待补充") + "；适用范围：" + loc.get("scope", ""), "判断依据：" + loc.get("evidence", "")]
            if t.get("note"):
                paragraphs.append("备注：" + t["note"])
            tables = [TableModel(["角色", "企业（原始名称）", "国别", "份额 / 排名 / 产品"], leaders(t), [1.3, 4.3, 1.5, 9.1])]
            for sub in t.get("subs", []):
                text = "二级细分 · " + sub["name"] + "：" + sub.get("note", "")
                for field, label in (("global_leaders", "全球"), ("china_leaders", "中国")):
                    if sub.get(field):
                        text += "；" + label + "：" + "；".join(value(x.get("name", x.get("company_id", ""))) if isinstance(x, dict) else x for x in sub[field])
                paragraphs.append(text)
            refs = source_ids(t)
            sections.append(SectionModel(t["name"], paragraphs, tables, sorted(refs), t.get("group") != prior_group))
            prior_group = t.get("group")
            used.update(refs)
    facts = snapshot["meta"].get("facts", []) if report_type in ("overview", "landscape") else snapshot["equipment"].get("wfe_facts", []) if report_type == "equipment" else []
    if facts:
        rows = [[f.get("label", ""), value(f.get("value")) + f.get("unit", ""), value(f.get("year")), f.get("scope", f.get("region", "")), f.get("source_id", "")] for f in facts]
        sections.insert(0, SectionModel("关键市场数据", [], [TableModel(["指标", "数值", "年份", "范围 / 口径", "来源"], rows, [4.1, 3.2, 1.5, 4.0, 3.4])], sorted(source_ids(facts)), True))
        used.update(source_ids(facts))
    sources = [s for s in snapshot["sources"]["sources"] if s["source_id"] in used]
    if used - {s["source_id"] for s in sources}:
        raise ValueError("报告存在未解析的来源编号")
    generated_at = generated_at or datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    return ReportModel(report_type, TITLES[report_type], snapshot["data_version"], generated_at,
                       summary, sections, sources, snapshot["meta"].get("footer_note", "仅供研究参考，不构成投资建议。"), quotes or [])
