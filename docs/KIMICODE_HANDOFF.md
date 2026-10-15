# V1.1 Codex → Kimi Code 工程交接

用途：Kimi Code无需重新研究前端、CloudBase、行情、PDF或抽卡工程，即可开始正式公司数据库和研究数据完善。读者：Kimi Code、项目负责人。更新时间：2026-10-15。产品版本：V1.1（荧光黄主色与结构图修订）。

本文件维护交接内容。发布后执行 `python -m tools.export_handoff`，生成包含最终完整SHA、远端push核对及生成时间的交接快照 `output/handoff/KimiCode_V1.1_交接.md`；请把该快照直接交给Kimi。本文件及以下核心文档是维护入口，快照只作本次交付留档。

## 一、当前版本状态

<!-- release-status:start -->
| 项目 | 当前状态 |
| --- | --- |
| 产品版本 | V1.1；前端修订不改变研究版本，也不改变API健康接口中保留的1.1.0工程版本号 |
| Git branch | `codex/v1.1-online-product`，未合并main |
| 最终commit SHA | 发布后的交接快照实时填入完整HEAD，并与GitHub分支核对 |
| GitHub是否已push | 交接导出工具必须核对远端SHA一致才会生成快照 |
| GitHub | https://github.com/Verlaski/semi-industry-web/tree/codex/v1.1-online-product |
| CloudBase在线URL | https://teyvat-1-d8g0sba0a7e30225d-1463262475.tcloudbaseapp.com/semi-industry/index.html |
| 数据更新时间 | 2026-10-15；研究meta.version仍为v1.0 |
<!-- release-status:end -->

本地仓库 `D:\AITool\AI临时文件\04-kimi\04 金融中台产业研究` 已存在，不要重新clone。网站在 `02 交付/半导体装备与材料产业图谱/`，下文称“站点”。上一轮基线提交为 `3696838598e6fdd495d76c59c766ac63b33c218c`。

已完成：七页面、双链结构图、总图左右对齐且留页打开详情、赛道与公司及来源侧栏、Badge、主图和长表固定表头、CSV、四类PDF、三证券小时行情、单抽/十连、条件筛选、金紫蓝卡面、随机准备文案与礼炮。Hero荧光黄#DFFF00配深字，正文/链接保留蓝青#087F98；导航突出🎲推荐跟踪。

临时状态：正式companies.json尚不存在。当前249条兼容记录、408条有效公司引用、233条可抽候选均是显示模型统计，不等于已核验法人数量。公司上市身份未知；行情仅3只试运行证券，3条临时显示关联不构成正式listing主数据。来源与研究份额未因工程改版而重新核验。

## 二、前端架构及稳定组件

### 页面route

| route | 页面 |
| --- | --- |
| `#/overview` | 总图、双链汇流结构图；点赛道只开侧栏、不换标签 |
| `#/equipment` | 装备分类、名单折叠、龙头总览表 |
| `#/materials` | 材料分类、名单折叠、龙头总览表 |
| `#/companies` | 公司检索、筛选、表内最新价/涨跌额/涨跌幅/总市值 |
| `#/landscape` | 竞争格局、国产化矩阵 |
| `#/discovery` | 🎲 AI推荐跟踪龙头 |
| `#/sources` | 五列来源列表、完整来源侧栏、版本记录 |

`#/equipment?track=eq-f-etch`等旧深链接保留。它会打开赛道侧栏，但不会给表格行留下持久高亮。原温控/运动系统黄底仅为旧定位高亮未清理，已移除，不是研究评级。

