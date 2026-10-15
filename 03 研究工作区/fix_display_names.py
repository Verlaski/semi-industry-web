# -*- coding: utf-8 -*-
"""显示名修正：对已迁移 leader（带 company_id）按最终规则重写 name。
规则与 migrate_relations.py 的 display_name 一致：short_name 优先，拉丁后缀取 ≤16 字符的英文名/别名。"""
import json, os, re, sys, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get('SITE_DATA_DIR') or os.path.normpath(os.path.join(BASE, '..', '02 交付', '半导体装备与材料产业图谱', 'data'))

CORP_SUFFIX = re.compile(r'\b(INC|CO|LTD|CORP|CORPORATION|GMBH|AG|SA|S\.A|LLC|LLP|PLC|HOLDINGS|HLDGS|KK|K\.K)\b\.?|(股份有限公司|有限责任公司|有限公司|股份公司|株式会社|有限会社)$', re.I)

def norm(s):
    s = unicodedata.normalize('NFKC', str(s or '')).upper()
    s = CORP_SUFFIX.sub(' ', s)
    return re.sub(r'[^\w\u4e00-\u9fff&/-]', '', s, flags=re.UNICODE)

def display_name(c):
    short = c.get('short_name') or c.get('name_cn') or c.get('name_en') or c['company_id']
    cands = [c.get('name_en') or ''] + [a for a in (c.get('aliases') or [])]
    for latin in cands:
        if latin and not re.search(r'[\u4e00-\u9fff]', latin) and len(latin) <= 16 and norm(latin) not in norm(short):
            return f'{short} {latin}'.strip()
    return short

companies = {c['company_id']: c for c in json.load(open(os.path.join(SITE, 'companies.json'), encoding='utf-8'))['companies']}
changed = 0
for fn in ['equipment.json', 'materials.json']:
    path = os.path.join(SITE, fn)
    data = json.load(open(path, encoding='utf-8'))
    for t in data['tracks']:
        nodes = [t] + list(t.get('subs') or [])
        for obj in nodes:
            for fld in ('global_leaders', 'china_leaders'):
                for l in (obj.get(fld) or []):
                    if isinstance(l, dict) and l.get('company_id') in companies:
                        new = display_name(companies[l['company_id']])
                        if l.get('name') != new:
                            l['name'] = new
                            changed += 1
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'显示名修正 {changed} 处')
