# 数据模型

用途：解释数据归属与接口字段。读者：维护人员、研究Agent与开发Agent。更新时间：2026-10-15。对应版本：V1.1。

研究JSON → 赛道及原始龙头引用 → CompanyRepository显示模型。正式companies.json到位后通过明确编号或唯一名称对应关系连接。行情以symbol暂存；PDF以ReportModel生成。公司属性、公司×赛道属性、动态行情分别维护。

## 数据文件与存储

| 数据 | 用途 | 维护边界 |
| --- | --- | --- |
| meta.json | 研究日期、规模、景气度、下游、趋势 | 本轮不改研究内容 |
| equipment.json / materials.json | 一级/二级赛道、龙头、份额、国产化、来源 | 保留现有taxonomy及关系属性；龙头经 company_id 引用公司主表 |
| sources.json | 资料来源、日期、口径及证据等级 | 含 SRC-LS- 上市核验来源段 |
| companies.json | 正式公司主表（公司固有属性 + 上市身份） | 公司主表研究线维护；不保存赛道关系属性 |
| quotes_latest | 最新有效行情 | ADMINONLY；symbol 作 _id 并关联 listing_id |
| report_cache | 报告状态与元数据 | ADMINONLY；缓存、生成锁与到期时间 |
| report_files | PDF的base64分块 | ADMINONLY；每块最多500000字符，随缓存6小时到期 |

## 研究字段与归属

| 字段 | 中文意思 / 类型 | 维护要求 |
| --- | --- | --- |
| id / track_id | 赛道编号，string | 研究维护；沿用现有eq-u、eq-f、eq-b及ma-f、ma-b前缀，不改既有编号 |
| name / group / chain_position | 名称、分组、产业链位置，string | 属于赛道；一级赛道必须完整 |
| subs | 二级细分，array | 每项含name、note及自己的龙头引用 |
| market_size | 市场规模，object | value、unit、year、scope、source_id一起维护，缺值不填0 |
| localization | 国产化判断，object | stage、scope、evidence、source_id一起维护 |
| company_id | 正式公司引用，string | 研究主表负责人分配；本轮不生成最终编号 |
| share / position | 份额或角色，string | 属于公司在某赛道中的关系；保留统计范围和报告期，现有数据多用share与global/china分组表达 |
| products / tag | 产品与说明，string | 属于公司×赛道关系，不搬到公司固有属性 |
| source_id | 来源编号，string | 必须对应sources.json现有账本；沿用SRC系列编号 |
| note | 赛道备注，string | 保留适用范围及不能直接比较的口径 |
| org / title / url | 来源机构、标题、链接，string | 由研究维护；仅允许HTTP(S)链接在页面打开 |
| publish_date / data_year / access_date | 发布日期、数据期、访问日期，string | 三者分别保留，不互相替代 |
| metric / caliber / region / level | 指标、统计口径、地域、A/B/C/D证据等级，string | 不因页面或报告改版提高证据等级 |

公司名称、地区与上市身份属于公司；规模和国产化属于赛道；份额、角色和产品属于两者的关系。例如同一公司在刻蚀和薄膜沉积中的份额可以不同。

正式companies.json为 `{"companies":[...]}` 对象。适配合同如下，company_id 由公司主表研究线分配：

