# 操作手册

用途：给出预览、发布、检查和故障处理步骤。读者：维护人员及接手Agent。更新时间：2026-10-15。对应版本：V1.1。

## 本机运行与验证

Windows终端先设置UTF-8；下文命令在仓库根目录执行。

```powershell
$utf8 = New-Object System.Text.UTF8Encoding $false
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
npm ci
npm test
python -m http.server 8000 --directory "02 交付/半导体装备与材料产业图谱"
```

打开`http://127.0.0.1:8000`。产品为原生静态页面，无构建框架；API地址在assets/js/config.js，由发布工具从真实环境查询结果写入。直接双击HTML受到fetch限制。

## 发布网页与函数代码

先阅读用户提供的CloudBase实战手册；它是本项目资源分离和部署操作的优先依据。工具通过本机MCP登录态操作，不读写明文密钥。若使用自定义mcporter配置，可在本机设置CLOUDBASE_MCP_CONFIG指向仓库外文件。

```powershell
python -m tools.cloudbase_mcp auth
python -m tools.deploy_cloudbase --env teyvat-1-d8g0sba0a7e30225d --site --functions
```

发布工具实际查询环境与网关，检查当前MCP绑定，生成白名单发布包，使用纯ASCII临时路径上传。`--site`仅更新semi-industry/目录；`--functions`仅更新既有syncQuotes/generateReport/semiApi代码，保留密钥和环境变量。它不会创建环境、升级套餐或覆盖其他站点。

发布包的CSS/JS/网页字体文件名带内容摘要，研究请求携带数据版本，避免浏览器沿用旧交互代码。源目录仍使用便于维护的原文件名；不要手工编辑生成文件。仅修改前端时使用同一命令加`--site`，不加`--functions`。

首次准备PDF运行包先执行`python -m pip install -r reporting/requirements-dev.txt`，再执行`python tools/prepare_pdf_runtime.py`。脚本下载官方Noto CJK字体源、生成400/700两个静态字重、保存OFL许可证，并下载Python3.9 Linux依赖。代码及字体变动会更新renderer_version，防止下载旧缓存。

函数更新为异步过程。发布工具轮询Active状态；仍待更新或失败时必须检查，不可把“上传成功”当运行成功。Python函数同时提供main_handler/main入口，兼容管理工具实际使用的index.main；部署后核对实际Handler和CodeInfo。

初次创建函数、集合、路由及触发器需要单独使用CloudBase MCP。现有本项目资源已创建，平时无需重建。函数安全规则是环境共享配置：必须读取后合并本项目条目，保留其他函数及通配配置。syncQuotes/generateReport客户端invoke=false，semiApi公开入口invoke=true；三个集合ADMINONLY。

## 检查与手工触发行情

在仓库外或.local/保存UTF-8参数文件，例如`.local/invoke-sync.json`：

```json
{"action":"invokeFunction","functionName":"syncQuotes","params":{}}
```

运行`python -m tools.cloudbase_mcp manageFunctions --arguments .local/invoke-sync.json`。输出只显示概要，MCP里检查ok和三只证券的provider/status/quote_time/fetched_at。勿把完整日志、环境变量或临时凭证提交。

用浏览器打开公司库的“行情试运行”，或请求本项目`apiBase + /api/quotes`。正常价格必须大于0；人民币/港元/美元分别显示。每小时固定:05触发，CloudBase七段表达式为`0 5 * * * * *`。用queryFunctions/listFunctionTriggers确认存在semiHourlyQuotes。

QUOTE_PROVIDERS可设置`Tencent,EastMoney`或`EastMoney,Tencent`，更改时合并既有环境变量。当前环境优先腾讯；东方财富云端连接尚受限。本轮真实触发已验证东方财富失败后自动切到腾讯。完整节假日日历未接入，特殊休市状态需人工解释。

## 本地生成与检查PDF

```powershell
python -m reporting overview
python -m reporting equipment
python -m reporting materials
python -m reporting landscape
python -m reporting.qa output/pdf/equipment.pdf --output output/qa/equipment
```

ReportDataProvider读取交付目录当前研究数据，输出在output/pdf。QA逐页生成PNG、联系图与checks.json，检查页码、替换字符和文字边界；仍必须目检全部页面，尤其长表、来源和最后一页。修改模型/样式后重新生成，不人工编辑PDF。部署前可设置REPORT_FONT_MODE=bundled验证与云端相同的开放字体。

## 网页下载PDF

在总图、装备、材料或竞争格局页点击“下载PDF”。页面显示生成中；后端命中缓存则直接返回链接，否则调用Python生成，再缓存并返回30分钟签名链接。浏览器下载PDF附件。失败时查看函数状态、Handler、依赖及日志；不要将堆栈返回页面。

