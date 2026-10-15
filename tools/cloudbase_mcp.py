"""从本机已安装的MCP调用CloudBase。凭证仅由MCP登录态管理。"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import tempfile


def runtime():
    cache = Path.home() / "AppData/Local/npm-cache/_npx"
    candidates = sorted(cache.glob("*/node_modules/mcporter/dist/cli.js"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("请先安装mcporter：npm install -g mcporter，或使用已配置的CloudBase MCP")
    config = os.environ.get("CLOUDBASE_MCP_CONFIG")
    if not config:
        packages = list(cache.glob("*/node_modules/@cloudbase/cloudbase-mcp/package.json"))
        if not packages:
            raise RuntimeError("本机缺少CloudBase MCP，请先安装官方插件")
        packages.sort(key=lambda p: tuple(int(x) for x in json.loads(p.read_text(encoding="utf-8"))["version"].split(".")[:3]), reverse=True)
        directory = Path(tempfile.gettempdir()) / "semi-industry-mcp"
        directory.mkdir(exist_ok=True)
        config = str(directory / "mcporter.json")
        Path(config).write_text(json.dumps({"mcpServers": {"cloudbase": {"command": "node", "args": [str(packages[0].parent / "dist/cli.cjs")],
            "env": {"TCB_SITE": "domestic", "TCB_REGION": "ap-shanghai"}}}}), encoding="utf-8")
    return [shutil.which("node") or "node", str(candidates[0]), "--config", config]


def call(tool, arguments):
    result = subprocess.run(runtime() + ["call", "cloudbase." + tool, "--args", json.dumps(arguments, ensure_ascii=False), "--timeout", "240000", "--output", "json"],
                            capture_output=True, encoding="utf-8", timeout=250)
    if result.returncode:
        raise RuntimeError("CloudBase调用失败；请在MCP查看登录或参数错误，未输出可能含敏感信息的原始响应")
    payload = json.loads(result.stdout)
    if payload.get("success") is False:
        raise RuntimeError(payload.get("message", "CloudBase操作失败"))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tool")
    parser.add_argument("--arguments", help="UTF-8 JSON参数文件路径")
    args = parser.parse_args()
    parameters = json.loads(Path(args.arguments).read_text(encoding="utf-8-sig")) if args.arguments else {}
    result = call(args.tool, parameters)
    # 只显示结果概要，完整响应可能包括函数环境变量或短时签名地址。
    print(json.dumps({"success": result.get("success", result.get("ok", True)), "message": result.get("message", "操作完成")}, ensure_ascii=False))