| 模块/组件 | 位置、职责及接手边界 |
| --- | --- |
| 配置 | assets/js/config.js：公开apiBase/dataVersion；由发布工具实际查询环境生成，无Secret |
| 图谱渲染 | assets/js/app.js：四JSON加载、来源索引、总图/结构图、赛道卡与表格、hash路由 |
| 纯数据层 | assets/js/domain.js：CompanyRepository、过滤、CSV、抽卡、卡面标签、行情显示桥/数值格式、随机等待文案 |
| 页面交互 | assets/js/product.js：Drawer、公司表、行情请求、PDF下载、抽卡状态、主图固定条、页脚说明 |
| Design Token | assets/css/style.css：--brand-primary/--lime=#DFFF00；--brand-secondary/--navy=#087F98；--ink=#173D45；--bg=#F3F8F8；--sans本地Noto Sans SC；--mono通用等宽字体 |
| Track Drawer | openTrack读取原赛道完整细节，侧栏内可点公司，支持返回赛道 |
| Company Drawer | openCompany显示公司身份、产业关系、份额/产品/来源；缺失字段保留待补充 |
| Source Drawer / Tooltip | 来源标题或角标打开右侧卡，展示完整口径/备注/原链接；title提供简短提示，无跑马灯、无额外Popover库 |
| Drawer公共机制 | openDrawer/closeDrawer负责背景inert、Esc、焦点约束和恢复；避免另造弹窗体系 |
| Badge | 只有正式上市状态和listing才显示资本市场/证券代码；未知不当作非上市 |
| Sticky Header | nav高度由ResizeObserver计算；主图标题与三栏在本部分边界内固定，移动端按当前列固定；长表是独立限高滚动区 |
| CSV Export | domain.csvTables/csvText，UTF-8 BOM、公式前缀保护、赛道与leader分表、二级拆行；正式公司库到位后自动启用三张主表导出 |
| PDF Download | product.report请求自有API→下载签名PDF；不调用浏览器打印来替代Engine |
| Discovery | 过滤后均匀随机，无放回；动画与研究数据分离，取消/切页会清理状态 |

上述视觉、Drawer、Badge、Sticky、CSV、PDF下载及抽卡交互已稳定，Kimi不需要重新设计或引入React/Vue。只改必要数据适配及字段展示。新增中文名称后运行 `python -m tools.build_web_fonts` 更新网页OFL字体子集。

## 三、CompanyRepository数据契约（P0必读）

```text
正式 companies.json 不存在（HTTP 404）
  ↓
Compatibility Adapter：读取一级/二级global_leaders和china_leaders
  ↓
拆分部分原始名单、保守名称归并、生成临时Company ViewModel
  ↓
公司页 / 抽卡候选池 / Track Drawer / Company Drawer / CSV适配
```

只有404才回退；503、解析错误或正式主库格式错误会明确报错，不悄悄用旧数据代替。兼容模型的runtime_key以legacy:开头，不得用作最终company_id。ticker_hints只是原文数字线索；listing_status/listings留空，不从代码或母公司推断上市身份。country_region来自原文，缺失时国内筛选可用china角色作显示分组，不能据此认定注册地。

### 正式公司主表（当前已经支持）

文件路径：`站点/data/companies.json`。接受公司数组，或 `{"companies":[...]}`；每个company_id必须非空且唯一。推荐同一主体在全库只保留一个ID，多地上市放listings[]。

| 字段 | 期望类型/要求 |
| --- | --- |
| company_id | string，稳定唯一，由研究主表线分配 |
| name_cn / name_en | string，至少一项，确认过的主体名称 |
| aliases | string[]，仅确认过的名称变体 |
| country_region | string，未知留空，不继承未经核验的fallback国别 |
| listing_status | 当前值域严格为上市/非上市；未知留空（未上市不是当前代码值域） |
| listings[] | object[]，上市身份列表，多地上市不复制公司 |
| listings[].listing_id | string，稳定上市身份ID，后续行情关联键 |
| market / exchange / ticker / primary | 如A股、SSE、688012.SH、true；ticker带市场后缀，primary boolean |

### 公司×赛道关系

