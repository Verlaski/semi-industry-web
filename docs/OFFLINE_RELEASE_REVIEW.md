# 离线保存：待用户确认的本地版本

分支：`codex/offline-download`，基于 main `f6371bc592a5db3ed221a2fd5b04b1d57c248a59`。

## 当前状态

仅本地制作，未上传 COS，未发布网页，未修改主分支。用户要求先查看压缩包，再上传。

生成：`python -m tools.build_offline`。

交付文件：`output/offline-review/semi-industry-offline-v1.1.1-20261015.zip`。

SHA-256：`20e1726b778e041975472b01e87fc5b206e88d4414ad28070b5ea73856f5ff4d`，677,299 字节。

包内共 11 个文件，数据内嵌于 index.html，保留 245 家公司、38 个赛道、426 条公司赛道关系、801 条来源。包含页面代码、本地字体及字体 OFL 许可；不含项目文档、原始工作区、云函数、行情快照、SDK、凭证。

离线启动读取内嵌数据，跳过 fetch 和行情定时器。移除行情栏及云端 PDF 按钮，保留 CSV 和全部产业交互。CSP connect-src none 进一步禁止后台连接。来源的外部链接仍可手动打开。

GitHub 图标来自 https://brand.github.com/GitHub_Logos.zip 中 SVG/GitHub_Invertocat_Black.svg，仅用于在线下载入口，未纳入离线包。

## 验证

- Python 10 项、Node 16 项通过，JS 语法及 diff 检查通过。
- 数据投影保留全部前端消费字段；去掉行情供应商映射等前端无用字段后，公司 ViewModel 与在线版一致；公司/装备/材料/来源 CSV 输出一致。
- 从 ZIP 解压出的页面经本地 HTTP 预览验证：7 个页面均渲染、245 家公司搜索、公司→产业→返回上级、十连抽 10 张卡、CSV 实际下载成功。
- 无行情栏、无行情容器、无 PDF 按钮；控制台无错误，服务器只收到页面/代码/字体请求，无 JSON/API 请求。
- 内置浏览器只允许 HTTP/HTTPS，无法直接验收 file://。代码已消除 file:// 下的数据 fetch 依赖，解压双击 index.html 的最后体验交由用户预览核对，不将 HTTP 测试冒充 file:// 测试。

## 用户确认后才能做

1. 核验当前 COS 桶、公共读状态和域名；上传上述 SHA 的同一个包，使用带内容摘要的不可变对象路径，避免覆盖已发布版本。
2. 对象 Content-Type application/zip，Content-Disposition attachment，指定离线 ZIP 文件名。仅开放这个包的读取，不调整全桶策略。
3. 使用未登录、无签名查询参数的公共 HTTPS 链接下载，验证实际压缩包与本地一致。
4. 写入 `config/offline-release.json`，记录 url、sha256、filename、bytes、数据版本及上传时间。`tools/package_deploy.py` 会将 url 注入公开配置 offlineDownload；不接受凭证、签名参数或非 HTTPS 链接。
5. 导航链接才会启用；COS 跨域下载应依靠对象 attachment 响应头，不能单靠 HTML download 属性。
6. 本地复核在线页面保留行情、离线包下载正确后，再合并主分支、提交/push 并发布网页。无需部署或变更行情云函数。

压缩包内容清单和导航截图在 output/offline-review 下，位于 ZIP 外部。