| 字段 | 类型 | 必填 / 含义 | 维护者 |
| --- | --- | --- | --- |
| company_id | string | 是；公司唯一编号（编码规则见下） | 公司主表研究线 |
| name_cn / name_en | string | 至少一项；中英文名称 | 研究 |
| short_name | string | 否；通行显示简称 | 研究 |
| aliases | string[] | 否；确认过的名称变体（更名史/品牌/收购前名） | 研究 |
| country_region | string | 应填；未确认留空 | 研究 |
| listing_status | enum | 应填；上市或非上市，未知留空（查不到不等于非上市） | 研究 |
| listings | object[] | 已上市时应提供；多地上市不复制公司 | 研究 |
| listing_id | string | 正式上市身份编号 `{company_id}_{交易所}`；行情关联键 | 研究 |
| market / exchange / ticker | string | 上市市场词表、交易所、标准证券代码（带市场后缀） | 研究 |
| primary | boolean | 否；主要上市地，未提供时显示首条 | 研究 |
| provider_symbols | object | 否；A股/港股/美股填 tencent 格式（sh/sz/bj/hk/us 前缀），供行情注册表生成 | 研究 |
| listing_source_id | string | 否；上市信息核验来源（sources.json 中 SRC-LS- 编号） | 研究 |
| source_keys / entity_decision / confidence / unresolved | string / array | 研究侧溯源字段：候选池辅助键、主体裁决、置信度、未决事项；前端不消费 | 研究 |

company_id 编码规则：通行英文缩写大写（AMEC、NAURA、ASML、TEL、SHINETSU）；无通行英文名的中国公司用拼音缩写大写；同一主体全库唯一 ID，多地上市放 listings[]，冲突由主表维护者裁决。前端不据名称线索把子公司自动连接到上市母公司，也不强行归并不同公司。正式company_id引用优先；旧名单只在名称能唯一匹配时连接正式主表。

## CompanyRepository / 抽卡Candidate

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| runtime_key | string | 页面运行时标识；兼容模式用legacy前缀，绝非最终company_id |
| name / name_cn / name_en | string | 从原始数据清洗得到的显示名 |
| aliases / ticker_hints | string[] | 原文名称变体与代码线索，未作证券代码确认 |
| country_region | string | 原始country/括号地区汇总；缺失留空 |
| listing_status | string | 正式主表确认的上市/非上市；兼容模式留空 |
| listings | object[] | 正式上市记录，含listing_id/market/exchange/ticker/primary |
| occurrences | object[] | dataset/track_id/track_name/sub_name/role及原始份额、产品、来源 |
| combo | boolean | 是否为未拆分斜杠组合；抽卡排除 |
| verified_master | boolean | 是否来自正式公司主表，不表示本轮重新核验 |

一级与二级leader均进入兼容模型；相同中英文清洗名粗去重。公司库筛选为纯数据过滤，未知上市身份不进入已上市或未上市集合。单抽/十连在过滤后使用Fisher-Yates洗牌，无放回抽取runtime_key不同的记录。不同别名是否属于同一法人，最终以正式公司库为准。

## 行情schema

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| symbol / name / market / currency | string | 规范证券标识、测试证券名、市场、币种 |
| price / previous_close / change / change_pct | number或null | 最新价、前收、差值、百分比；无有效价格时不显示为0 |
| market_cap / float_market_cap / total_shares | number或null | 原币种市值、流通市值、股数；不跨币种汇总 |
| quote_time | ISO8601 UTC或null | 供应商行情本身的时间 |
| fetched_at | ISO8601 UTC或null | 本系统成功取得该有效行情的时间；双失败时保留旧值 |
| provider / status | string | EastMoney或Tencent；ok/closed/stale/unavailable |
| last_sync_failed / last_attempt_at | boolean / ISO8601 | 失败标志和最近尝试时间，不冒充行情时间 |

EastMoney按f59精度缩放价格；Tencent市值单位转换为基础货币单位。美股行情时间按纽约时区处理夏令时。交易时段任一有效时间超过90分钟显示stale；常规收盘时段允许closed；主备均失败保留最后有效价并标记stale。

证券注册表为 `backend/market/symbols.generated.js`，由 `tools/build_quote_registry.py` 从正式公司主表的 listings 生成（携带 listing_id 外键）；首批覆盖 A股（SH/SZ/BJ）、港股、美股（腾讯 gtimg 已实测五类前缀），日股/欧股/韩股/台股公司不入注册表、前端显示—。Tencent 解析对 SH/SZ/BJ 统一按 A股载荷取总股本字段。semiApi 的 /api/quotes 允许注册表内任意证券（缺省返回全部），不再限三只试运行证券。