| 字段 | 目标含义 | 当前实际消费方式 |
| --- | --- | --- |
| company_id | 正式主体外键 | 优先明确ID；旧名称只有唯一匹配时才连接 |
| track_id | 现有赛道ID | 来自track.id；沿用eq-u/eq-f/eq-b、ma-f/ma-p实际编号 |
| role | global/china及未来其他已定义角色 | 当前由global_leaders/china_leaders所在数组派生 |
| position | 排名/地位及适用范围 | 原对象字段会保留，但现有视图主要展示share/tag，需明确是否单独展示 |
| share | 份额，必须附报告期/产品范围 | 赛道关系属性，不放入公司固有属性 |
| products | 该公司在该赛道的产品 | 侧栏已显示，不是全公司通用产品结论 |
| source_ids | 多来源目标字段 | 当前前端主要读取单数source_id；需保留主来源或给srcRefs做小适配，不能仅改名 |
| sub_name / tag | 二级细分名、跟踪标签 | 当前兼容关系字段；抽卡等级会使用，不可在迁移中漏掉二级关系 |

**接入路径：** 先填companies.json，再在现有tracks/subs的global_leaders/china_leaders对象中写company_id与关系字段。前端会自动进入official模式，显示确认身份、筛选和公司/上市/关系CSV。正式模式下没被关系匹配的公司仍在公司库，但不进入抽卡候选池。

当前**不会自动读取独立track_company_relations.json**。如Kimi采用独立关系主表，应给CompanyRepository增加一层关系加载/attach适配，再同步静态打包白名单、CSV字段及报告Provider；其余UI组件复用。不要把一个新关系文件放进data/就误认为已接入。

名字相同不保证同一法人。现有forLeader仍兼容唯一名称；P0完成后以明确company_id关系为准，检查每条一级/二级引用是否成功attach，逐条处理未匹配和歧义，不依赖fallback替你决定主体。

## 四、不能继承为最终真值的数据

以下全部只能作迁移线索，不能当作正式已核验结论：临时拆分主体、legacy运行标识、ticker_hints、组合公司字符串、原文母子公司描述、company_pool_draft、前端fallback归并/地区推断、测试fixture/mock、三证券PREVIEW_QUOTES临时显示关联。

不要把研究草稿直接改名为companies.json上线。不要把上市母公司的代码直接赋给未核验子公司，也不要因为组合字符串出现在同一条名单就认定同一主体。证据等级必须回到来源核验，不因本次页面或PDF改版自动升级。

前期公司池材料在现有`codex/v1.1-company-prep`分支的`03 研究工作区/`：company_pool_draft.json、company_pool_report.md、company_pool_review.md、validate_company_pool.py。本轮只核对这些文件路径存在，没有将草稿合并到在线分支或重新背书其中结论。Kimi可先只读查看作为异常处理线索，不要整分支合并发布。

## 五、CloudBase现状

本轮只读核对环境、路由、定时器与托管配置，并继续复用已部署工程。文档不记录Secret、Token、临时签名或完整环境变量。

| 项目 | 当前配置 |
| --- | --- |
| envId / region | teyvat-1-d8g0sba0a7e30225d / ap-shanghai，既有个人版，环境NORMAL |
| 静态托管路径 | semi-industry/，入口index.html；只上传站点白名单，不上传工作区 |
| 网关域名 | teyvat-1-d8g0sba0a7e30225d-1463262475.ap-shanghai.app.tcloudbase.com |
| 网关route | /semi-industry-api → SCF semiApi，EnablePathTransmission=true，EnableAuth=false |
| syncQuotes | Nodejs18.15 Event函数，证券注册表中的3只证券同步与过期报告缓存清理，index.main |
| semiApi | Nodejs18.15 Event函数，行情只读API/报告请求/签名下载，index.main |
| generateReport | Python3.9 Event函数，ReportLab生成PDF；同时提供main_handler与main兼容入口 |
| collection | quotes_latest、report_cache、report_files；现有规则ADMINONLY，仅服务端访问 |
| Storage目录 | 本项目未建立报告Storage目录；既有桶公共读，不上传报告，也不改变其他项目ACL |
| PDF实际存储 | report_files集合base64分块，ID为cacheKey-index；不是Storage路径 |
| 定时任务 | syncQuotes / semiHourlyQuotes / timer；七段cron为0 5 * * * * *，每小时:05执行 |
| 自定义域名 | 本项目未绑定独立自定义业务域名，使用上述CloudBase默认域名；查询中的*通配记录不是本项目域名 |

