# -*- coding: utf-8 -*-
"""交叉核验：verify_out 中所有 A股/港股/美股 listing 的 ticker 用 gtimg 实时接口反查名称，
与实体名称比对。输出不一致清单。运行：python crosscheck_tickers.py"""
import json, glob, os, re, time, urllib.request, unicodedata, sys

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0'}

def gtimg(sym):
    url = 'https://qt.gtimg.cn/q=' + sym
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=8) as r:
            txt = r.read().decode('gb18030', errors='replace')
        m = re.search(r'v_\w+="([^"]+)"', txt)
        if not m:
            return None
        parts = m.group(1).split('~')
        return parts[1] if len(parts) > 2 and parts[1] else None
    except Exception:
        return None

def norm(s):
    s = unicodedata.normalize('NFKC', str(s or ''))
    return re.sub(r'(股份有限公司|有限责任公司|有限公司|集团|控股|科技|电子|半导体|股份|\s)', '', s.upper())

mismatch, checked, failed = [], 0, []
for f in sorted(glob.glob(os.path.join(BASE, 'verify_out', '*.result.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for e in d.get('entities', []):
        for l in (e.get('listings') or []):
            sym = ((l.get('provider_symbols') or {}).get('tencent'))
            if not sym:
                continue
            checked += 1
            name = gtimg(sym)
            time.sleep(0.12)
            if name is None:
                failed.append(f"{e.get('company_id')} {l.get('ticker')} ({sym}) 接口未返回")
                continue
            names = {norm(e.get('name_cn')), norm(e.get('short_name')), norm(e.get('name_en'))} | {norm(a) for a in (e.get('aliases') or [])}
            nn = norm(name)
            if not any(nn and x and (nn in x or x in nn) for x in names):
                mismatch.append(f"{e.get('company_id')}: {l.get('ticker')} gtimg名='{name}' vs 实体名 cn={e.get('name_cn')} en={e.get('name_en')}")
print(f'核验 {checked} 只证券；名称不一致 {len(mismatch)}；接口失败 {len(failed)}')
for m in mismatch: print('  [不一致]', m)
for x in failed: print('  [失败]', x)
sys.exit(1 if mismatch else 0)
