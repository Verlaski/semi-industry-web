"""准备可部署的Linux依赖和开放中文字体，不复制Windows商业字体。"""
from pathlib import Path
import subprocess
import sys
import urllib.request
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / ".local" / "font-source"
FONTS = ROOT / "reporting" / "fonts"
TEMP.mkdir(parents=True, exist_ok=True)
FONTS.mkdir(parents=True, exist_ok=True)
destination = FONTS / "NotoSansSC-Regular.ttf"
source = TEMP / "NotoSansSC-VF.ttf"
if not source.exists():
    urllib.request.urlretrieve("https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf", source)
for name, weight in (("NotoSansSC-Regular.ttf", 400), ("NotoSansSC-Bold.ttf", 700)):
    target = FONTS / name
    if not target.exists():
        font = instantiateVariableFont(TTFont(source), {"wght": weight}, inplace=True)
        font.save(target)
        font.close()
license_path = FONTS / "OFL.txt"
if not license_path.exists():
    urllib.request.urlretrieve("https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE", license_path)
if any(not (FONTS / f"NotoSansKR-Hangul-{weight}.ttf").exists() for weight in ("Regular", "Bold")):
    subprocess.run([sys.executable, str(ROOT / "tools/build_korean_fonts.py")], check=True)
runtime = ROOT / ".local" / "python-linux"
if not (runtime / "reportlab").exists():
    subprocess.run([sys.executable, "-m", "pip", "install", "--target", str(runtime), "--platform", "manylinux2014_x86_64",
                "--python-version", "39", "--implementation", "cp", "--abi", "cp39", "--only-binary=:all:",
                "-r", str(ROOT / "reporting/requirements.txt"), "--index-url", "https://pypi.org/simple", "--disable-pip-version-check"], check=True)
print("Font and Linux dependencies prepared:", destination.stat().st_size)
