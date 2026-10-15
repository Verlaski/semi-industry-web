# 本地 UI 并行修改交接

本轮只完成独立本地开发和网页测试。未推送、未合并、未部署 CloudBase。

## 隔离状态

- 基线：`b8053346db29404523d92c34b6fbcd232b60026b`。
- 独立分支：`codex/interactive-map-checkboxes`。
- 工作空间：`C:\Users\verla\.codex\worktrees\interactive-map-checkboxes\04 金融中台产业研究`。
- 原工作空间与 Kimi 使用的 `codex/v1.1-online-product` 未切换、未修改。
- 本地预览：`http://127.0.0.1:8013/index.html#/overview`；抽卡页 `#/discovery`。
- 预览关闭后可在本工作空间网站目录运行 `python -m http.server 8013 --bind 127.0.0.1`。

## 完成内容

### 数据驱动产业链结构

`SemiDomain.structureModel(data)` 读取 `equipment.tracks` / `materials.tracks`，按实际 `group` 分组，保持原数据顺序；新增分组与赛道不需要改图。

当前包含装备 23 个赛道、材料 15 个赛道、3 项基础原料和 4 个下游应用环节。所有赛道节点使用现有 `data-open-track` 打开 Track Drawer，保持 overview 路由；原料和下游节点打开对应关系说明 / 代表性厂商详情。原料关系、厂商名称均取自原 JSON，没有补写公司事实。手机端改为纵向流式布局。

### 抽卡复选框

- 地域、上市状态、赛道范围三个下拉复选框入口同排展示，桌面和手机均保持一行；入口显示当前选择摘要，可键盘操作。
- 同一类别取 OR；地域、状态、赛道之间取 AND；某类别无选项时表示不限。
- 地域两个选项均勾选只收录能够归入其中的记录，未知地域不会被自动归类。
- 已上市 / 未上市同时勾选仍排除上市身份未知的公司。
- 赛道菜单按装备 / 材料分列，各实际分类分别下拉展开逐赛道复选框，显示本组已选数量；支持本组全选 / 清空和全局重置。
- 三个菜单互斥展开，勾选时保持菜单打开，点击外部或按 Esc 收起；Esc 返回入口焦点。菜单限制高度并内部滚动，按屏幕剩余高度自适应。
- 条件更新取消准备动画与礼炮，清除旧结果，禁用旧清单复制，重新计算候选数。
- 卡面等级和推荐理由只从所选赛道关系产生。单抽、十连、无放回和礼炮框架保持。
- `CompanyRepository.filter` 的标量调用继续兼容，公司库原有下拉筛选不变。

## 涉及文件

网站目录：`02 交付/半导体装备与材料产业图谱/`。

| 文件 | 变更 |
| --- | --- |
| assets/js/domain.js | structureModel、selection / selected、多选过滤与卡面 / 文案范围 |
| assets/js/app.js | 真实赛道结构图，替换示例 SVG |
| assets/js/product.js | 原料 / 下游详情、复选框、分组操作与筛选重置 |
| assets/css/style.css | 数据节点、双链关系、复选框与移动端布局 |
| assets/fonts/*.woff2 | 新增界面文字的 Noto 字体子集 |
| tests/domain.test.js | 真实赛道完整覆盖、多选逻辑、卡面范围回归 |

没有更改研究 JSON、正式公司数据、行情 Provider、PDF Engine、CloudBase 配置或云端资源。

## 已完成验证

- `npm test`：15 项通过（含新增 3 项）。
- JS 语法检查、`git diff --check` 通过。
- 桌面 1440 × 1080 / 手机 390 × 844，页面无横向溢出；导航本身保留移动端横向滚动。
- 38 个赛道按钮逐个打开正确标题，关闭后仍在 overview。
- 7 个原料 / 下游按钮逐个打开正确详情。
- 键盘 Enter 打开赛道，Esc 关闭详情。
- 赛道分组全选 9 个前道设备、清空恢复不限。
- 刻蚀设备 + 半导体硅片：兼容池 14 家，十连 10 家无重复，卡面全部属于所选两赛道。
- 地域复选、状态复选、重置、准备中切换条件均通过。
- 追加三入口同排下拉交互：桌面 / 手机同一 top 坐标；地域和状态多选摘要、菜单互斥、外部点击关闭、Esc 关闭与焦点返回、赛道分类展开和计数均通过。手机菜单底部保留 12px 可视空间，页面无横向溢出。
- 手机端选 3 个赛道并单抽，最终 1 张卡面正常揭晓。
- 公司库标量筛选：249 条记录，刻蚀筛选 5 条，原有表格正常。
- 浏览器控制台无 JavaScript error。

截图保存在独立工作空间 `output/qa/interactive-map-checkboxes/`（忽略文件，不加入产品仓库）。上述数量只描述本分支基线，不能替代 Kimi 完成正式公司库后的验收数字。

## Kimi 完工后的合并顺序

1. 确认 Kimi P0/P1 已提交，并核对公司数据与关系契约。
2. 在整合分支合入本地分支提交；不要整文件覆盖 Kimi 修改。
3. 优先人工检查 `domain.js` 和 `product.js`：保留 Kimi 的正式公司加载、ID、关系和 Candidate Pool 实现，将本轮复选框数组条件接入新关系。
4. `app.js` 结构图继续从实际 tracks 分组生成；不要恢复旧示例 SVG。
5. 根据整合后的所有文本重新运行 `python -m tools.build_web_fonts`，避免覆盖 Kimi 新增文字字形。
6. 运行合并后的单元测试和真实正式数据网页测试，覆盖多地域 / 多上市状态 / 多赛道、单抽 / 十连、Drawer、公司库、行情 / CSV / PDF 原有链路。
7. **只有合并后的本地网页测试通过，才进行 CloudBase 部署。** 本轮本地测试不代表合并后的版本已通过。

## Known Issues / Technical Debt

| 类别 | 状态 | 是否阻塞本轮 | 处理人 / 阶段 |
| --- | --- | --- | --- |
| Data / Discovery | 本分支冻结在正式公司库之前，仍是兼容候选；上市状态筛选可为 0，不能把未知身份推断成未上市 | 否；正式整合测试前必须接入 Kimi 数据 | Kimi P0/P1 + Codex 整合 |
| Frontend | 结构图与详情重复引用同一 track，属于入口复用；原料及下游没有独立 track_id，只展示 JSON 已有说明 | 否 | 保留现有数据语义 |
| Integration | Kimi 并行改动可能涉及 CompanyRepository / Candidate Pool 同一区域，尚未尝试合并 | 阻塞部署 | Kimi 完工后 Codex 整合 |
| CloudBase / Quote / PDF | 本轮未改服务端；后续仍需合并版本回归后再发布 | 阻塞部署，非本地 UI 阻塞 | Codex 整合验收阶段 |
