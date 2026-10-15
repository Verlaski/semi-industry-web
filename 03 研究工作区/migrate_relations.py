# -*- coding: utf-8 -*-
"""赛道关系迁移 v2：equipment.json / materials.json 的一级+二级 leader 全部挂上 company_id。
匹配逻辑与站点 domain.js 的 pieces()/parseName()/norm() 保持一致（名称分段、括号剥离、组合拆分）。
公司后缀（Inc/Co/Ltd/Corp/GmbH/AG/SA/株式会社等）参与匹配前剥除。
--apply 才写回。未匹配/歧义输出报告并非零退出。"""
import json, os, re, sys, unicodedata, collections

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get('SITE_DATA_DIR') or os.path.normpath(os.path.join(BASE, '..', '02 交付', '半导体装备与材料产业图谱', 'data'))
APPLY = '--apply' in sys.argv

CORP_SUFFIX = re.compile(r'\b(INC|CO|LTD|CORP|CORPORATION|GMBH|AG|SA|S\.A|LLC|LLP|PLC|HOLDINGS|HLDGS|KK|K\.K)\b\.?|(股份有限公司|有限责任公司|有限公司|股份公司|株式会社|有限会社)$', re.I)

def norm(s):
    s = unicodedata.normalize('NFKC', str(s or '')).upper()
    s = CORP_SUFFIX.sub(' ', s)
    return re.sub(r'[^\w\u4e00-\u9fff&/-]', '', s, flags=re.UNICODE)

def top_split(text, seps):
    out, depth, begin = [], 0, 0
    for i, c in enumerate(text):
        if c in '(（': depth += 1
        elif c in ')）': depth -= 1
        elif not depth and c in seps:
            out.append(text[begin:i].strip()); begin = i + 1
    out.append(text[begin:].strip())
    return [x for x in out if x]

def pieces(text):
    """与 domain.js pieces() 同规则：分号分句、冒号说明、顿号/中点并列。"""
    description = len(top_split(text, ':：')) > 1
    out = []
    for i, clause in enumerate(top_split(text, ';；')):
        parts = top_split(clause, ':：')
        if i and description and len(parts) == 1:
            continue
        out.extend(top_split(parts[0], '、·'))
    return out

def split_cn_en(p):
    """剥离括号后拆中/英文段，返回可能的名字 token 列表。"""
    s = re.sub(r'[（(][^（）()]*[）)]', ' ', p)
    s = re.sub(r'\s+', ' ', s).strip()
    if not s:
        return []
    tokens = [s]
    m = re.match(r'^(.*?[\u4e00-\u9fff][^\s]*)\s+([^\s\u4e00-\u9fff].*)$', s)   # 中文 英文
    if m:
        tokens += [m.group(1), m.group(2)]
    m = re.match(r'^([^\s\u4e00-\u9fff][^\u4e00-\u9fff]*?)\s+([\u4e00-\u9fff].*)$', s)  # 英文 中文
    if m:
        tokens += [m.group(1), m.group(2)]
    m = re.match(r'^([^\u4e00-\u9fff]+?)([\u4e00-\u9fff].*)$', s)   # 英文紧接中文
    if m:
        tokens += [m.group(1), m.group(2)]
    m = re.match(r'^([\u4e00-\u9fff].*?)([^\u4e00-\u9fff]+)$', s)  # 中文紧接英文
    if m:
        tokens += [m.group(1), m.group(2)]
    return tokens

