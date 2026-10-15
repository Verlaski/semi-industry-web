"""从本机已安装的MCP调用CloudBase。凭证仅由MCP登录态管理。"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import queue
import threading
import time


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
    # 直接使用官方MCP的标准stdio协议，避免共享mcporter守护进程故障阻断发布。
    config = json.loads(Path(runtime()[3]).read_text(encoding="utf-8"))["mcpServers"]["cloudbase"]
    command = [config["command"], *config.get("args", [])]
    env = {**os.environ, **config.get("env", {})}
    payload = stdio_call(command, env, tool, arguments)
    if payload.get("success") is False:
        raise RuntimeError("CloudBase操作失败；请检查工具状态，原始响应未输出")
    return payload


def stdio_call(command, env, tool, arguments, timeout=250):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, encoding="utf-8", env=env)
    messages = queue.Queue()

    def read():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except json.JSONDecodeError:
                pass  # 官方进程可能含非协议启动提示；绝不回显原始输出。
        messages.put(None)

    threading.Thread(target=read, daemon=True).start()

    def send(message):
        process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def request(identifier, method, params):
        send({"jsonrpc": "2.0", "id": identifier, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("CloudBase MCP请求超时")
            try:
                message = messages.get(timeout=remaining)
            except queue.Empty:
                raise RuntimeError("CloudBase MCP请求超时") from None
            if message is None:
                raise RuntimeError("CloudBase MCP进程提前退出")
            if message.get("id") == identifier:
                if "error" in message:
                    raise RuntimeError("CloudBase MCP协议请求失败，原始响应未输出")
                return message["result"]

    try:
        request(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "semi-industry-release", "version": "1.1"}})
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        result = request(2, "tools/call", {"name": tool, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError("CloudBase工具执行失败，原始响应未输出")
        if isinstance(result.get("structuredContent"), dict):
            return result["structuredContent"]
        texts = [item["text"] for item in result.get("content", []) if item.get("type") == "text"]
        if len(texts) != 1:
            raise RuntimeError("CloudBase工具响应格式异常")
        return json.loads(texts[0])
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdin.close()
        process.stdout.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tool")
    parser.add_argument("--arguments", help="UTF-8 JSON参数文件路径")
    args = parser.parse_args()
    parameters = json.loads(Path(args.arguments).read_text(encoding="utf-8-sig")) if args.arguments else {}
    result = call(args.tool, parameters)
    # 只显示结果概要，完整响应可能包括函数环境变量或短时签名地址。
    print(json.dumps({"success": result.get("success", result.get("ok", True)), "message": result.get("message", "操作完成")}, ensure_ascii=False))
