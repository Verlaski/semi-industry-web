"""通用PDF Engine；不直接读取研究JSON。"""
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Spacer, PageBreak, Paragraph, KeepTogether
import re
from .components import paragraph, table
from .styles import FontResolver, styles, NAVY, GRAY


def generate(model, destination):
    font = FontResolver.register()
    st = styles()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    story = [Spacer(1, 4 * cm), paragraph(model.title, st["title"]), Spacer(1, .5 * cm),
             paragraph("产业链 · 龙头企业 · 竞争格局", st["subtitle"]), Spacer(1, 2.4 * cm),
             paragraph("研究数据版本：" + model.data_version, st["meta"]),
             paragraph("生成时间：" + model.generated_at, st["meta"]),
             paragraph("数据来自已收录公开资料，保留原始统计口径", st["meta"]), PageBreak(), paragraph("先看这里 · 要点摘要", st["h1"])]
    for i, item in enumerate(model.summary, 1):
        text = escape(item).replace("两条并行投入链", '<b><font backColor="#FFF2CC">两条并行投入链</font></b>')
        text = re.sub(r"\d+个(?:一级)?赛道", lambda m: '<b><font color="#C00000">' + m.group() + '</font></b>', text)
        story.append(Paragraph('<b><font color="#17375E">' + str(i) + ". </font></b>" + text, st["body"]))
    if model.quotes:
        story.append(paragraph("行情快照（各市场币种不可直接相加）", st["h1"]))
        for q in model.quotes:
            price = q.get("price")
            if isinstance(price, (float, int)) and price > 0:
                story.append(paragraph(f"{q.get('name', '')} {q.get('symbol', '')}：{price} {q.get('currency', '')}；行情时间 {q.get('quote_time', '')}；抓取时间 {q.get('fetched_at', '')}；来源 {q.get('provider', '')}；状态 {q.get('status', '')}", st["note"]))
    for section in model.sections:
        if section.new_page:
            story.append(PageBreak())
        story.append(paragraph(section.title, st["h1"]))
        for item in section.paragraphs:
            if item:
                story.append(paragraph(item, st["body"]))
        source_note = "资料来源：" + "、".join(section.source_ids) + "。详细书目与访问链接见文末。" if section.source_ids else None
        nonempty_tables = [item for item in section.tables if item.rows]
        for index, item in enumerate(nonempty_tables):
            if item.rows:
                story.extend([table(item, st, source_note if index == len(nonempty_tables)-1 else None), Spacer(1, .18 * cm)])
        if source_note and not nonempty_tables:
            story.append(paragraph(source_note, st["note"]))
    story.extend([PageBreak(), paragraph("资料来源与证据等级", st["h1"]),
                  paragraph("以下等级沿用原始研究账本，本轮未重新核验或调整证据等级。公司自述与二手转引以原备注为准。", st["note"])])
    reference_nodes = []
    for source in model.sources:
        text = f"[{source['source_id']}] {source.get('org', '')}，《{source.get('title', '')}》；发布 {source.get('publish_date', '')}；数据年份 {source.get('data_year', '')}；证据 {source.get('level', '')}级。"
        if source.get("caliber"):
            text += "口径：" + source["caliber"] + "。"
        if source.get("remark"):
            text += "备注：" + source["remark"]
        url = source.get("url", "")
        if url.startswith(("https://", "http://")):
            reference_nodes.append(Paragraph(escape(text) + '<br/><link href=' + quoteattr(url) + ' color="#17375E">' + escape(url) + "</link>", st["ref"]))
        else:
            reference_nodes.append(paragraph(text, st["ref"]))
    story.extend(reference_nodes[:-4])
    story.append(KeepTogether(reference_nodes[-4:] + [Spacer(1, .6 * cm), paragraph("免责声明", st["h1"]), paragraph(model.disclaimer, st["note"])]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(GRAY)
        canvas.setFont("ResearchCN", 8)
        canvas.drawString(2.4 * cm, 1.1 * cm, model.title + " · 研究参考")
        canvas.drawRightString(A4[0] - 2.4 * cm, 1.1 * cm, f"第 {doc.page} 页")
        canvas.setStrokeColor(HexColor("#DFE4EA"))
        canvas.line(2.4 * cm, A4[1] - 1.5 * cm, A4[0] - 2.4 * cm, A4[1] - 1.5 * cm)
        canvas.restoreState()

    doc = BaseDocTemplate(str(destination), pagesize=A4, topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                            leftMargin=2.4 * cm, rightMargin=2.4 * cm, title=model.title, author="产业研究")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="research", frames=[frame], onPage=footer))
    doc.build(story)
    return {"path": str(destination), "font": font, "data_version": model.data_version, "generated_at": model.generated_at}