API入口为网关域名后加`/semi-industry-api`。`GET /health`、`GET /api/quotes`、`POST /api/reports`、`GET /api/reports/file`均已实现。当前公开API只服务随站点公开的研究内容；若以后加入非公开资料，应先设计访问鉴权。

发布通过本机MCP登录态，使用 `python -m tools.deploy_cloudbase --env teyvat-1-d8g0sba0a7e30225d --site` 更新页面；数据/报告包联动时使用同一构建的 `--site --functions`。工具不建环境、不升级套餐、不覆盖其他站点，CSS/JS/woff2带内容摘要。完整操作和回退见[操作手册](04_OPERATIONS.md)。

## 六、行情工程与迁移

Provider接口在`backend/market/providers.js`，服务和时段在`backend/market/service.js`。已发布顺序记录为Tencent主源、EastMoney备用源，由QUOTE_PROVIDERS控制。前次云端实测东财连接失败后切腾讯；本次读三股API仍为Tencent。同步频率1小时，网页公司页也每小时重读缓存；不是实时终端。

| normalize / quotes_latest字段 | 含义与单位 |
| --- | --- |
| _id / symbol | 当前集合文档ID为symbol；688012.SH、00522.HK、AMAT.US |
| name / market / currency | 名称、市场、CNY/HKD/USD；不跨币种汇总 |
| price / previous_close / change / change_pct | 数值或null；change_pct是百分数，2.5代表2.5% |
| market_cap / float_market_cap / total_shares | 原币种基础金额及股数；前端市值除1e8展示为亿 |
| quote_time | 供应商行情本身UTC时间，不用抓取时间替代 |
| fetched_at | 最近成功获取该有效行情的UTC时间 |
| provider / status | 供应商；ok、stale、closed、unavailable |
| last_sync_failed / last_attempt_at | 双源失败标志/尝试时间，旧有效价格及原时间保留 |

fresh是概念，当前schema状态名是ok：预期交易时段内quote_time和fetched_at均不超过90分钟。周末及常规收盘状态为closed；没有有效价格/时间为unavailable；失败或交易时段超时为stale。未接完整节假日日历。美股按纽约时区处理夏令时；东财按f59精度，腾讯市值从亿元转基础金额。

公司表直接展示最新价、涨跌额、涨跌幅、总市值，红涨绿跌；顶部为三股缓存最近成功fetched_at（北京时间），每只证券原quote_time/status在单元格提示中。未知证券显示—。没有伪造全部249条记录的报价。

**Kimi迁移：** 正式listing确认后把临时symbol关联迁移为listing_id。symbol仍保留作Provider证券标识，新增listing_id外键并建立可核验映射；不要直接把symbol改名造成供应商失配。扩充现有SYMBOLS注册表、API三证券限制、前端固定请求及Drawer白名单，按批次读取；复用Provider和normalize，不重写行情系统。切换完成后移除domain.js里的PREVIEW_QUOTES，回填和切换缓存键时保留旧缓存可回退。未知身份或组合主体不得进入正式行情关联。

## 七、PDF Engine：复用，不重写

```text
ReportDataProvider → 规范快照 → Builder → ReportModel/SectionModel/TableModel
                                         ↓
                           Style + Components + Engine
                                         ↓
                         generateReport（Python Event）
                                         ↓
                    semiApi → report_files私有分块缓存
                                         ↓
                          30分钟签名下载链接 → PDF
```

| 组件 | 当前文件/作用 |
| --- | --- |
| ReportDataProvider | reporting/data_provider.py集中读取研究JSON；可读取可选companies.json，并计入内容版本 |
| ReportModel | reporting/models.py；类型、标题、数据版本、生成时间、摘要、章节、来源、免责声明与行情快照 |
| Builder | reporting/builders.py组织四类报告，不直接读文件 |
| Style | styles.py、fonts.py、components.py：A4研究报告样式、开放中文字体、表格分页、来源和页码 |
| Engine | engine.py输出真实PDF；不依赖网页截图或手工排版 |
| Cloud Function | cloudfunctions/generateReport/index.py消费受控参数，返回PDF base64给semiApi |
| Storage / Cache | 不使用公共Storage；report_cache元数据/生成锁，report_files每块≤500000字符，6小时到期，小时任务清理 |

