# 半导体装备与材料产业图谱

本项目面向投行、IPO及资本运作研究，通过产业链、赛道、龙头名单和公开来源帮助使用者了解行业。

用途：项目总入口。读者：负责人及接手Agent。更新时间：2026-10-15。产品版本：V1.1；研究数据版本仍以原始meta.json为准。

- [在线网站](https://teyvat-1-d8g0sba0a7e30225d-1463262475.tcloudbaseapp.com/semi-industry/index.html)
- 环境：`teyvat-1-d8g0sba0a7e30225d`，`ap-shanghai`；复用既有CloudBase个人版。
- 产品包含产业链总图、装备图谱、材料图谱、龙头公司库、竞争格局、AI推荐跟踪龙头和来源页。
- 正式公司主数据库（companies.json）已接入：公司实体经主体与上市信息核验，赛道龙头以 company_id 引用；A股/港股/美股龙头行情按小时更新。

| 想知道什么 | 文档 |
| --- | --- |
| 当前有哪些能力、哪些尚待完成 | [产品说明](docs/01_PRODUCT.md) |
| 数据和字段分别代表什么 | [数据模型](docs/02_DATA_MODEL.md) |
| 网站、行情与PDF如何连接 | [系统结构](docs/03_ARCHITECTURE.md) |
| 怎样预览、发布、触发行情和生成报告 | [操作手册](docs/04_OPERATIONS.md) |
| 为什么采用这些方案 | [关键决策](docs/05_DECISIONS.md) |
| 本轮改了哪些内容 | [变更记录](CHANGELOG.md) |
| KimiCode从哪里接手本次界面修订 | [交接文档](docs/KIMICODE_HANDOFF.md) |
| 公司主数据接入后的发布要点 | [发布交接](docs/CODEX_RELEASE_HANDOFF.md) |

网站文件在`02 交付/半导体装备与材料产业图谱/`；四份研究JSON保持原始内容。`backend/`与`cloudfunctions/`实现服务，`reporting/`实现报告，`tools/`用于打包与发布。`01 用户提供资料/`不入库、不发布。

| 网站数据文件 | 内容 |
| --- | --- |
| equipment.json | 装备赛道及龙头关系 |
| materials.json | 材料赛道及龙头关系 |
| sources.json | 研究来源账本（含 SRC-LS- 上市核验段） |
| meta.json | 研究日期、行业概览及版本 |
| companies.json | 统一公司与上市身份主表 |

本机预览：在仓库根目录执行 `python -m http.server 8000 --directory "02 交付/半导体装备与材料产业图谱"`，访问 `http://localhost:8000`。测试执行 `npm test`；PDF、部署及在线验收步骤见操作手册。

本轮开发分支为`codex/v1.1-online-product`，不合并main。上一轮公司池预处理仍在独立的`codex/v1.1-company-prep`分支。

当前界面采用荧光黄主色与蓝青辅色；总图提供双链结构示意及留页详情，公司表内显示已配置三证券行情。给Kimi的最终交接快照在commit/push后由`python -m tools.export_handoff`生成，包含完整SHA及远端核对状态；维护内容见上方交接文档。
