from xml.sax.saxutils import escape
import re
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle
from .styles import NAVY, font_fallback


def paragraph(text, style):
    content = escape(str(text)).replace("\n", "<br/>")
    # 中文字体常不含上标负号/数字；使用真正的上标排版，保留科学计数含义。
    content = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+", lambda m: "<super>" + m.group().translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")) + "</super>", content)
    return Paragraph(font_fallback(content), style)


def table(model, styles, source_note=None):
    content = [model.headers] + model.rows
    rows = [[paragraph(cell, styles["head"] if i == 0 else styles["cell"]) for cell in row] for i, row in enumerate(content)]
    if source_note:
        rows.append([paragraph(source_note, styles["note"])] + [""] * (len(model.headers) - 1))
    result = Table(rows, colWidths=[w * cm for w in model.widths], repeatRows=1, hAlign="LEFT")
    rules = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("LINEABOVE", (0, 0), (-1, 0), 1.2, NAVY), ("LINEBELOW", (0, 0), (-1, 0), .6, NAVY),
             ("LINEBELOW", (0, -1), (-1, -1), 1.2, NAVY)]
    for i in range(2, len(rows), 2):
        rules.append(("BACKGROUND", (0, i), (-1, i), HexColor("#F2F5F9")))
    if source_note:
        last = len(rows) - 1
        rules.extend([("SPAN", (0, last), (-1, last)), ("BACKGROUND", (0, last), (-1, last), HexColor("#FFFFFF")),
                      ("NOSPLIT", (0, last - 1), (-1, last)), ("TOPPADDING", (0, last), (-1, last), 8)])
    result.setStyle(TableStyle(rules))
    return result
