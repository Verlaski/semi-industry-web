"""Build a double-clickable offline site using an explicit public-file allowlist.

No upload or cloud operation is performed. Review artifacts live outside the ZIP.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '02 交付' / '半导体装备与材料产业图谱'
ONLINE_URL = 'https://teyvat-1-d8g0sba0a7e30225d-1463262475.tcloudbaseapp.com/semi-industry/index.html#/overview'
FILENAME = '半导体装备与材料产业链龙头图谱_上海业务部_离线版本.zip'
ASSETS = (
    'assets/css/style.css',
    'assets/js/domain.js', 'assets/js/product.js', 'assets/js/app.js',
    'assets/fonts/NotoSansSC-Regular.woff2', 'assets/fonts/NotoSansSC-Bold.woff2',
    'assets/fonts/NotoSansKR-Hangul-Regular.woff2', 'assets/fonts/NotoSansKR-Hangul-Bold.woff2',
    'assets/fonts/OFL.txt',
    'assets/icons/github-mark.svg',
)
COMPANY_FIELDS = ('company_id', 'short_name', 'name_cn', 'name_en', 'aliases',
                  'country_region', 'listing_status', 'ipo_status', 'ipo_detail')
LISTING_FIELDS = ('listing_id', 'market', 'exchange', 'ticker', 'primary')


def public_bundle(site=SITE):
    bundle = {name: json.loads((site / 'data' / (name + '.json')).read_text(encoding='utf-8'))
              for name in ('meta', 'equipment', 'materials', 'sources', 'companies')}
    bundle['companies'] = {'companies': [
        {**{key: company[key] for key in COMPANY_FIELDS if key in company},
         'listings': [{key: listing[key] for key in LISTING_FIELDS if key in listing}
                      for listing in company.get('listings', [])]}
        for company in bundle['companies']['companies']]}
    return bundle


def make_files(site=SITE):
    bundle = public_bundle(site)
    encoded = json.dumps(bundle, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    html = (site / 'index.html').read_text(encoding='utf-8')
    html = html.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n<meta http-equiv="Content-Security-Policy" content="connect-src \'none\'; object-src \'none\'; frame-src \'none\'">')
    html = re.sub(r'<a\b[^>]*\bid="offline-save"[^>]*>.*?</a>',
                  '<a id="offline-save" class="nav-offline" href="' + ONLINE_URL + '" target="_blank" rel="noopener" title="访问在线版本"><img src="assets/icons/github-mark.svg" width="18" height="18" alt="">点击访问在线url</a>',
                  html, flags=re.S)
    html = html.replace('<script src="assets/js/config.js">',
                        '<script id="offline-data" type="application/json">' + encoded + '</script>\n<script src="assets/js/config.js">')
    files = {name: (site / name).read_bytes() for name in ASSETS}
    files['index.html'] = html.encode('utf-8')
    config = {'offline': True, 'version': bundle['meta']['version'], 'updated': bundle['meta']['updated']}
    files['assets/js/config.js'] = ('window.SEMI_CONFIG=' + json.dumps(config) + ';\n').encode('utf-8')
    return files, bundle


def build(destination, site=SITE):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    files, bundle = make_files(site)
    version = str(bundle['meta']['version'])
    filename = FILENAME
    archive = destination / filename
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, content in sorted(files.items()):
            item = zipfile.ZipInfo('semi-industry-offline/' + name, (2026, 10, 15, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            package.writestr(item, content, compresslevel=9)
    manifest = {
        'filename': filename, 'bytes': archive.stat().st_size,
        'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'version': version, 'updated': bundle['meta']['updated'],
        'companies': len(bundle['companies']['companies']),
        'tracks': sum(len(bundle[key]['tracks']) for key in ('equipment', 'materials')),
        'sources': len(bundle['sources']['sources']),
        'files': [{'path': 'semi-industry-offline/' + name, 'bytes': len(content)} for name, content in sorted(files.items())],
    }
    (destination / 'contents.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    text = f"# 离线包预览\n\n文件：{filename}\n\n大小：{manifest['bytes'] / 1048576:.2f} MB（{manifest['bytes']:,} 字节）\n\n解压后打开 semi-industry-offline/index.html，即可离线浏览，无需安装运行环境。\n\n"
    text += f"保留：7 个页面、{manifest['companies']} 家公司、{manifest['tracks']} 个赛道、{manifest['sources']} 条来源、详情卡、抽卡、CSV 导出、全部本地字体。五份必要数据库内嵌在 index.html，不重复保存 JSON。\n\n"
    text += "不含：行情快照及缓存、云函数、SDK/依赖、凭证、项目文档、研究草稿、测试文件、Git 目录。离线版不显示行情和云端 PDF 下载入口，不自动连接在线服务；原始来源的外部链接需要联网后手动打开。\n\n字体 OFL.txt 是字体分发必须保留的许可文件。\n\n## 包内文件\n\n| 文件 | 字节 |\n| --- | ---: |\n"
    text += ''.join(f"| {entry['path']} | {entry['bytes']:,} |\n" for entry in manifest['files'])
    text += f"\nSHA-256：`{manifest['sha256']}`\n\n当前状态：仅本地生成，等待用户预览确认，未上传 COS。\n"
    (destination / '离线包内容清单.md').write_text(text, encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'output' / 'offline-review')
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
