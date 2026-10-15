# 系统结构

用途：说明静态站、云函数、行情与报告如何连接。读者：开发与运维人员。更新时间：2026-10-15。对应版本：V1.1。

```text
四份静态研究JSON + 正式 companies.json
  ├─ 原生Web前端 → CompanyRepository → 公司/赛道侧栏、筛选、抽卡
  ├─ CSV Adapter → 关系拆表 → 浏览器下载
  └─ ReportDataProvider → ReportModel → Builder → ReportLab Engine
                                                    ↓
                                             generateReport（Python）
                                                    ↓
                                           私有NoSQL PDF缓存/分块
                                                    ↓
                                        semiApi → 30分钟签名链接 → 下载

EastMoney / Tencent
        ↓
MarketDataProvider → syncQuotes（每小时:05）→ quotes_latest
                                               ↓
                                       semiApi → 前端 / PDF
```

## 实际资源边界

前端界面继续使用原生HTML/CSS/JavaScript。app.js拥有图谱和来源列表，product.js拥有侧栏、折叠栏、抽卡准备/揭晓和页脚说明，domain.js拥有纯数据适配和卡面跟踪分类。浏览器使用本地Noto Sans SC网页子集及OFL许可证；tools/build_web_fonts.py从已保存的报告字体和当前公开文本重建，发布时字体也带内容摘要。没有增加前端框架、外部字体请求或在线AI调用。

| 层 | 本项目资源 | 说明 |
| --- | --- | --- |
| 环境 | teyvat-1-d8g0sba0a7e30225d / ap-shanghai | 复用现有个人版，NoSQL后端 |
| 静态托管 | 独立semi-industry/子目录 | 公共HTML/CSS/JS/JSON；不上传研究工作区和用户资料 |
| 网关 | 既有默认HTTPSERVICE域名的/semi-industry-api | 上游SCF事件函数，路径透传 |
| Node事件函数 | semiApi | 读行情缓存、请求报告、签名下载；不直接暴露数据库 |
| Node事件函数 | syncQuotes | 小时触发与手工管理端调用；执行后清理过期报告缓存 |
| Python事件函数 | generateReport | 本地打包Linux依赖和开放中文字体，读取函数包内研究JSON |
| 数据库 | quotes_latest / report_cache / report_files | 三者均ADMINONLY，仅服务端访问 |
| 原有Storage | 保持既有公共读设置 | 本项目报告不上传这个公共桶，不改变其他项目权限 |

三个函数均为Event函数，不使用HTTP函数的端口9000/scf_bootstrap，也不使用CloudRun。网关SCF入口与静态托管是不同域名资源，地址由实时查询生成；不凭手册拼接新域名。

## API合同

- `GET {apiBase}/health`：固定非敏感健康信息及版本。
- `GET {apiBase}/api/quotes`：默认全部 96 只注册证券；可用 symbols 传注册表内子集，未知证券返回 400。浏览器不访问供应商。
- `POST {apiBase}/api/reports`：请求体`{"report_type":"equipment","filters":{}}`；类型限overview/equipment/materials/landscape，筛选只允许已存在的track_id及固定国产化stage。
- `GET {apiBase}/api/reports/file?key=...&expires=...&signature=...`：验证签名/有效期后返回PDF附件，不提供永久公开文件地址。

报告结果包含filename、data_version、generated_at、cached、expires_at、download_url。API只返回面向使用者的错误文字；不回显请求上下文、环境变量、供应商原始响应或堆栈。

## 行情运行方式

syncQuotes 按 QUOTE_PROVIDERS 配置依次尝试供应商，对注册证券并发同步。当前云端腾讯优先；两者均失败时保留旧有效值和原始时间，记录本次尝试时间及 stale。quotes_latest 仍以 symbol 保存，注册表由正式 listings 生成并携带 listing_id，不再使用临时公司名称映射。港股供应商代码补为五位，正式 ticker 保持不变。

公司页将 API 注册证券缓存接入表格单元格，更新行情时不重绘表格，保留筛选、滚动与焦点；domain.quoteSymbol 只负责正式主上市地 listing，quoteDisplay 负责数值/币种和红涨绿跌。PREVIEW_QUOTES 已移除。没有向浏览器增加供应商直连。

freshness依据市场时区、常规交易时段与90分钟阈值。周末及收盘后允许closed；节假日日历尚未完整接入。行情每小时更新，页面也每小时读取一次缓存，无WebSocket。

## 报告运行方式

`reporting/data_provider.py`负责全部文件读取；`models.py`定义报告模型；`builders.py`按类型组织章节；`styles.py`负责字体和排版；`components.py`负责表格/段落；`engine.py`输出PDF；`qa.py`逐页渲染与检查。

Provider 已读取 companies.json 并更新内容摘要；当前 Builder 仍按 leader.name 或 company_id 直接显示，不会自动查主表名称。当前正式关系保留 name，因此报告正常；迁移为 ID-only 关系前需要增加名称解析薄层，复用现有模型、样式与 Engine。

报告样式沿用Verlaski/cn-pdf-report-style，A4、藏蓝#17375E、斑马纹表格、页码、摘要高亮和来源附录。FontResolver本地可用微软雅黑；云端使用随包发布的Noto Sans SC常规/粗体及OFL许可。科学计数上标使用排版标签，避免中文字体缺字。

缓存键包含研究数据内容版本、渲染器版本、行情小时和筛选条件。生成锁避免同一报告并发重复构建；文件按base64分块保存，单块不超过500000字符。签名密钥只放函数环境变量。后续如具备私有Storage，可以替换存储适配，继续保持API合同。