def main():
    companies = json.load(open(os.path.join(SITE, 'companies.json'), encoding='utf-8'))['companies']
    # 人工裁决补丁：drop_match_tokens 从匹配索引剔除（如 Shinkawa 归属 Yamaha Robotics 后，旧主体不再以该名匹配）
    patches_path = os.path.join(BASE, 'verify_out', 'manual_patches.json')
    patches = json.load(open(patches_path, encoding='utf-8')) if os.path.exists(patches_path) else {}
    drop_tokens = patches.get('drop_match_tokens', {})
    alias_owner = collections.defaultdict(set)
    for c in companies:
        tokens = {c.get('name_cn'), c.get('name_en'), c.get('short_name'), *(c.get('aliases') or [])}
        tokens -= set(drop_tokens.get(c['company_id']) or [])
        for t in tokens:
            if t:
                alias_owner[norm(t)].add(c['company_id'])
    ambiguous_aliases = {k: v for k, v in alias_owner.items() if len(v) > 1}
    index = {k: next(iter(v)) for k, v in alias_owner.items() if len(v) == 1}
    by_id = {c['company_id']: c for c in companies}

    unmatched, ambiguous, stats = [], [], collections.Counter()

    def match_one(text, where):
        for tok in split_cn_en(text):
            key = norm(tok)
            if not key:
                continue
            if key in ambiguous_aliases:
                ambiguous.append(f'{where}: "{text}" 别名歧义 → {sorted(ambiguous_aliases[key])}')
                return None
            if key in index:
                return index[key]
        return None

    def display_name(c):
        short = c.get('short_name') or c.get('name_cn') or c.get('name_en') or c['company_id']
        # 拉丁后缀取不超过16字符的英文名或别名（如 TEL/AMEC），法定全称不进入显示名
        cands = [c.get('name_en') or ''] + [a for a in (c.get('aliases') or [])]
        for latin in cands:
            if latin and not re.search(r'[\u4e00-\u9fff]', latin) and len(latin) <= 16 and norm(latin) not in norm(short):
                return f'{short} {latin}'.strip()
        return short

    def resolve_string(s, where):
        """二级字符串 → 若干 {name, company_id?} 对象。"""
        out = []
        for piece in pieces(s):
            for part in top_split(piece, '/'):
                stats['sub_piece'] += 1
                cid = match_one(part, where)
                if cid:
                    out.append({'name': display_name(by_id[cid]), 'company_id': cid})
                    stats['matched'] += 1
                else:
                    out.append({'name': re.sub(r'\s+', ' ', re.sub(r'[（(][^（）()]*[）)]', ' ', part)).strip()})
                    unmatched.append(f'{where}: "{part}"')
        return out

    def migrate_file(fn):
        path = os.path.join(SITE, fn)
        data = json.load(open(path, encoding='utf-8'))
        for t in data['tracks']:
            nodes = [(t, '')] + [(s, s.get('name', '')) for s in (t.get('subs') or [])]
            for obj, sub_name in nodes:
                for role in ('global', 'china'):
                    fld = role + '_leaders'
                    leaders = obj.get(fld) or []
                    new_leaders = []
                    for leader in leaders:
                        where = f"{fn[:-5]}/{t['id']}{('/' + sub_name) if sub_name else ''}/{fld}"
                        if isinstance(leader, str):
                            new_leaders.extend(resolve_string(leader, where))
                            continue
                        stats['l1'] += 1
                        if leader.get('company_id'):
                            stats['matched'] += 1
                            new_leaders.append(leader); continue
                        name = leader.get('name', '')
                        parts = top_split(name, '/')
                        if len(parts) > 1:
                            # 一级对象斜杠组合：拆为多对象，关系字段随各实体复制并在 tag 注明
                            for part in parts:
                                stats['l1_split'] += 1
                                cid = match_one(part, where)
                                if cid:
                                    nl = dict(leader)
                                    nl['name'] = display_name(by_id[cid])
                                    nl['company_id'] = cid
                                    nl['tag'] = (nl.get('tag') or '') + '（原组合条目拆分）'
                                    new_leaders.append(nl)
                                    stats['matched'] += 1
                                else:
                                    nl = dict(leader); nl['name'] = part
                                    new_leaders.append(nl)
                                    unmatched.append(f'{where}: "{part}"（组合拆分后）')
                            continue
                        cid = match_one(name, where)
                        if cid:
                            leader['company_id'] = cid
                            leader['name'] = display_name(by_id[cid])
                            stats['matched'] += 1
                        else:
                            unmatched.append(f'{where}: "{name}"')
                        new_leaders.append(leader)
                    if leaders:
                        obj[fld] = new_leaders
        if APPLY:
            json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        return data

    for fn in ['equipment.json', 'materials.json']:
        migrate_file(fn)

    print(f"一级对象: {stats['l1']}（含组合拆出 {stats['l1_split']}）；二级片段: {stats['sub_piece']}；已匹配: {stats['matched']}")
    print(f'未匹配 {len(unmatched)} 条:')
    for u in unmatched: print('  [未匹配]', u)
    print(f'歧义 {len(ambiguous)} 条:')
    for a in ambiguous: print('  [歧义]', a)
    if not APPLY:
        print('\n（预演模式，未写回；确认后加 --apply）')
    sys.exit(1 if (unmatched or ambiguous) else 0)

if __name__ == '__main__':
    main()
