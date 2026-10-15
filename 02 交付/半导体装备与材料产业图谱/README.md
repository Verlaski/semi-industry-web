# 半导体装备与材料产业图谱 · 网站入口

用途：说明交付网站的入口及维护文档位置。读者：使用者与接手人员。更新时间：2026-10-15。产品版本：V1.1；研究数据版本见data/meta.json。

[在线访问](https://teyvat-1-d8g0sba0a7e30225d-1463262475.tcloudbaseapp.com/semi-industry/index.html)。首次访问可能显示腾讯云测试域名提示，确认后进入。

网站包含产业链总图、装备、材料、龙头公司库、竞争格局、机会抽卡与来源页。公司及赛道详情在侧栏打开。支持结构化CSV、后端PDF下载，以及三只指定证券的小时行情试运行。

前端继续使用HTML/CSS/原生JavaScript，无React/Vue或外部前端CDN。浏览器从data/读取meta、equipment、materials、sources四份研究JSON。正式companies.json接入前，公司库仅使用赛道名单兼容模型，未确认的上市状态保持待补充。

本机双击“启动本地预览.bat”，或在本目录运行`python -m http.server 8000`，再访问`http://localhost:8000`。直接打开file://地址受浏览器fetch限制。

| 维护事项 | 统一文档 |
| --- | --- |
| 项目入口与目录 | [项目README](../../README.md) |
| 当前产品能力和待办 | [产品说明](../../docs/01_PRODUCT.md) |
| JSON、行情、报告、CSV字段 | [数据模型](../../docs/02_DATA_MODEL.md) |
| 前后端与CloudBase资源关系 | [系统结构](../../docs/03_ARCHITECTURE.md) |
| 发布、行情同步、PDF QA、导出与抽卡验收 | [操作手册](../../docs/04_OPERATIONS.md) |
| 方案选择的原因 | [关键决策](../../docs/05_DECISIONS.md) |
| 本轮变化 | [变更记录](../../CHANGELOG.md) |

产业分类、国产化阶段和来源体系沿用原始研究数据。本轮不重新核验公司主体或市场份额，研究工作区及原始用户资料不属于静态发布目录。
