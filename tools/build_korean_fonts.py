"""为正式公司名补充同属OFL Noto Sans的韩文字形，不替换全站中文字体。"""
from pathlib import Path
import urllib.request
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]


def build():
    source = ROOT / '.local/font-source/NotoSansKR-VF.ttf'
    source.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        urllib.request.urlretrieve('https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansKR-VF.ttf', source)
    for label, weight in [('Regular', 400), ('Bold', 700)]:
        target = ROOT / f'reporting/fonts/NotoSansKR-Hangul-{label}.ttf'
        font = instantiateVariableFont(TTFont(source), {'wght': weight}, inplace=True)
        options = subset.Options()
        options.name_IDs = ['*']
        selected = subset.Subsetter(options=options)
        selected.populate(unicodes=[*range(32, 127), *range(0x1100, 0x1200), *range(0x3130, 0x3190), *range(0xAC00, 0xD7B0)])
        selected.subset(font)
        font.save(target)
        font.close()
        print(target.name, target.stat().st_size, flush=True)


if __name__ == '__main__':
    build()
