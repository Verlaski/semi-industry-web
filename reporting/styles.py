"""继承cn-pdf-report-style的A4、藏蓝、斑马纹与中文排版参数。"""
import os
import re
from pathlib import Path
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

NAVY = HexColor("#17375E")
GRAY = HexColor("#666666")


class FontResolver:
    @staticmethod
    def register():
        configured = os.environ.get("REPORT_FONT_PATH")
        bundled = Path(__file__).parent / "fonts" / "NotoSansSC-Regular.ttf"
        windows = Path("C:/Windows/Fonts/msyh.ttc")
        normal = Path(configured) if configured else windows if os.name == "nt" and windows.exists() and os.environ.get("REPORT_FONT_MODE") != "bundled" else bundled
        bold = Path("C:/Windows/Fonts/msyhbd.ttc") if normal == windows else normal.parent / "NotoSansSC-Bold.ttf"
        if not normal.is_file() or not bold.is_file():
            raise RuntimeError("缺少可用中文字体，请检查FontResolver配置")
        pdfmetrics.registerFont(TTFont("ResearchCN", str(normal), subfontIndex=0))
        pdfmetrics.registerFont(TTFont("ResearchCN-Bold", str(bold), subfontIndex=0))
        pdfmetrics.registerFontFamily("ResearchCN", normal="ResearchCN", bold="ResearchCN-Bold", italic="ResearchCN", boldItalic="ResearchCN-Bold")
        for weight, name in [('Regular', 'ResearchKR'), ('Bold', 'ResearchKR-Bold')]:
            fallback = bundled.parent / f'NotoSansKR-Hangul-{weight}.ttf'
            if not fallback.is_file():
                raise RuntimeError('缺少Noto韩文字形，请运行python -m tools.build_korean_fonts')
            pdfmetrics.registerFont(TTFont(name, str(fallback)))
        pdfmetrics.registerFontFamily('ResearchKR', normal='ResearchKR', bold='ResearchKR-Bold', italic='ResearchKR', boldItalic='ResearchKR-Bold')
        return normal.name


def font_fallback(markup):
    """仅为韩文文本加入同字体家族字形；保留已转义文本和链接标记。"""
    return ''.join(part if part.startswith('<') else re.sub(r'[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]+',
                   lambda match: '<font name="ResearchKR">'+match.group()+'</font>', part)
                   for part in re.split(r'(<[^>]*>)', markup))


def styles():
    base = dict(fontName="ResearchCN", textColor=HexColor("#333333"), wordWrap="CJK", splitLongWords=True)
    def make(name, **kw):
        return ParagraphStyle(name, **{**base, **kw})
    return {
        "title": make("title", fontName="ResearchCN-Bold", fontSize=23, leading=33, textColor=NAVY, alignment=TA_CENTER),
        "subtitle": make("subtitle", fontSize=13.5, leading=22, textColor=HexColor("#444444"), alignment=TA_CENTER),
        "meta": make("meta", fontSize=10, leading=20, textColor=GRAY, alignment=TA_CENTER),
        "h1": make("h1", fontName="ResearchCN-Bold", fontSize=14.5, leading=20, textColor=NAVY, spaceBefore=14, spaceAfter=8, keepWithNext=True),
        "body": make("body", fontSize=10, leading=16.5, alignment=TA_JUSTIFY, spaceAfter=6, rightIndent=12),
        "note": make("note", fontSize=8.5, leading=13, textColor=GRAY, spaceAfter=8, rightIndent=12),
        "cell": make("cell", fontSize=9, leading=13, rightIndent=5),
        "head": make("head", fontName="ResearchCN-Bold", fontSize=9, leading=13, textColor=white),
        "ref": make("ref", fontSize=8.5, leading=13, textColor=GRAY, leftIndent=16, firstLineIndent=-16, rightIndent=12, spaceAfter=7),
    }
