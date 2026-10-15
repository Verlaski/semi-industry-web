# V1.1 在线产品实施计划

用途：落实本轮完整开发任务，供项目负责人和接手人员检查。更新时间：2026-10-15。版本：V1.1。

目标：在现有原生网页上交付公司/赛道侧栏、公司库、小时行情、结构化CSV、数据驱动PDF、机会抽卡及实际在线部署。

架构：保留四份研究JSON。CompanyRepository在正式公司库缺失时仅构造临时显示模型。CloudBase事件函数提供行情及报告API，NoSQL保存行情和仅服务端可读的PDF缓存，Python ReportLab负责报告。浏览器不直接连接行情供应商。

技术：HTML/CSS/原生JavaScript、Node.js事件函数、Python/ReportLab、NoSQL、CloudBase静态托管和HTTP网关。

## 顺序与验收

1. 前端：两类Drawer、公司库、Badge、抽卡骨架；检查键盘、移动端、缺少companies.json的显示及正式库适配。
2. 发布：查询现有环境，复用静态托管独立semi-industry目录及独立API路由，实测浏览器/MIME/中文资源路径。
3. 行情：三个测试symbol；EastMoney/Tencent可切换；小时触发、保留最后有效值、区分行情时间和获取时间；测试主备和失败。
4. CSV：赛道与leader拆表，含二级引用、来源编号、UTF-8 BOM、公式注入防护。
5. PDF：ReportDataProvider→ReportModel→Builder→Engine；四类报告，本地至少三类逐页渲染检查，云端实测生成/缓存/签名下载。
6. 抽卡：结构化理由、均匀随机无放回、组合筛选、复制清单；排除未拆组合主体，避免一张卡代表多家企业。
7. 集成：全流程在线验收，维护README/CHANGELOG及五份docs，分支提交并推送，不合并main。

## 已核实资源及边界

- 现有环境：teyvat-1-d8g0sba0a7e30225d，ap-shanghai，个人版，NoSQL运行中。
- 静态托管已启用；新站放semi-industry子目录，保留其他站点和网关路由。
- 现有Storage桶是公共读。报告采用ADMINONLY的report_cache/report_files集合和短时签名下载，避免改变现有桶或新增付费桶。后续可换私有Storage适配器。
- quotes_latest、report_cache、report_files三个新集合均仅管理员/服务端可读写。
- 不创建正式companies.json，不修改产业分类、研究数据及历史主体判断，不使用研究草稿作为生产库。

## 视觉约束

沿用浅色投研终端及原有产业链布局；藏蓝、白灰、少量金色。中文使用微软雅黑/思源字体栈；桌面侧栏宽约620px，移动端全屏。普通微动效180—240ms，抽卡约650ms，均尊重减少动态效果设置。

## 部署前核对

用户本次任务已明确授权实际部署。使用现有套餐、默认域名和原生NoSQL，无新环境、套餐升级、自定义域名、TCP数据库或容器依赖。事件函数不回显环境/请求头/上下文；公共API只读取本项目公开研究数据。报告链接签名有效期30分钟，缓存集合禁止浏览器直读。真实地址、函数状态及权限以在线验收记录为准。