支持overview总览、equipment装备、materials材料、landscape竞争格局四类；公司专题PDF仍未实现。数据版本、renderer_version、行情小时和筛选条件共同参与缓存键，链接HMAC签名30分钟有效。单个PDF限制3MB，超限需缩小范围。

本地生成：仓库根目录执行 `python -m reporting overview`（也可换equipment/materials/landscape），支持`--track-id`与`--data`；输出output/pdf。`python -m reporting.qa output/pdf/overview.pdf --output output/qa/overview`渲染逐页PNG、联系图和检查结果，正式交付仍需目检全部页。字体/依赖准备、云端同字体模式和修复流程见[操作手册](04_OPERATIONS.md)。

云端生成：网页“下载PDF”，或POST自有apiBase的`/api/reports`，请求`{"report_type":"equipment","filters":{}}`。只允许现有track_id和国产化stage。获取download_url后下载，不保存/提交带signature的URL。`python -m tools.verify_online`验证四类生成、缓存、下载与篡改拒绝；这会真实生成报告，不是纯静态检查。

**companies.json接入后自动增强与仍需做的小适配：** Provider会自动把主表加入快照、把其内容加入data_version，部署后缓存键自动变化。当前Builder的leader名称仍取name或company_id，**不会自动按主表解析名称/上市信息**；Kimi应给Provider/Builder增加薄层ID→公司名称/listing解析，保持ReportModel/Engine/Style不变。在完成此解析前，清理原始leader时先保留已核验显示name，避免PDF只出现ID。正式库存在不代表公司PDF或全量行情自动出现。

研究或companies更新必须将相同构建的semiApi数据版本与generateReport数据包一起发布，否则会触发Report revision mismatch。网页颜色改版不要求重做PDF研究排版。

## 八、AI推荐跟踪龙头

当前实现：单抽、十连；国内/海外、上市/未上市、赛道筛选；无放回均匀抽取；金五星核心龙头、紫四星重点跟踪、蓝三星产业观察；模板理由；约2.4秒准备进度；三阶段各10句、最多1000种等待组合；揭晓彩条、清单复制与受限下载兜底。减少动态效果时直接揭晓。等级角落注明不构成投资评级。

