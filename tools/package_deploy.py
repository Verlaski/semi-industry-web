"""构建白名单站点/函数包，部署目录始终在.local内。"""
from pathlib import Path
import json
import hashlib
import shutil
from reporting.data_provider import ReportDataProvider

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "02 交付" / "半导体装备与材料产业图谱"
LOCAL = ROOT / ".local"


def reset(directory):
    directory = directory.resolve()
    if not directory.is_relative_to(LOCAL.resolve()) or directory == LOCAL.resolve():
        raise ValueError("打包目录越界")
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def build(environment):
    static = LOCAL / "site"
    reset(static)
    shutil.copy2(SITE / "index.html", static / "index.html")
    shutil.copytree(SITE / "assets", static / "assets")
    shutil.copytree(SITE / "data", static / "data")
    # 公共静态目录只含交付网站；绝不复制工作区、内部资料或研究草稿。
    allowed = {"meta.json", "equipment.json", "materials.json", "sources.json", "companies.json"}
    if any(p.name not in allowed for p in (static / "data").iterdir()):
        raise ValueError("站点数据目录含未批准的文件")
    revision = {"data_version": ReportDataProvider(SITE / "data").snapshot()["data_version"]}
    config = {"version": "1.1.0", "apiBase": environment["api_base"], "dataVersion": revision["data_version"]}
    text = "window.SEMI_CONFIG=" + json.dumps(config, ensure_ascii=False) + ";\n"
    (static / "assets/js/config.js").write_text(text, encoding="utf-8")
    # 此文件为公开配置，不包含环境凭证。
    (SITE / "assets/js/config.js").write_text(text, encoding="utf-8")
    # 发布文件名携带内容摘要，让已经打开过网站的浏览器也读取本次版本。
    html = (static / "index.html").read_text(encoding="utf-8")
    for asset in [static / "assets/css/style.css", *(static / "assets/js").glob("*.js")]:
        version = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        renamed = asset.with_name(asset.stem + "." + version + asset.suffix)
        shutil.copy2(asset, renamed)
        html = html.replace(asset.relative_to(static).as_posix(), renamed.relative_to(static).as_posix())
    (static / "index.html").write_text(html, encoding="utf-8")
    (static / "assets/发布校验.txt").write_text("半导体装备与材料产业图谱 V1.1 中文路径校验\n", encoding="utf-8")
    engine_hash = hashlib.sha256()
    for source in sorted((ROOT / "reporting").rglob("*")):
        if source.is_file() and (source.suffix == ".py" or source.suffix == ".ttf"):
            engine_hash.update(source.relative_to(ROOT / "reporting").as_posix().encode() + source.read_bytes())
    revision["renderer_version"] = engine_hash.hexdigest()[:12]
    functions = LOCAL / "functions"
    reset(functions)
    for name in ("semiApi", "syncQuotes", "generateReport"):
        target = functions / name
        shutil.copytree(ROOT / "cloudfunctions" / name, target)
        if name == "generateReport":
            shutil.copytree(ROOT / "reporting", target / "reporting", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(SITE / "data", target / "data")
            runtime = LOCAL / "python-linux"
            if runtime.exists():
                shutil.copytree(runtime, target, dirs_exist_ok=True)
        else:
            shutil.copytree(ROOT / "backend/market", target / "market")
            dependencies = {"name": "semi-" + name.lower(), "version": "1.1.0", "dependencies": json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["dependencies"]}
            (target / "package.json").write_text(json.dumps(dependencies), encoding="utf-8")
            # Event函数可云端安装，发布包也带已锁定的本地依赖以减少部署漂移。
            if (ROOT / "node_modules").exists():
                shutil.copytree(ROOT / "node_modules", target / "node_modules")
            if name == "semiApi":
                shutil.copytree(SITE / "data", target / "data")
                (target / "data-revision.json").write_text(json.dumps(revision), encoding="utf-8")
    return {"site": str(static), "function_root": str(functions), **revision}


if __name__ == "__main__":
    settings = json.loads((LOCAL / "environment.json").read_text(encoding="utf-8"))
    print(json.dumps(build(settings), ensure_ascii=False, indent=2))