公司表行情显示由quoteSymbol/quoteDisplay桥接：正式模式认已上市公司的 primary listing ticker；临时三证券显示桥（PREVIEW_QUOTES）已随正式主表接入移除。price/change/change_pct保留数值含义，市值原币种除1e8展示为亿；未知显示—。正涨跌为红、负为绿。symbol 保留作 Provider 证券标识（缓存键不变、可回退），listing_id 关联经注册表建立。

当前关系来自tracks/subs的global_leaders/china_leaders，不自动读取独立关系文件。position与source_ids多来源是目标契约，前端当前主要展示share/tag并读取source_id主来源；采用新契约时需同步小范围适配。详见[交接契约](KIMICODE_HANDOFF.md#三companyrepository数据契约p0必读)。

## ReportModel与缓存

ReportModel包括report_type、title、data_version、generated_at、summary、sections、sources、disclaimer、quotes。每个SectionModel包含标题、段落、TableModel、source_ids及分页标志；Builder只消费Provider快照，不直接读取文件。

data_version使用原meta版本加四份研究文件内容摘要；产品V1.1与研究数据v1.0区分。缓存键包含报告类型、data_version、renderer_version、行情小时和稳定排序的筛选条件。修改样式或字体会更换renderer_version，避免继续下载旧版PDF。

report_cache保存state、report_type、filename、data_version、generated_at、chunks、bytes、quote_hour、filters、expires_at。下载链接为HMAC签名，仅30分钟有效；不是Storage公共链接。报告缓存6小时后由小时同步任务清理。

## CSV schema

| 文件 | 一行代表什么 | 关键内容 |
| --- | --- | --- |
| equipment_tracks / materials_tracks | 一级赛道或一个二级细分 | 赛道、分组、细分、规模、国产化及来源 |
| equipment_leaders / materials_leaders | 一次有效企业引用 | 赛道、细分、角色、名称、原文、份额、产品、来源、代码线索 |
| sources | 一份来源 | 原始账本列，平铺导出 |
| companies（正式库） | 一家公司 | company_id、中英文名、地区、上市状态 |
| company_listings（正式库） | 一个上市身份 | company_id、listing_id、市场、交易所、代码、primary |
| track_company_relations（正式库） | 一条赛道引用 | 公司、赛道、细分、角色、份额、来源 |

CSV使用UTF-8 BOM、标准引号/换行转义；可能触发Excel公式的开头字符先加文本前缀。嵌套数组按关系拆行，不把整份JSON塞入单元格。

## 卡面跟踪标签

这是前端展示规则，不新增研究字段，不写回公司主表，不改变均匀随机抽取概率。只检查当前筛选范围内的公司×赛道关系，满足多个条件时按金、紫、蓝顺序显示。卡片赛道与跟踪理由使用触发该等级的关系，避免多赛道公司的卡面错配。

| 等级 | 使用已有字段的规则 | 视觉 |
| --- | --- | --- |
| 核心龙头 | 在光刻机、刻蚀设备、薄膜沉积设备、硅片、光刻胶、CMP材料六个产品设定的重点跟踪赛道中，属于一级全球/国内龙头（非二级引用） | 暖金、五星 |
| 重点跟踪 | 其他二级细分龙头，或原始tag含龙头/国产/替代/核心/第一；重要未上市企业须同时有已核验非上市状态及重点/重要/核心标签 | 深紫、四星 |
| 产业观察 | 其余候选记录 | 蓝灰、三星 |

重点赛道集合维护在domain.js的FOCUS_TRACKS中，是可调整的产品跟踪配置，不代表一份新增行业评级。缺少正式上市主数据时绝不从名称猜测“重要未上市企业”。页面角落明确显示：卡面等级表示产业图谱中的跟踪标签，不构成投资评级。
