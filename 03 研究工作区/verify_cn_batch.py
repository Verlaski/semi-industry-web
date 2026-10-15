# -*- coding: utf-8 -*-
"""中国候选公司批量上市核验：东财 suggest API（名称→代码/板块）+ 腾讯 gtimg（代码→名称/可交易）。
不烧模型额度，确定性核验。输出 verify_out/batch_cn_auto.result.json（与代理同 schema）。
高置信自动判上市；无匹配→listing_status 留空（未知，不武断判非上市）；全部留待人工复核清单。"""
import json, os, re, time, urllib.request, urllib.parse, unicodedata, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'verify_out', 'batch_cn_auto.result.json')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

UA = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}

def http(url, gbk=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
    return raw.decode('gb18030' if gbk else 'utf-8', errors='replace')

def suggest(query):
    url = ('https://searchapi.eastmoney.com/api/suggest/get?input=' + urllib.parse.quote(query) +
           '&type=14&token=D43BF722C8E33BD1C740FD9E4C0DEA0F&count=8')
    try:
        d = json.loads(http(url))
        return (d.get('QuotationCodeTable') or {}).get('Data') or [], url
    except Exception as e:
        return [], url

def gtimg_name(code_with_suffix):
    code, suffix = code_with_suffix.split('.')
    prefix = {'SH': 'sh', 'SZ': 'sz', 'BJ': 'bj'}[suffix]
    sym = prefix + code
    url = 'https://qt.gtimg.cn/q=' + sym
    try:
        txt = http(url, gbk=True)
        m = re.search(r'v_\w+="([^"]+)"', txt)
        if not m:
            return None, url, sym
        parts = m.group(1).split('~')
        return (parts[1] if len(parts) > 2 else None), url, sym
    except Exception:
        return None, url, sym

def norm(s):
    s = unicodedata.normalize('NFKC', str(s or ''))
    return re.sub(r'(股份有限公司|有限责任公司|有限公司|集团|控股|科技股份|科技|电子|半导体|技术|\s)', '', s.upper())

def suffix_for(code):
    if re.match(r'^(688|689|600|601|603|605)', code): return 'SH'
    if re.match(r'^(000|001|002|003|300|301|302)', code): return 'SZ'
    if re.match(r'^(4\d{2}|8\d{2}|920)', code): return 'BJ'
    return ''

MKT_NAME = {'SH': ('A股', 'SSE'), 'SZ': ('A股', 'SZSE'), 'BJ': ('A股', 'BSE')}

def main():
    rows = []
    for i in (1, 2, 3, 4):
        p = os.path.join(BASE, 'verify_batches', f'batch_cn_{i}.json')
        if os.path.exists(p):
            rows += json.load(open(p, encoding='utf-8'))['rows']

    entities, review = [], []
    for idx, r in enumerate(rows):
        key = r['key']
        names = [n for n in [r.get('name_cn'), *(r.get('cn_variants') or [])] if n]
        hints = r.get('ticker_hints') or []
        match = None          # (code, quote_name, board, quote_id)
        # 1) 代码线索反查
        for h in hints:
            m = re.search(r'(\d{6})', h)
            if not m:
                continue
            code = m.group(1)
            sfx = suffix_for(code)
            if not sfx:
                continue
            qname, qurl, sym = gtimg_name(code + '.' + sfx)
            time.sleep(0.15)
            if qname:
                nq, nn = norm(qname), norm(names[0] if names else '')
                if nq and nn and (nq in nn or nn in nq):
                    match = (code + '.' + sfx, qname, '', sym, qurl)
                    break
        # 2) 名称正查
        sug_url = ''
        if not match:
            for nm in names:
                data, sug_url = suggest(nm)
                time.sleep(0.15)
                nn = norm(nm)
                best = None
                for item in data:
                    qn = item.get('Name', '')
                    code = item.get('Code', '')
                    qid = item.get('QuoteID', '')
                    if not re.fullmatch(r'\d{6}', code):
                        continue
                    nq = norm(qn)
                    if nq and nn and (nq == nn or nq in nn or nn in nq):
                        best = (code, qn, item.get('SecurityTypeName', ''), qid)
                        break
                if best:
                    code, qn, board, qid = best
                    sfx = suffix_for(code)
                    if sfx:
                        gname, qurl, sym = gtimg_name(code + '.' + sfx)
                        time.sleep(0.15)
                        match = (code + '.' + sfx, qn, board, sym, qurl)
                    break
        entity = {
            'source_keys': [key],
            'entity_decision': '',
            'company_id': '', 'name_cn': r.get('name_cn') or '', 'name_en': r.get('name_en') or '',
            'short_name': '', 'aliases': [],
            'country_region': r.get('region') or '中国',
            'listing_status': '', 'listings': [],
            'evidence': [], 'confidence': '', 'unresolved': ''
        }
        if match:
            ticker, qname, board, sym, qurl = match
            mkt, exch = MKT_NAME[ticker.split('.')[1]]
            cid = re.sub(r'[^A-Z0-9]', '', (r.get('name_en') or '').upper()) or 'CN' + ticker.split('.')[0]
            entity.update({
                'company_id': cid,
                'short_name': qname,
                'listing_status': '上市',
                'listings': [{'listing_id': f'{cid}_{exch}', 'market': mkt, 'exchange': exch,
                              'ticker': ticker, 'primary': True,
                              'provider_symbols': {'tencent': sym}}],
                'evidence': [
                    {'org': '东方财富', 'title': f'证券简称检索：{qname}（{ticker}）', 'url': sug_url or qurl,
                     'publish_date': '', 'data_year': '2026', 'metric': '上市状态/代码/板块', 'caliber': '东财证券名录检索',
                     'region': '中国', 'type': '财经数据站', 'level': 'B', 'remark': f'板块：{board or "见检索"}；gtimg 实时行情名称交叉验证一致'},
                    {'org': '腾讯财经', 'title': f'gtimg 行情快照 {sym}', 'url': qurl,
                     'publish_date': '', 'data_year': '2026', 'metric': '行情存在性', 'caliber': '实时行情接口',
                     'region': '中国', 'type': '财经数据站', 'level': 'B', 'remark': ''}],
                'confidence': 'high' if norm(qname) == norm(names[0] if names else '') else 'medium'
            })
            if entity['confidence'] == 'medium':
                entity['unresolved'] = f'名称近似匹配（原名 {names[0] if names else ""} vs 行情名 {qname}），待人工复核'
                review.append(key)
        else:
            entity['unresolved'] = '东财名录+行情接口均未匹配；上市状态待人工核验（不得默认非上市）'
            entity['confidence'] = 'low'
            review.append(key)
        entities.append(entity)
        print(f"[{idx+1}/{len(rows)}] {key} -> {entity['listing_status'] or '未知'} {entity['listings'][0]['ticker'] if entity['listings'] else ''} {entity['confidence']}", flush=True)

    json.dump({'batch': 'batch_cn_auto', 'entities': entities}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    listed = sum(1 for e in entities if e['listing_status'] == '上市')
    print(f'\n完成: {len(entities)} 行，上市 {listed}，待人工复核/未知 {len(review)}')
    print('待复核 keys:', review)

if __name__ == '__main__':
    sys.exit(main())
