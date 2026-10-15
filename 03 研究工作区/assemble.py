# -*- coding: utf-8 -*-
"""汇总 03 研究工作区/research_*.json → 02 交付/半导体装备与材料产业图谱/data/*.json
用法: python assemble.py
校验: 所有被引用的 source_id 必须存在；赛道龙头数量、国产化词表检查。"""
import json, os, sys, collections

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(BASE, '..', '02 交付', '半导体装备与材料产业图谱', 'data'))

STAGES = {'依赖进口', '验证导入', '份额提升', '批量替代', '国际领先'}

def load(name):
    with open(os.path.join(BASE, name), encoding='utf-8') as f:
        return json.load(f)

def main():
    ov   = load('research_overview.json')
    eq_u = load('research_eq_upstream.json')
    eq_f = load('research_eq_front.json')
    eq_b = load('research_eq_back.json')
    m_f  = load('research_mat_fab.json')
    m_p  = load('research_mat_pkg.json')

    errors, warnings = [], []

    # ---- sources 合并去重 ----
    merged, seen = [], {}
    for src_file, d in [('overview', ov), ('eq_u', eq_u), ('eq_f', eq_f),
                        ('eq_b', eq_b), ('m_f', m_f), ('m_p', m_p)]:
        for s in d.get('sources', []):
            sid = s.get('source_id')
            if not sid:
                errors.append(f'{src_file}: 存在缺 source_id 的来源')
                continue
            if sid in seen:
                prev = seen[sid]
                if (prev.get('org'), prev.get('title')) != (s.get('org'), s.get('title')):
                    warnings.append(f'source_id 冲突: {sid} 在多处定义且内容不同（保留首见）')
                continue
            seen[sid] = s
            merged.append(s)

    # ---- 引用完整性 + 字段检查 ----
    def check_ref(sid, where):
        if sid and sid not in seen:
            errors.append(f'{where}: 引用了不存在的 {sid}')

    def check_track(t, ctx):
        where = f"{ctx}/{t.get('id')}"
        if t.get('name') is None: errors.append(f'{where}: 缺 name')
        gl = t.get('global_leaders') or []
        cl = t.get('china_leaders') or []
        if len(gl) < 2: warnings.append(f'{where}({t.get("name")}): 全球龙头仅 {len(gl)} 家（规范要求≥2）')
        if len(gl) > 5: warnings.append(f'{where}({t.get("name")}): 全球龙头 {len(gl)} 家（规范要求≤5）')
        if not cl and '国内暂无' not in (t.get('note') or ''):
            warnings.append(f'{where}({t.get("name")}): 无国内龙头且 note 未注明')
        loc = t.get('localization') or {}
        if loc.get('stage') and loc['stage'] not in STAGES:
            errors.append(f'{where}: 国产化阶段 "{loc["stage"]}" 不在词表内')
        if loc.get('stage') and not loc.get('scope'):
            warnings.append(f'{where}({t.get("name")}): 国产化缺适用产品范围 scope')
        for l in gl + cl:
            check_ref(l.get('source_id'), where + '/' + str(l.get('name')))
        if t.get('market_size'): check_ref(t['market_size'].get('source_id'), where + '/market_size')
        if loc.get('source_id'): check_ref(loc.get('source_id'), where + '/localization')

    eq_tracks = eq_u['tracks'] + eq_f['tracks'] + eq_b['tracks']
    ma_tracks = m_f['tracks'] + m_p['tracks']
    for t in eq_tracks: check_track(t, 'equipment')
    for t in ma_tracks: check_track(t, 'materials')
    for f_ in ov.get('facts', []): check_ref(f_.get('source_id'), 'facts/' + str(f_.get('key')))
    for r in ov.get('equipment_top', []): check_ref(r.get('source_id'), 'equipment_top/' + str(r.get('name')))
    for n in ov.get('trend_notes', []): check_ref(n.get('source_id'), 'trend_notes')
    for k, p in (ov.get('prosperity') or {}).items():
        for sid in p.get('source_ids', []): check_ref(sid, f'prosperity/{k}')
    for f_ in eq_f.get('wfe_facts', []): check_ref(f_.get('source_id'), 'wfe_facts')

    # ---- meta.json ----
    meta = {
        "site_title": "半导体装备与材料产业链图谱",
        "industry_name": "半导体装备与材料",
        "version": "v1.0",
        "updated": "2026-10-15",
        "dept": "",
        "stage_vocab": ["依赖进口", "验证导入", "份额提升", "批量替代", "国际领先"],
        "prosperity": ov.get('prosperity'),
        "facts": ov.get('facts'),
        "drivers": ov.get('drivers'),
        "equipment_top": ov.get('equipment_top'),
        "trend_notes": ov.get('trend_notes'),
        "downstream": {
            "note": "下游为装备与材料的共同应用环节，仅列代表性厂商，不穷举、不标注份额。",
            "nodes": [
                {"name": "晶圆代工", "players": ["台积电(台)", "三星代工(韩)", "中芯国际", "华虹"], "note": "先进逻辑与成熟制程代工"},
                {"name": "存储制造", "players": ["三星(韩)", "SK海力士(韩)", "美光(美)", "长江存储", "长鑫存储"], "note": "DRAM / NAND / HBM"},
                {"name": "IDM 与特色工艺", "players": ["英特尔(美)", "德州仪器(美)", "华润微", "士兰微"], "note": "功率/模拟/传感等特色工艺"},
                {"name": "封装测试（OSAT）", "players": ["日月光(台)", "安靠(美)", "长电科技", "通富微电", "华天科技"], "note": "传统封测与先进封装产线"}
            ]
        },
        "overview_note": "口径说明：装备链与材料链为两条并行投入链，共同汇入晶圆制造与封装测试，不存在「材料→设备」的串联关系。石英、陶瓷、硅制品等作为设备内部零部件与工艺耗材归入装备图谱上游，材料图谱不重复收录；CMP 设备归装备、抛光液/抛光垫等耗材归材料。",
        "methodology_note": "数据纪律：市占率不与收入排名、出货量、装机量、产能等指标混用；无市场份额数据时明确标注「N/A（按收入排名）」等；同一指标多来源冲突时在备注中记录差异；D 级证据不单独支撑核心结论。点击图谱中金色 [n] 角标可跳转至对应来源条目。",
        "footer_note": "本站为行业图谱专项研究成果，数据均来自公开渠道并注明来源与报告期，仅供内部研究参考，不构成投资建议。",
        "version_log": [
            {"version": "v1.0", "date": "2026-10-15", "note": "首版发布：装备链 23 赛道（零部件 12 + 前道 9 + 后道 2）、材料链 15 赛道（制造材料 8 + 封装材料 7），全部关键数据绑定来源与证据等级；WFE 等旧内部口径已按 SEMI 最新公开数据重核。"}
        ]
    }

    equipment = {
        "industry": "半导体装备",
        "intro": "以晶圆制造前道工艺流程为主线组织九大前道设备赛道，后道独立建立封装设备与测试设备；上游核心零部件与子系统单列十二赛道（装备价值与国产替代的关键支撑层）；下游为设备客户，仅列代表性厂商。点击赛道卡片展开龙头明细，点击 [n] 角标溯源。",
        "wfe_facts": eq_f.get('wfe_facts', []),
        "tracks": eq_tracks
    }
    materials = {
        "industry": "半导体材料",
        "intro": "聚焦直接进入半导体制造流程的电子材料：晶圆制造材料八大赛道（硅片、光掩膜、光刻胶及配套、电子特气、湿电子化学品、CMP 抛光材料、溅射靶材、前驱体）与封装材料七大赛道；基础原料仅示意转换关系，不穷举公司。",
        "base_materials": m_p.get('base_materials', []),
        "tracks": ma_tracks
    }

    os.makedirs(OUT, exist_ok=True)
    def dump(name, obj):
        p = os.path.join(OUT, name)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        print(f'写入 {name}: {os.path.getsize(p)} bytes')

    dump('meta.json', meta)
    dump('equipment.json', equipment)
    dump('materials.json', materials)
    dump('sources.json', {"sources": merged})

    print(f'\n赛道统计: 装备 {len(eq_tracks)}（上游{len(eq_u["tracks"])}/前道{len(eq_f["tracks"])}/后道{len(eq_b["tracks"])}）'
          f' 材料 {len(ma_tracks)}（制造{len(m_f["tracks"])}/封装{len(m_p["tracks"])}） 来源 {len(merged)} 条')
    print(f'证据等级分布: {dict(collections.Counter(s.get("level","?") for s in merged))}')
    print(f'\n错误 {len(errors)} 条:')
    for e in errors: print('  [E]', e)
    print(f'警告 {len(warnings)} 条:')
    for w in warnings: print('  [W]', w)
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
