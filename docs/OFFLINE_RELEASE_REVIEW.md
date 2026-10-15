# 离线版本发布记录

用户已确认发布，并指定文件名、在线/离线按钮文案。开发分支 codex/offline-download，基于 main f6371bc。

## 压缩包

- 文件名：半导体装备与材料产业链龙头图谱_上海业务部_离线版本.zip
- 大小：678,451 字节
- SHA-256：`28247bda26ec234df8042cbfacac6bfda04106f76904b591cf4ed5db41d34329`
- COS 对象：`semi-industry/offline/28247bda26ec234d/半导体装备与材料产业链龙头图谱_上海业务部_离线版本.zip`
- 公共下载：[离线版本](https://7465-teyvat-1-d8g0sba0a7e30225d-1463262475.tcb.qcloud.la/semi-industry/offline/28247bda26ec234d/%E5%8D%8A%E5%AF%BC%E4%BD%93%E8%A3%85%E5%A4%87%E4%B8%8E%E6%9D%90%E6%96%99%E4%BA%A7%E4%B8%9A%E9%93%BE%E9%BE%99%E5%A4%B4%E5%9B%BE%E8%B0%B1_%E4%B8%8A%E6%B5%B7%E4%B8%9A%E5%8A%A1%E9%83%A8_%E7%A6%BB%E7%BA%BF%E7%89%88%E6%9C%AC.zip)
- 上传时间：2026-10-15T21:24:56+08:00

现有存储桶 ACL 为 READONLY，未修改权限。匿名 HTTP GET 返回 200、application/zip、Content-Disposition attachment；完整下载与本地 SHA 一致。浏览器点击按钮实测保存的中文文件名正确。

包内 12 个必要文件，含本地字体及 OFL 许可、GitHub 图标，五份必要数据库内嵌 index.html。保留 245 家公司、38 个赛道、426 条关系、801 条来源。无行情数据、工作区文档、云函数、SDK、凭证、研究草稿或 Git 目录。

## 在线与离线

- 在线按钮：GitHub 图标 + 点击下载离线版本，直接使用 COS 公共链接。
- 离线按钮：GitHub 图标 + 点击访问在线url，新标签页打开现有在线地址。
- 离线启动读取内嵌数据，不发出数据 fetch、不加载行情、不启动行情刷新；CSP connect-src none 阻止后台连接。保留图谱、筛选、抽卡、详情卡和 CSV；无云端 PDF 下载入口。
- 原始来源的外部链接需联网后手动打开。
- config/offline-release.json 是公开下载配置，不包含签名地址或 Secret。构建时将公共 URL 注入 SEMI_CONFIG.offlineDownload。

## 验证

Python 10 项、Node 16 项、JS 语法及 diff 检查通过。离线数据投影保持全部前端消费字段及 CSV 一致。ZIP 解压后的 7 页面渲染、公司搜索、逐层详情返回、十连抽及 CSV 下载通过本地 HTTP 预览测试。内置浏览器不允许 file://，未将 HTTP 测试冒充双击验收。

在线构建本地实测下载成功，公司库正常显示 245 条记录、行情更新时间和报价。未变更浏览器 SDK、登录、安全域名、数据库权限或行情/PDF 云函数。

## 后续更新

先生成新包并确认内容，再使用内容摘要目录上传，避免覆盖旧包。匿名下载校验成功后更新 config/offline-release.json，再构建/发布网页。只修改数据库不会自动更新已经发布的离线 ZIP；需重新打包。使用 python -m tools.build_offline 生成文件，打包白名单在 tools/build_offline.py。

图标源为 https://brand.github.com/GitHub_Logos.zip 中的 SVG/GitHub_Invertocat_Black.svg。

## 正式发布验收

2026-10-15T21:29:06+08:00（UTC+8）：已合并 main、push 并发布静态网页，应用代码提交 76d7328。线上 index.html 及 6 项 CSS/JS/图标资源与本地构建逐字节一致。线上按钮实际下载成功；下载名准确（浏览器已有同名文件时自动加序号）。公司库行情更新时间正常显示 UTC+8。COS 匿名下载复核通过。
