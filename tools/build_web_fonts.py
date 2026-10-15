"""Build OFL web font subsets from committed Noto fonts and current public UI/data.

Run after adding research names or UI text. Requires fonttools[woff] and brotli.
The PDF fonts remain unchanged; this only creates browser assets.
"""
from pathlib import Path
import shutil
from fontTools import subset

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '02 交付/半导体装备与材料产业图谱'


def build():
    text = ''.join(chr(i) for i in range(32, 127))
    for path in sorted(SITE.rglob('*')):
        if path.suffix in {'.html', '.js', '.css', '.json'}:
            text += path.read_text(encoding='utf-8')
    target = SITE / 'assets/fonts'
    target.mkdir(parents=True, exist_ok=True)
    for weight in ('Regular', 'Bold'):
        options = subset.Options()
        options.flavor = 'woff2'
        # Retain family/license metadata and shaping needed by the selected glyphs.
        options.name_IDs = ['*']
        font = subset.load_font(str(ROOT / f'reporting/fonts/NotoSansSC-{weight}.ttf'), options)
        sub = subset.Subsetter(options=options)
        sub.populate(text=text)
        sub.subset(font)
        output = target / f'NotoSansSC-{weight}.woff2'
        subset.save_font(font, str(output), options)
        print(output.name, output.stat().st_size)
    shutil.copy2(ROOT / 'reporting/fonts/OFL.txt', target / 'OFL.txt')


if __name__ == '__main__':
    build()
