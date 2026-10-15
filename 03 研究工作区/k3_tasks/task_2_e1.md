# task_2：主体异常批 E1（斜杠组合 + 疑似重复，30 行）

输入：`verify_batches\batch_e1_slash_dup.json`
输出：`verify_out\batch_e1_slash_dup.result.json`（batch 字段写 "batch_e1_slash_dup"）

对每行做**实体裁决**：
- 斜杠组合（如 Nikon/Canon、EVG/SUSS、东京电子/东京精密、NGK/NTK、Soulbrain/Lake Materials/DNF、Unisem/FST）：拆成多个独立实体，各占一条输出记录，entity_decision 写"拆分"
- 疑似重复（如 SCREEN vs SCREEN Holdings、SHINKO 新光电气工业 vs Shinko Electric、TEL 各写法）：裁决合并为同一实体（一个 company_id，多个 aliases）或确认不同主体，entity_decision 写"合并/独立 + 依据"
- 一行输入产出多条实体时，source_keys 都填该行的 key

已知参考（需核验确认）：
- SCREEN Holdings = SCREEN（迪恩士，7735.T），合并
- Shinko Electric Industries（新光电气工业，6967.T）两个写法是同一家，合并；注意与材料侧"新光电气"同
- 东京精密 = Accretech（7729.T），与东京电子 TEL（8035.T）是两家不同公司
- NGK Insulators 日本碍子（5333.T）与 Niterra 日本特殊陶业（5334.T，旧称 NGK Spark Plug）是两家不同公司；NTK CERATEC 是 NGK Insulators 的陶瓷品牌/事业部
- EVG（奥地利 EV Group，家族企业非上市）与 SUSS MicroTec（德国，SMHN.DE）独立；SUSS 已在 verify_out\batch_eu.result.json 中建过档，复用其 company_id
- TRUMPF Hüttinger 是 TRUMPF 通快集团（非上市）的电子子公司，合并为一个实体
- 默克 Merck KGaA 已在 batch_eu 建档（MRK.DE）；霍尼韦尔 Honeywell（HON.US）已在 batch_us 建档——拆分后复用两边 company_id
- 大族封测：大族激光（002008.SZ）旗下封测设备子公司，核验其独立 IPO 状态（曾申报创业板，确认当前是否上市/撤回）
- 英杰电气（300820.SZ 上市）与英杰晨晖（其子公司的 RF 电源业务）：主体裁决并注明
- 中电科 43 所/合肥圣达：裁决事业单位与产业化公司的主体关系
- 韩国 Soulbrain（357780.KQ?）/Lake Materials（281740.KQ?）/DNF、Unisem/FST：逐一核验 KOSDAQ 代码，不确定就留空写 unresolved