没有在线LLM评分，也没有个人偏好分析，准备进度只是揭晓动效。理由来自真实已有关系字段；卡面等级只是在产品定义的跟踪范围中分组，概率不加权。规则集中在domain.cardCategory，详见[数据模型](02_DATA_MODEL.md#卡面跟踪标签)。

当前Candidate Adapter仅是临时方案，排除combo和无关系记录；兼容名称去重不保证法人去重，不能作为完整正式Candidate Pool。上市未知不会被当作未上市，因此当前上市/未上市筛选可能空池。

Kimi用`companies.json + 已核验company-track relations`构造正式候选；每个company_id一次，多赛道放occurrences。保留筛选、抽取、卡面和动画框架，重做数据映射即可。不要把company_pool_draft直接上线，不把未知上市身份或未确认母子关系伪装为已核验推荐标签。

## 九、Kimi只需要做什么

| 优先级 | 任务 | 完成标准 |
| --- | --- | --- |
| P0 | 处理主体异常、确定最终company_id | 组合/别名/母子关系有明确处理记录，ID稳定唯一 |
| P0 | 建立companies.json、核验listing | 名称、地区、上市状态、交易所、ticker、listing_id与来源可回查，未知保留未知 |
| P0 | 建company-track关系、清理leader字符串 | 一级与二级引用全部映射，无静默丢失、歧义归并或用legacy当正式ID |
| P0 | 修正来源等级与主来源 | 回原始公开资料验证；多来源策略兼容现有source_id消费 |
| P0 | 接入CompanyRepository | official模式；公司/赛道/抽卡/CSV可用，抽卡按company_id去重，旧接口错误明确可见 |
| P0 | 最小PDF公司名解析、同版发布 | company_id引用在PDF显示已核验名；semiApi/generateReport版本一致，复用既有Engine |
| P1 | 完善公司研究信息与推荐标签 | 属性归公司，份额/产品/地位归关系；不由UI颜色反推研究结论 |
| P1 | 修正份额、排名与二级关系 | 绑定报告期、产品范围及来源，覆盖所有subs |
| P1 | listing_id行情关联与扩容 | 去除试运行显示桥、配置批量证券注册/限额；不重写Provider |

不需要重新做：页面视觉、结构图、Drawer、Badge、Sticky Header、CloudBase部署体系、行情Provider、PDF Engine、CSV Engine、抽卡交互框架。必要的字段桥接、注册表扩充和测试应在现有模块中小范围完成。

接入验收顺序：JSON/ID/来源校验→现有JS及Python测试→七页面、公司/赛道/来源侧栏、抽卡/CSV→四类PDF文字和逐页视觉→统一发布→HTTP/API/缓存验收。代码与对应文档同次commit，再push；不把研究草稿、凭证、临时签名、debug日志或用户资料加入公开站点。

## 十、Known Issues / Technical Debt

| 类别 | 已知事项 | 是否阻塞 | 由谁处理 | 建议阶段 |
| --- | --- | --- | --- | --- |
| Data | 249兼容记录未完成主体、组合、母子及ID核验 | 阻塞正式公司主表/正式候选池；不阻塞当前浏览 | Kimi研究线 | P0 |
| Data | 原份额、地位、证据等级及部分二级来源待核 | 阻塞将这些字段作为已复核研究结论 | Kimi研究线 | P0来源，P1完善 |
| Frontend | 独立关系JSON、source_ids复数、position独立展示尚未自动适配 | 若采用这些新契约则阻塞接入 | Kimi数据适配 | P0 |
| Frontend | 前轮IAB复制返回成功但工具读剪贴板为空 | 不阻塞页面；实际粘贴仍需手工复核，已有失败文本/下载兜底 | Kimi验收/负责人 | 交接验收 |
| CloudBase | 默认测试域名可能有平台访问提示，未绑独立域名 | 不阻塞当前默认URL | 负责人/运维 | 域名正式发布时 |
| CloudBase | 平台静态响应带attachment；浏览器已实测可渲染 | 不阻塞已验证浏览器；新浏览器若触发下载需诊断 | 运维 | 出现兼容性问题时 |
| CloudBase | 当前公开API仅面向公开研究，非公开资料需鉴权 | 阻塞上线非公开数据 | 负责人/工程 | 引入私密资料前 |
| Quote | 仅3证券、PREVIEW_QUOTES临时显示桥、symbol缓存键 | 阻塞全量公司行情；不阻塞当前三股试运行 | Kimi主数据+工程 | 主表后P1 |
| Quote | EastMoney云端连接受限、完整休市日历缺失 | 不阻塞腾讯主源；影响备源/节假日状态精度 | 运维/行情工程 | P1 |
| PDF | Builder尚未解析company_id到主表名称/listing | 阻塞删除leader.name后完整展示 | Kimi数据适配 | 与ID-only迁移同批P0 |
| PDF | 公司专题报告、私有Storage适配未做；现有3MB限制 | 不阻塞四类现有PDF | 工程后续 | 公司专题/规模确需时 |
| Discovery | 临时去重、未知上市筛选可能空池、跟踪等级为产品配置 | 阻塞正式候选池完整性；动画不受影响 | Kimi研究/数据适配 | P0/P1 |

当前验收见[界面验收记录](UI_REFINEMENT_ACCEPTANCE.md)，原行情/PDF完整验收见[在线验收](ONLINE_ACCEPTANCE.md)。既有未跟踪手册、PLAN_V1.1.md、文档维护规范和docs/debug.log属于本地材料，不在本次提交和静态发布中，保留原状。
