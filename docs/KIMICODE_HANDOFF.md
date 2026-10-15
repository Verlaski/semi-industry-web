# KimiCode 接手：V1.1 界面与抽卡修订

用途：接手本次前端工作。读者：KimiCode及项目负责人。日期：2026-10-15。对应版本：V1.1界面修订。

## 从这里继续

- 本地仓库：`D:\AITool\AI临时文件\04-kimi\04 金融中台产业研究`，不要重新clone。
- 分支：`codex/v1.1-online-product`；远程：[GitHub分支](https://github.com/Verlaski/semi-industry-web/tree/codex/v1.1-online-product)。本轮提交在V1.1基线`d9217d5`之后，交接文件与实现同次提交，可用`git log -1 --oneline`核对。
- [在线网站](https://teyvat-1-d8g0sba0a7e30225d-1463262475.tcloudbaseapp.com/semi-industry/index.html)，保持hash路由。未合并main。
- 先看[产品说明](01_PRODUCT.md)、[本次验收](UI_REFINEMENT_ACCEPTANCE.md)，维护步骤见[操作手册](04_OPERATIONS.md)。字段和卡面规则只在[数据模型](02_DATA_MODEL.md)维护，取舍只在[决策记录](05_DECISIONS.md)维护。

## 本次明确采纳的用户意见

蓝青与荧光黄绿替换藏青/金色，页面结构保留轻量卡片，不采用新粗野主义的厚黑边。标题与正文使用同一Noto Sans SC，仅代码/Source ID使用Mono。Hero只保留数据更新；长说明放在页脚折叠区，总图名称与阶段靠近，行距放松。

装备和材料主图支持全球/国内/二级细分独立展开、全部展开/收起。主图标题与表头在本部分内吸顶，结束即退出；移动端随当前列显示栏目。其他长表在独立滚动区固定表头。来源页取消跑马灯，精简五列，标题与角标打开右侧来源详情卡。

“AI推荐跟踪龙头”增加单抽/十连不同原创SVG、三组准备文案及进度、金/深紫/蓝灰5/4/3星卡和彩条。等级是跟踪标签，非投资评级；均匀随机、无放回。准备动画不调用AI、不分析个人偏好，筛选和切页会取消；减少动态效果设置下直接揭晓。

## 修改入口

| 文件 | 负责内容 |
| --- | --- |
| 交付站点/assets/css/style.css | 颜色、字体、留白、吸顶、折叠与卡面/准备/礼炮动画 |
| 交付站点/assets/js/app.js | 总图、产业卡、来源五列表；保留原始研究内容和详情数据 |
| 交付站点/assets/js/product.js | 三类侧栏、主图表头与折叠按钮、页脚说明、抽卡状态与礼炮清理 |
| 交付站点/assets/js/domain.js | CompanyRepository及cardCategory；重点赛道集合FOCUS_TRACKS |
| tools/build_web_fonts.py | 从已保存的OFL字体生成网页子集；新增汉字后重建 |
| tools/package_deploy.py | 静态白名单打包，CSS/JS/字体内容摘要避免旧缓存 |

“交付站点”指`02 交付/半导体装备与材料产业图谱`。代码继续使用原生前端，未增加框架或外部CDN。字体许可证位于该站点`assets/fonts/OFL.txt`。

## 边界与已知待办

四份研究JSON、后端、云函数与PDF本轮未修改。正式companies.json仍待另一研究开发线提供；当前为249条兼容记录，233条可抽取，未知上市身份不会被当作未上市。不要从卡面等级推断财务质量、买卖建议或最终公司主体。

云端复用既有环境`teyvat-1-d8g0sba0a7e30225d`，本轮仅发布`semi-industry/`静态子目录。不要新建环境、改变共享权限或重发函数。发布与回退按操作手册，不要把签名、密钥或.local产物提交。环境的其他站点/服务保持原状。

仓库原有未跟踪文件`CloudBase网页发布实战手册_跨Agent交接.md`、`PLAN_V1.1.md`、`文档维护规范.md`属于用户本地材料，未加入本次提交，也不要删除。

后续若改变卡面规则，先更新数据模型中的产品配置，保留跟踪标签说明与均匀随机概率；若接入真正的在线AI，再单独明确输入、隐私与真实分析状态。新增研究/公司名称后重建字体并检查页面。
