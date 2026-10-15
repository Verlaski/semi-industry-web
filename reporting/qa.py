"""逐页渲染、页面文字边界检查及联系图；视觉检查不能由文字检查替代。"""
from pathlib import Path
import argparse
import json
try:
    import pymupdf as fitz
except ImportError:
    import fitz
from PIL import Image, ImageDraw


def inspect(pdf, output, dpi=110):
    pdf, output = Path(pdf), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf)
    problems, pages, thumbnails = [], [], []
    for number, page in enumerate(document, 1):
        image_path = output / f"page-{number:03}.png"
        page.get_pixmap(dpi=dpi).save(image_path)
        text = page.get_text()
        if not text.strip():
            problems.append(f"第{number}页为空白")
        if "\ufffd" in text or "\x00" in text:
            problems.append(f"第{number}页有替换字符")
        if f"第 {number} 页" not in text:
            problems.append(f"第{number}页缺页码")
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    x0, y0, x1, y1 = span["bbox"]
                    if x0 < 62 or x1 > page.rect.width - 62 or y0 < 32 or y1 > page.rect.height - 20:
                        problems.append(f"第{number}页文字超安全边界：{span['text'][:30]}")
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((450, 640))
        thumbnails.append((number, image.copy()))
        pages.append({"page": number, "characters": len(text), "image": str(image_path)})
    for index in range(0, len(thumbnails), 6):
        contact = Image.new("RGB", (1380, 1330), "#dde2e8")
        draw = ImageDraw.Draw(contact)
        for k, (number, image) in enumerate(thumbnails[index:index+6]):
            x, y = (k % 3) * 460, (k // 3) * 665
            draw.text((x+8, y+4), f"{pdf.stem} / {number}", fill="#17375e")
            contact.paste(image, (x+5, y+22))
        contact.save(output / f"contact-{index//6+1:02}.jpg", quality=92)
    result = {"pdf": str(pdf), "page_count": len(document), "problems": problems, "pages": pages}
    (output / "checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--output", default="output/qa")
    args = parser.parse_args()
    result = inspect(args.pdf, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "pages"}, ensure_ascii=False))
    raise SystemExit(bool(result["problems"]))
