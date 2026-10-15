# K3 协作任务包 · 半导体产业图谱公司核验

你是被主会话（Kimi Code）通过 CLI 派单的研究代理。当前日期 2026-10-15（作为 access_date）。
本目录 4 份任务文件，**按 task_1 → task_4 顺序依次执行**。

## 全局纪律（每个任务都适用）

- 核验工具：WebSearch/FetchURL；日股可用 Yahoo chart 接口脚本化初验（`https://query1.finance.yahoo.com/v8/finance/chart/8035.T?interval=1d&range=1d` 返回 longName/exchangeName/currency）；A股可用东财 suggest 接口（`https://searchapi.eastmoney.com/api/suggest/get?input=名称或代码&type=14&token=D43BF722C8E33BD1C740FD9E4C0DEA0F`）
- 证据等级：A=交易所官网/公司IR/招股书/年报（实际打开过）；B=财经数据站（东财/雅虎/腾讯行情等）；C=行业媒体；不得编造，查不到留空写 unresolved
- ticker 格式：A股 688012.SH/002371.SZ/920186.BJ（688/689/600/601/603/605→SH；000/001/002/003/300/301→SZ；4xx/83x/87x/88x/920→BJ）；港股 00522.HK；美股 AMAT.US；日股 8035.T；欧股 ASML.AS；台股 2344.TW 或 6488.TWO（柜买）；韩股 195870.KS / 166090.KQ（KOSDAQ）
- market 词表：A股/港股/美股/日股/欧股/台股/韩股/其他海外；listing_status 只用 上市/非上市/空字符串（未知，**查不到≠非上市**）
- provider_symbols 仅 A股/港股/美股填 tencent 格式（sh688012/sz002371/bj920186/hk00522/usAMAT）
- company_id：通行英文缩写大写；纯中文名用拼音缩写大写。**先读 `verify_out/` 下已有 4 份结果文件（batch_us/batch_eu/batch_jp_2/batch_kr_tw_other），同一实体复用其 company_id**
- 每个实体都要有 evidence（至少一条带 URL）；confidence: high/medium/low
- **只许写 `verify_out/` 目录下的指定结果文件，不得修改仓库任何其他文件**
- 每份结果写完用 `python -m json.tool` 校验

## 输出统一 schema

```json
{"batch":"<任务批次名>","entities":[
 {"source_keys":["输入行key"],"entity_decision":"主体边界裁决（无特殊关系留空）",
  "company_id":"...","name_cn":"...","name_en":"...","short_name":"...","aliases":[],
  "country_region":"...","listing_status":"上市|非上市|",
  "listings":[{"listing_id":"<ID>_<EXCH>","market":"...","exchange":"...","ticker":"...","primary":true,"provider_symbols":{"tencent":"..."}}],
  "evidence":[{"org":"...","title":"...","url":"https://...","publish_date":"","data_year":"2026","metric":"上市状态与代码","caliber":"...","region":"...","type":"交易所|公司官网|财经数据站|行业媒体","level":"A|B|C","remark":""}],
  "confidence":"high|medium|low","unresolved":""}]}
```

路径根：`D:\AITool\AI临时文件\04-kimi\04 金融中台产业研究\03 研究工作区\`
输入在 `verify_batches\`，输出到 `verify_out\`。
