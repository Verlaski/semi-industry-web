# -*- coding: utf-8 -*-
"""合并 verify_out/*.result.json → 站点 data/companies.json + sources.json 新增 SRC-LS- 来源。
运行：python build_companies.py
校验：company_id 唯一、必填字段、listing 词表与 ticker 格式、证据齐全。发现问题非零退出。"""
import json, glob, os, re, sys, collections

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(BASE, '..', '02 交付', '半导体装备与材料产业图谱', 'data'))

MARKETS = {'A股', '港股', '美股', '日股', '欧股', '台股', '韩股', '其他海外'}
MARKET_ALIAS = {'英股': '欧股', '新加坡股': '其他海外', '德国': '欧股', '荷兰': '欧股', '法国': '欧股', '瑞士': '欧股', '奥地利': '欧股', '英国': '欧股'}
STATUS = {'上市', '非上市', ''}
TICKER_RE = re.compile(r'^(\d{6}\.(SH|SZ|BJ)|\d{5}\.HK|[A-Z0-9.\-]+\.US|\d{3,5}\.T|[A-Z0-9.\-]+)$')

def main():
    results = []
    for f in sorted(glob.glob(os.path.join(BASE, 'verify_out', '*.result.json'))):
        d = json.load(open(f, encoding='utf-8'))
        results.append((d.get('batch', os.path.basename(f)), d.get('entities', [])))
    if not results:
        print('verify_out 无结果文件'); sys.exit(1)

    # 人工裁决补丁（可选）：别名增补、名称修正
    patches_path = os.path.join(BASE, 'verify_out', 'manual_patches.json')
    patches = json.load(open(patches_path, encoding='utf-8')) if os.path.exists(patches_path) else {}
    add_aliases = patches.get('add_aliases', {})       # {company_id: [别名...]}
    drop_tokens = patches.get('drop_match_tokens', {}) # {company_id: [不参与匹配的token...]}（实体仍保留该名称字段）
    name_cn_fix = patches.get('name_cn', {})           # {company_id: 中文名}

    errors, warnings = [], []
    entities, seen_ids, key_owner = [], {}, {}

    def auto_id(cid):
        return bool(re.fullmatch(r'CN\d{6}', cid or ''))

    def merge_into(prev, e, batch, why):
        prev['source_keys'] = sorted(set(prev.get('source_keys') or []) | set(e.get('source_keys') or []))
        for f in ('name_cn', 'name_en', 'short_name', 'country_region', 'listing_status'):
            if not prev.get(f) and e.get(f):
                prev[f] = e[f]
        prev['aliases'] = sorted(set((prev.get('aliases') or []) + (e.get('aliases') or [])))
        known = {l.get('ticker') for l in prev.get('listings', [])}
        for l in (e.get('listings') or []):
            if l.get('ticker') not in known:
                prev.setdefault('listings', []).append(l)
                known.add(l.get('ticker'))
        prev.setdefault('evidence', []).extend(e.get('evidence') or [])
        if prev.get('confidence') != 'high' and e.get('confidence') == 'high':
            prev['confidence'] = 'high'
        for f in ('entity_decision', 'unresolved'):
            if e.get(f) and e[f] not in (prev.get(f) or ''):
                prev[f] = ((prev.get(f) or '') + '；' + e[f]).strip('；')
        # id 质量：自动生成的 CN+代码 让位给助记 id
        if auto_id(prev.get('company_id')) and not auto_id(e.get('company_id')) and e.get('company_id'):
            old = prev['company_id']
            if e['company_id'] in seen_ids:
                merge_into(seen_ids[e['company_id']], prev, batch, 'id归并')
                return seen_ids[e['company_id']]
            del seen_ids[old]
            prev['company_id'] = e['company_id']
            seen_ids[prev['company_id']] = prev
        warnings.append(f'实体合并（{why}）: {e.get("company_id")} → {prev["company_id"]}（{batch}）')
        return prev

    for batch, ents in results:
        for e in ents:
            cid = (e.get('company_id') or '').strip().upper()
            keys = e.get('source_keys') or []
            # 组合键（含 /）由拆分出的多个实体共享，不参与 merge 判定
            plain_keys = [k for k in keys if '/' not in k]
            # 1) source_key 重叠 → 同一公司（不同批次/脚本对同一候选行的重复建档）
            prev = next((key_owner[k] for k in plain_keys if k in key_owner), None)
            if prev is not None:
                merge_into(prev, e, batch, 'source_key重叠')
                for k in plain_keys:
                    key_owner[k] = prev
                continue
            if not cid:
                errors.append(f'{batch}: 实体缺 company_id: {e.get("name_cn") or e.get("name_en")}'); continue
            e['company_id'] = cid
            # 2) company_id 相同 → 同一实体跨批次（如 SUSS 在 EU 批与 E1 拆分批）
            if cid in seen_ids:
                prev = seen_ids[cid]
                merge_into(prev, e, batch, 'company_id相同')
                for k in plain_keys:
                    key_owner[k] = prev
                continue
            seen_ids[cid] = e
            for k in plain_keys:
                key_owner[k] = e
            e.setdefault('evidence', [])
            if not (e.get('name_cn') or e.get('name_en')):
                errors.append(f'{cid}: 名称全空')
            st = e.get('listing_status', '')
            if st not in STATUS:
                errors.append(f'{cid}: listing_status="{st}" 不在词表')
            listings = e.get('listings') or []
            if st == '上市' and not listings:
                errors.append(f'{cid}: 上市但无 listings')
            if st != '上市' and listings:
                warnings.append(f'{cid}: 非上市/未知但带 listings，已忽略')
                listings = []
            prim = [l for l in listings if l.get('primary') is True]
            if len(prim) > 1:
                errors.append(f'{cid}: 多个 primary listing')
            if listings and not prim:
                warnings.append(f'{cid}: listings 无 primary，自动置首条'); listings[0]['primary'] = True
            for l in listings:
                mk = l.get('market')
                if mk in MARKET_ALIAS:
                    l['market'] = MARKET_ALIAS[mk]
                    mk = l['market']
                if mk not in MARKETS:
                    errors.append(f'{cid}: market "{mk}" 不在词表')
                tk = l.get('ticker') or ''
                if tk and not TICKER_RE.match(tk):
                    warnings.append(f'{cid}: ticker 格式异常 "{tk}"')
                if not l.get('listing_id'):
                    l['listing_id'] = f"{cid}_{(l.get('exchange') or 'X').replace(' ', '')}"
            if st == '上市' and not e.get('evidence'):
                warnings.append(f'{cid}: 上市但无 evidence')
            e['company_id'] = cid
            e['listings'] = listings
            entities.append(e)

    # 统一 listing_id 规范：{company_id}_{交易所}（各批代理格式不一，归一后供行情注册表引用）
    # 同实体内按 ticker 去重（保留首个，优先带 provider_symbols 的）
    exch_seen = {}
    for e in entities:
        cid = e['company_id']
        tick_seen = {}
        dedup = []
        for l in (e.get('listings') or []):
            tk = l.get('ticker')
            if tk in tick_seen:
                if l.get('provider_symbols') and not tick_seen[tk].get('provider_symbols'):
                    tick_seen[tk]['provider_symbols'] = l['provider_symbols']
                continue
            tick_seen[tk] = l
            dedup.append(l)
        e['listings'] = dedup
        for l in dedup:
            exch = re.sub(r'[^A-Za-z0-9]', '', l.get('exchange') or 'X').upper()
            lid = f'{cid}_{exch}'
            while lid in exch_seen:
                lid += '_2'
            exch_seen[lid] = True
            if l.get('listing_id') != lid:
                l['listing_id'] = lid

    # 终末去重：任何路径导致的同 id 重复对象在此合并
    deduped, seen_final = [], {}
    for e in entities:
        cid = e['company_id']
        if cid in seen_final:
            warnings.append(f'终末去重: {cid} 重复对象已合并')
            merge_into(seen_final[cid], e, 'final', '重复对象')
            continue
        seen_final[cid] = e
        deduped.append(e)
    entities = deduped

    # 合并来源：URL 去重，编号 SRC-LS-NNN（幂等：先剔除上次生成的 SRC-LS- 段）
    src_path = os.path.join(SITE, 'sources.json')
    sources = json.load(open(src_path, encoding='utf-8'))
    srcs = [s for s in sources['sources'] if not str(s.get('source_id', '')).startswith('SRC-LS-')]
    sources['sources'] = srcs
    existing_urls = {s.get('url') for s in srcs}
    existing_ids = {s.get('source_id') for s in srcs}
    n = 0
    url_to_id = {}
    for e in entities:
        ev_ids = []
        for ev in (e.get('evidence') or []):
            url = ev.get('url') or ''
            if url and url in url_to_id:
                ev_ids.append(url_to_id[url]); continue
            n += 1
            sid = f'SRC-LS-{n:03d}'
            while sid in existing_ids:
                n += 1; sid = f'SRC-LS-{n:03d}'
            existing_ids.add(sid)
            if url:
                url_to_id[url] = sid
            srcs.append({
                'source_id': sid, 'org': ev.get('org', ''), 'title': ev.get('title', ''),
                'publish_date': ev.get('publish_date', ''), 'data_year': ev.get('data_year', ''),
                'metric': ev.get('metric', '公司上市信息'), 'caliber': ev.get('caliber', ''),
                'region': ev.get('region', ''), 'url': url, 'access_date': ev.get('access_date', '2026-10-15'),
                'type': ev.get('type', ''), 'level': ev.get('level', 'C'), 'remark': ev.get('remark', '')})
            ev_ids.append(sid)
        e['listing_source_id'] = ev_ids[0] if ev_ids else ''
        e['evidence_source_ids'] = ev_ids

    # companies.json（只保留契约字段 + 研究备注字段）
    companies = []
    for e in entities:
        cid = e['company_id']
        name_cn = name_cn_fix.get(cid, e.get('name_cn', ''))
        aliases = sorted(set((e.get('aliases') or []) + (add_aliases.get(cid) or [])))
        companies.append({
            'company_id': cid,
            'name_cn': name_cn, 'name_en': e.get('name_en', ''),
            'short_name': e.get('short_name', '') or name_cn or e.get('name_en', ''),
            'aliases': aliases,
            'country_region': e.get('country_region', ''),
            'listing_status': e.get('listing_status', ''),
            'listings': e.get('listings') or [],
            'listing_source_id': e.get('listing_source_id', ''),
            'source_keys': e.get('source_keys') or [],
            'entity_decision': e.get('entity_decision', ''),
            'confidence': e.get('confidence', ''),
            'unresolved': e.get('unresolved', '')})
    companies.sort(key=lambda c: (c['country_region'], c['company_id']))

    json.dump({'companies': companies}, open(os.path.join(SITE, 'companies.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    json.dump(sources, open(src_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    by_status = collections.Counter(c['listing_status'] or '未知' for c in companies)
    by_market = collections.Counter(l['market'] for c in companies for l in c['listings'])
    print(f'公司实体: {len(companies)}；上市状态分布: {dict(by_status)}')
    print(f'上市地分布: {dict(by_market)}')
    print(f'新增来源: {n} 条（sources.json 现共 {len(srcs)} 条）')
    low = [c['company_id'] for c in companies if c['confidence'] == 'low']
    unres = [c['company_id'] for c in companies if c['unresolved']]
    print(f'低置信: {len(low)} {low[:15]}')
    print(f'有未决项: {len(unres)} {unres[:15]}')
    print(f'\n错误 {len(errors)}:'); [print('  [E]', x) for x in errors]
    print(f'警告 {len(warnings)}:'); [print('  [W]', x) for x in warnings[:40]]
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
