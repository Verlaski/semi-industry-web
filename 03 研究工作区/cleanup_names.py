# -*- coding: utf-8 -*-
"""清理 data/{equipment,materials}.json 中 leader 名称与国别重复的问题：
- 名称末尾括号为纯国别且与 country 字段重复 → 去除括号
- 混合括号（如 "Atlas Copco旗下，英/瑞典"）→ 仅剔除国别词，保留其余信息
- china_leaders 的 country 为 中/中国 → 置空（国内列不重复标注）
会就地改写文件并打印改动清单。"""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))
TOKENS = {'中', '中国', '美', '日', '韩', '台', '荷', '德', '英', '法', '瑞士', '瑞典', '意', '以色列', '新', '新加坡', '奥', '奥地利', '马来西亚', '加'}

def is_pure_country(s):
    parts = re.split(r'[/、，,\s]+', s.strip())
    return all(p in TOKENS for p in parts if p)

def clean_name(name, country):
    m = re.search(r'[（(]([^）)]{1,24})[）)]\s*$', name)
    if not m:
        return name, None
    inner = m.group(1)
    if is_pure_country(inner):
        return name[:m.start()].rstrip(), f'去重括号({inner})'
    # 混合内容：剔除国别词，保留其余
    parts = [p for p in re.split(r'[，,]', inner) if p.strip()]
    kept = [p.strip() for p in parts if not is_pure_country(p)]
    if len(kept) != len(parts):
        if kept:
            new = name[:m.start()] + '（' + '，'.join(kept) + '）'
        else:
            new = name[:m.start()].rstrip()
        return new, f'括号剔国别留信息: {inner} → {"，".join(kept) or "(空)"}'
    return name, None

changes = []
for fn in ['equipment.json', 'materials.json']:
    path = os.path.join(BASE, fn)
    d = json.load(open(path, encoding='utf-8'))
    for t in d['tracks']:
        for side in ('global_leaders', 'china_leaders'):
            for l in (t.get(side) or []):
                if side == 'china_leaders' and l.get('country') in ('中', '中国'):
                    l['country'] = ''
                    changes.append(f"{fn}/{t['id']}/{l['name']}: 国内龙头国别置空")
                new_name, why = clean_name(l.get('name', ''), l.get('country', ''))
                if why:
                    changes.append(f"{fn}/{t['id']}: {l['name']} → {new_name} [{why}]")
                    l['name'] = new_name
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print(f'共 {len(changes)} 处改动')
for c in changes: print(' ', c)
