# Kimi Code → Codex 发布交接（公司主数据 + 行情扩容）

接收回执：本交接至 `daf6625` 的成果已与独立 UI 分支合入 main，完成部署与线上联调。当前验收、港股适配修正及后续边界见 [RELEASE_2026-10-15.md](RELEASE_2026-10-15.md)。下文保留 Kimi 交付时的原始记录；实际同步实现使用并发请求，并非逐只串行。

用途：Kimi 完成正式公司主数据库与行情扩容后，Codex 据此执行部署与线上验收。读者：Codex、项目负责人。更新时间：2026-10-15。对应版本：V1.1 数据正式化。

## 一、本轮变更摘要

| 项 | 内容 |
| --- | --- |
| 新增 | `站点/data/companies.json`：正式公司主表（245 家实体，上市 171 / 非上市 74） |
| 迁移 | equipment.json / materials.json 一级与二级 leader 全部改为 `{name, company_id, share, products, tag, source_id}` 结构；426 条引用全部 attach，0 未匹配、0 歧义 |
| 新增来源 | sources.json 增加 SRC-LS- 段（上市核验来源 644 条，含交易所/官网 IR/财经数据站分级） |
| 行情扩容 | `backend/market/symbols.generated.js` 由 `tools/build_quote_registry.py` 从主表 listings 生成（96 只证券，A股/港股/美股），每只带 `listing_id` 外键 |
| 移除 | domain.js 的 PREVIEW_QUOTES 临时显示桥（兼容模式不再关联行情） |
| 修复 | TencentProvider 的 SZ/BJ 总股本字段下标（原仅 .SH 取 73，深市/北交所会错取美股位） |
| 放宽 | semiApi `/api/quotes` 三证券限制 → 注册表内任意证券（缺省返回全部） |
| 前端 | product.js Drawer 行情白名单改为按代码后缀（SH/SZ/BJ/HK/US）；公司表页脚说明同步更新；公司库显示名改用 short_name 优先 |

## 二、发布步骤（与既有流程一致）

```text
python -m tools.deploy_cloudbase --env teyvat-1-d8g0sba0a7e30225d --site --functions
```

1. **semiApi 与 generateReport 必须同一构建发布**（data_version 已因 companies.json 改变，PDF 缓存键将自动失效重建，属预期）。
2. syncQuotes 注册表扩充至 96 只：首个整点同步周期耗时将显著增加（逐只请求腾讯接口），请观察首个周期日志确认无超时；如需分批，service.js 的 synchronize 可加并发批处理。
3. 部署白名单已含 companies.json（package_deploy.py 第 29 行），无需改。
4. quotes_latest 缓存键为 symbol，未变；三只试运行证券的注册表条目与原文档完全一致，旧缓存可直接沿用。

## 三、验收要点

- 公司库页：记录数 = 245；A股/港股/美股记录应显示行情（每小时同步），其余市场显示 —
- 抽卡：候选池按 company_id 去重，无组合主体
- CSV：公司/上市信息/赛道关系三张正式表可下载
- PDF：四类报告正常（leader 保留了已核验显示 name，Builder 无需改）
- `python -m tools.verify_online` 四类报告链路验证

## 四、已知未决项（数据侧，不阻塞发布）

- 87 家实体的 unresolved 字段记录了待办（多为中文名缺失、次要主体确认），见 companies.json
- 日股/欧股/韩股/台股 ticker 已在主表但不在行情注册表（供应商首批范围外），后续如需覆盖需在 Provider 层验证对应市场前缀
- 东财（EastMoney）备源对北交所代码的支持未实测通过；A股 SH/SZ 备源格式正常
- 北交所证券在东财备源失败时会回退腾讯主源（实测腾讯支持 bj 前缀）

## 五、第二轮追加：A股IPO在审状态与上市库双向核对（commit `38274da`）

Kimi 后续用用户提供的两份台账素材做了第二轮数据工作，Codex 部署时一并发布以下内容：

### 数据变化

| 项 | 内容 |
| --- | --- |
| 新增字段 | companies.json 每条新增 `ipo_status`（`A股IPO在审` 或空）与 `ipo_detail`（板块+交易所+审核状态） |
| 新分类 | 6 家实体标记 **A股IPO在审**：东方晶源、华卓精科、神州半导体（已问询·科创板）、珠海越亚（中止·创业板）、猎奇智能（注册同意待挂牌·创业板）、中科科化（中止·财报更新·科创板）。`listing_status` 保持"非上市"，**不破坏现有值域**（设计决策 DEC-025） |
| 来源 | 新增 SRC-LS-900（WIND 全球上市公司清单 28056 家）、SRC-LS-901（投行之声 A股IPO 项目明细 3618 项）；sources.json 现 801 条 |
| 核对结论 | WIND 清单核对 75 只 A股代码 **0 错误**；非上市中国公司反向排查无漏判已上市公司；4 家命中 WIND "A26xxx" 申报代码系 IPO 在审（非挂牌，未误判为上市） |

### 前端变化（Kimi 已做小范围改动，未动布局）

- `product.js`：`badge()` 对 `ipo_status==='A股IPO在审'` 的非上市公司显示橙色 "IPO在审" 徽章 + 板块/审核状态小字；图例 `legend()` 增加"IPO在审"档；公司详情增加 `ipo-banner` 提示条
- `domain.js`：VM 透传 `ipo_status/ipo_detail`；公司 CSV（`companies.csv`）表头与行增加两列
- `style.css`：新增 `.market-badge.ipo`（橙系）、`.ipo-banner`、`.ipo-detail` 样式

### 建议 Codex 做的交互增强（可选，非阻塞）

公司库"上市状态"筛选下拉目前仅"已上市/未上市"两档，建议增加 **"IPO在审"第三档**（`filters.status==='A股IPO在审'` 时按 `ipo_status` 过滤）。该下拉选项在 product.js `filterControls()`，属产品交互增强，由 Codex 统一调整更合适。

### 维护约定（给后续数据维护者）

- `ipo_status` 取数：投行之声 A股IPO 项目明细（用户同事定期导出），审核状态含 已受理/已问询/上市委通过/提交注册/中止/中止（财报更新）/注册同意
- 状态流转：注册同意→挂牌上市后，`listing_status` 转"上市"、补正式 ticker（届时自动进入行情注册表）；`ipo_status` 清空
- 注册同意未挂牌前不算上市（猎奇智能即此状态）

## 六、回退

```text
git revert <本轮commit>  → 重新执行同一构建发布
```

回退后 companies.json 404，前端自动回退兼容模式（行为与本轮之前一致）；注册表与 semiApi 限额随代码回退恢复原状。两轮数据（公司主表 + IPO在审）在同一批 companies.json 中，回退按 commit 粒度进行。

## 七、研究流水线留档（03 研究工作区/，不发布）

- `verify_batches/` 候选分批、`verify_out/` 各批核验结果与 `manual_patches.json` 人工裁决补丁
- `build_companies.py`（合并+校验+listing_id 归一）、`migrate_relations.py`（关系迁移，与 domain.js pieces/parseName 同规则）、`verify_cn_batch.py`（东财/腾讯接口核验）、`crosscheck_tickers.py`（行情接口名称反查，160/160 一致）
- 复现顺序：build_companies.py → build_quote_registry.py → migrate_relations.py --apply
