# Interactive map and checkbox filters Implementation Plan

**Goal:** 在独立工作空间完成真实赛道结构图与抽卡多选筛选，仅本地验证。

**Architecture:** 从现有 equipment / materials / meta 数据构造结构图，同一模型提供抽卡赛道分组。保留 Track Drawer 与 CompanyRepository 契约，筛选接受标量或数组，组内 OR、组间 AND、空数组不限。

**Tech Stack:** 原生 HTML / CSS / JavaScript、Node test、本地 Python HTTP 服务。

## 工作边界

- 基线 b8053346db29404523d92c34b6fbcd232b60026b。
- 本地分支 codex/interactive-map-checkboxes；不使用 Kimi 的 codex/v1.1-online-product。
- 不改原工作空间，不改研究 JSON，不部署、不 push、不提前合并。
- 继续使用 #DFFF00 / #087F98、Noto Sans SC 和现有 Drawer。

## 步骤

1. 修改 `tests/domain.test.js`：验证真实赛道覆盖、扩展分组、多选组合与未知上市状态、所选赛道的卡面等级和推荐理由。
2. 修改 `02 交付/半导体装备与材料产业图谱/assets/js/domain.js`：新增数据驱动结构模型与通用选项匹配，兼容现有标量调用。
3. 修改同目录 `app.js`：以真实分组和全部赛道按钮替换示例 SVG；原料和下游节点使用单独详情按钮。
4. 修改同目录 `product.js`：原料及下游详情、抽卡复选框、全选/清空、结果与准备动画重置；公司库筛选不变。
5. 修改 `assets/css/style.css`：结构分支、节点按钮、复选框分组和移动端布局，不改变全站设计。
6. `npm test`、JS 语法检查、字体子集更新；独立本地端口做桌面和移动端验证及截图。
7. 新建 `docs/LOCAL_UI_HANDOFF.md`，记录合并边界和验证情况；只做本地提交，等 Kimi 完工后再合并和验证，之后才部署。

## 追加：紧凑下拉复选框

用户提供的企业类型筛选截图作为交互参考。地域、上市状态、赛道范围三个下拉入口同排；赛道菜单按真实分类逐组展开，复用原生 checkbox 和既有数组筛选逻辑。选择不关闭菜单，入口与组标题同步显示摘要；外部点击 / Esc 关闭，Esc 返回焦点。菜单按可用高度内部滚动，手机端菜单占整行宽度。只修改 product.js / style.css，保留已有色彩、字体和数据契约，继续本地验收。

## 追加：右侧详情信息分区

保留现有内容和数据来源，按信息类型增加语义化小标题、浅底分区卡片和分隔。赛道抽屉复用已有 tc-kv，二级细分与龙头公司分别增加内部间隔；公司、来源、原料及下游详情同步采用统一 drawer-section。只改抽屉渲染和样式，本地检查内容数量、详情间跳转、关闭返回与手机宽度，再提交独立分支，不部署。