临时链接过期后重新点击生成即可。同版本/同小时/同筛选命中缓存；缓存6小时后清理。报告没有上传现有公共Storage桶。若未来报告包含非公开内容，必须先增加身份鉴权，再允许生成；目前服务只打包交付网站的公开研究数据。

## CSV与抽卡

装备/材料页分别点击“下载赛道 CSV”和“下载龙头 CSV”，各下载一张表；来源页导出sources.csv。独立按钮避免浏览器拦截连续多文件下载。Excel按UTF-8 BOM识别中文。公司CSV仅在正式公司库存在时导出，不把兼容模型宣称为正式主表。

抽卡页验证单抽一张、十连十个不同runtime_key、地区与赛道组合条件、人数不足提示、再次抽取及复制清单。正式库缺失时上市筛选可返回空结果，不能用未知身份冒充未上市。代码测试还覆盖正式主表样例的上市/未上市和资本市场适配。

## 日常研究数据更新

- 新增公司：由正式主表维护者在companies.json分配唯一company_id，补中英文名、地区、上市身份及来源，再在赛道中引用该编号。没有正式主表时继续按研究流程维护原名单，不把兼容runtime_key写回研究库。
- 新增赛道：在equipment.json或materials.json沿用现有分组、编号和字段，填写产业链位置、二级细分、龙头、规模和国产化来源；用JSON解析检查，再看总图、筛选、CSV和PDF是否同步出现。
- 修改份额：只改对应赛道的公司引用，保留范围/报告期并补source_id，不改公司固有属性。修改股票代码：正式库接入后只改该公司的listing，重新核对行情映射。
- 新增来源：在sources.json新增不重复编号，补机构、标题、链接、日期、指标、口径和证据等级；确认所有引用编号都能找到。
- 页面加载失败：先检查四份JSON是否能解析，正式companies.json格式是否正确，再检查静态路径和MIME。正式公司库返回503或错误格式时会明确报错，不悄悄退回旧名单。
- 公司或代码不显示：核对company_id、唯一名称匹配、listing_status及listings；未知上市身份显示待补充是预期行为。行情失败先看API健康、函数状态及Provider，而不是向网页添加供应商直连。

每次研究变更后重跑检查和PDF，再commit、push、部署并验收。研究结论由研究负责人复核，产品开发测试不能替代事实核验。

## 发布后验收

逐一检查index.html、CSS、全部JS、四份JSON及中文路径资源，核实HTTP状态与MIME；再在浏览器检查所有hash路由、赛道/公司侧栏、来源跳转、Esc/焦点恢复、手机宽度和减少动态效果。API检查健康、三股行情、无效参数、生成/缓存/下载以及签名篡改拒绝。

运行`python -m tools.verify_online`可重复HTTP/API检查，记录保存在忽略目录.local/online-checks.json，四类实际云端PDF保存在output/pdf/cloud-*.pdf。临时签名不写入记录。浏览器交互与PDF视觉检查仍需单独执行。

前次完整后端/PDF验收见[在线验收记录](ONLINE_ACCEPTANCE.md)，本次界面修订见[界面验收记录](UI_REFINEMENT_ACCEPTANCE.md)。研究数据版本不等于产品版本，来源结论尚未因本轮开发而重新核验。

## 字体与界面更新

网站使用随仓库保存的Noto Sans SC Regular/Bold网页子集及OFL许可证。新增页面文案或研究数据中的汉字后运行`python -m pip install "fonttools[woff]" brotli`，再运行`python -m tools.build_web_fonts`，将生成的两个woff2与代码/数据一起提交。新增正式公司库后也应重建字体，防止新名称依赖系统回退。子集仅覆盖当前公开页面/数据字符，PDF原字体不变。

界面验收依次检查：桌面与390px窄屏七个路由；总图行距与标签；主图全部/局部折叠、二级公司和详情侧栏；主图标题/三列表头吸顶及离开主图后的退出；表格内部滚动的表头固定；来源五列不换行及右侧完整资料；单抽/十连准备、10个唯一结果、三档卡面、礼炮、取消、空池和清单复制。减少动态效果时跳过准备与彩条。卡面规则只在数据模型维护，不新增研究结论。

## 回退

保留上一个正常代码提交与对应数据版本。先在独立分支检出正常版本并本地验证，再运行同一发布工具更新本项目目录和函数代码。不得删除既有其他站点、网关、集合或分支。签名密钥一般不需要更换；更换后旧链接会立即失效。
