# -*- coding: utf-8 -*-
"""把 company_pool_draft.json 的 249 候选行组织成研究批次文件。
批次策略：主体异常（slash/duplicate/relationship）优先独立成批；其余按地区分批。
输出 verify_batches/batch_*.json + 打印各批数量。"""
import json, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'verify_batches')
os.makedirs(OUT, exist_ok=True)

rows = json.load(open(os.path.join(BASE, 'company_pool_draft.json'), encoding='utf-8'))['companies']

def cats(r):
    return {x.get('category') for x in (r.get('review_reasons') or [])}

def slim(r):
    return {
        'key': r['normalized_key'],
        'name_cn': r.get('name_cn') or '', 'name_en': r.get('name_en') or '',
        'raw_names': r.get('raw_names') or [],
        'cn_variants': r.get('name_cn_variants') or [], 'en_variants': r.get('name_en_variants') or [],
        'region': r.get('country_region') or '', 'regions_evidence': r.get('country_regions') or [],
        'ticker_hints': r.get('ticker_hints') or ([r['ticker_hint']] if r.get('ticker_hint') else []),
        'notes': r.get('notes') or [],
        'reviews': [f"{x.get('category')}: {x.get('reason')}" for x in (r.get('review_reasons') or [])],
        'occurrence_count': len(r.get('occurrences') or [])
    }

e1, e2, regional = [], [], []
for r in rows:
    c = cats(r)
    if c & {'slash', 'duplicate'}:
        e1.append(slim(r))
    elif 'relationship' in c:
        e2.append(slim(r))
    else:
        regional.append((r, slim(r)))

CN, JP, US, EU, KRTW, UNKNOWN = [], [], [], [], [], []
EU_REGIONS = {'荷兰', '德国', '英国', '法国', '瑞士', '奥地利', '意大利'}
for r, s in regional:
    reg = s['region']
    if reg == '中国':
        CN.append(s)
    elif reg == '日本':
        JP.append(s)
    elif reg == '美国':
        US.append(s)
    elif reg in EU_REGIONS:
        EU.append(s)
    elif reg in ('韩国', '中国台湾', '新加坡') or '/' in reg:
        KRTW.append(s)
    elif not reg:
        # 缺失地区：有中文名视作中国候选，否则入 unknown
        (CN if s['name_cn'] else UNKNOWN).append(s)
    else:
        UNKNOWN.append(s)

def dump(name, items):
    p = os.path.join(OUT, name)
    json.dump({'batch': name, 'count': len(items), 'rows': items}, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{name}: {len(items)}')

dump('batch_e1_slash_dup.json', e1)
dump('batch_e2_relationship.json', e2)
for i in range(0, len(CN), 30):
    dump(f'batch_cn_{i//30+1}.json', CN[i:i+30])
for i in range(0, len(JP), 35):
    dump(f'batch_jp_{i//35+1}.json', JP[i:i+35])
dump('batch_us.json', US)
dump('batch_eu.json', EU)
dump('batch_kr_tw_other.json', KRTW)
dump('batch_unknown.json', UNKNOWN)
print('总计:', len(e1)+len(e2)+len(CN)+len(JP)+len(US)+len(EU)+len(KRTW)+len(UNKNOWN), '/ 249')
