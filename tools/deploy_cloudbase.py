"""在已授权的既有环境部署本项目；不创建环境、不升级套餐、不修改其他路由。"""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time
from .cloudbase_mcp import call
from .package_deploy import build, ROOT, LOCAL

parser = argparse.ArgumentParser()
parser.add_argument("--env", required=True, help="先通过MCP核实的完整环境ID")
parser.add_argument("--site", action="store_true")
parser.add_argument("--functions", action="store_true", help="只更新既有三个函数的代码，保留环境变量和签名密钥")
args = parser.parse_args()
info = call("queryEnv", {"action": "info", "envId": args.env})["EnvInfo"]
if info["EnvId"] != args.env or not info.get("staticDomainRouteEnabled"):
    raise RuntimeError("目标环境或静态路由未就绪")
status = call("auth", {"action": "status"})
if status.get("current_env_id") != args.env:
    raise RuntimeError("MCP当前绑定环境与目标不一致，请先明确绑定")
routes = call("queryGateway", {"action": "listRoutes"})["data"]["routes"]
gateway = next(r["Domain"] for r in routes if r["DomainType"] == "HTTPSERVICE" and r["IsDefault"] and r["Domain"] != "*")
domain = info["StaticStorages"][0]["StaticDomain"]
settings = {"env_id": args.env, "region": info["Region"], "static_domain": domain, "gateway_domain": gateway,
            "api_base": "https://" + gateway + "/semi-industry-api", "site_url": "https://" + domain + "/semi-industry/index.html"}
LOCAL.mkdir(exist_ok=True)
(LOCAL / "environment.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
package = build(settings)
with tempfile.TemporaryDirectory(prefix="semi-deploy-") as directory:
    staging = Path(directory)
    if args.site:
        shutil.copytree(package["site"], staging / "site")
        call("manageHosting", {"action": "upload", "localPath": str(staging / "site"), "cloudPath": "semi-industry/"})
        print("Site uploaded:", settings["site_url"])
    if args.functions:
        shutil.copytree(package["function_root"], staging / "functions")
        for name in ("syncQuotes", "generateReport", "semiApi"):
            call("manageFunctions", {"action": "updateFunctionCode", "functionName": name, "functionRootPath": str(staging / "functions")})
            print("Function code updated:", name)
            for attempt in range(30):
                detail = call("queryFunctions", {"action": "getFunctionDetail", "functionName": name})["data"]["functionDetail"]
                if detail.get("Status") == "Active":
                    break
                if detail.get("Status") not in ("Updating", "Creating"):
                    raise RuntimeError("函数状态异常：" + str(detail.get("Status")))
                time.sleep(3)
            else:
                raise RuntimeError("函数更新尚未就绪，请查看CloudBase部署状态")
print("部署后仍需运行HTTP/MIME/浏览器/PDF验收；上传成功不代表验收通过。")
