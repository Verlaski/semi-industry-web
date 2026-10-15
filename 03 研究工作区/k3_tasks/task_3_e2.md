# task_3：母子/品牌关系批 E2（23 行）

输入：`verify_batches\batch_e2_relationship.json`
输出：`verify_out\batch_e2_relationship.result.json`（batch 字段写 "batch_e2_relationship"")

对每行裁决**赛道龙头地位的实体归属**（子公司本体 vs 上市母公司 vs 品牌），核验该实体自身上市状态。**不得把母公司代码赋给未单独上市的子公司**；母公司信息写入 entity_decision。

已知参考（需核验确认）：
- 凯世通 Kingstone：万业企业（600641.SH）旗下，非上市
- 北京七星流量计：北方华创（002371.SZ）体系内，非上市
- 兴福电子：兴发集团（600141.SH）旗下，重点核验其是否已独立上市（科创板 IPO 进程）
- 凯德石英：835179.BJ 北交所上市（江丰电子参股），核验代码有效性
- 华海诚科：疑 688535.SH 科创板，核验
- 至正股份（603991.SH）与 AAMI（先进封装材料国际，原 ASMPT 材料业务、智路/建广系）：核验重组收购当前状态，两个实体分别建档
- 紫金佳博：紫金矿业系键合丝企业，非上市子公司方向核验
- 衡所华威（天津，塑封料）：上市状态待查
- 长川科技 300604.SZ（收购新加坡 STI 备注）、光力科技 300480.SZ（收购以色列 ADT/英国 LP）、新益昌 688383.SH：上市公司主体确认
- UP Chemical：韩国注册、雅克科技（002409.SZ）子公司，非上市，country_region=韩国
- 长春塑封料：台湾长春集团（非上市）旗下，country_region=中国台湾
- Atotech：2022 年被 MKS Instruments 收购退市，非上市，注明归属（MKS 已在 batch_us 建档）
- Berliner Glas：ASML 2021 年收购，非上市
- Cymer：ASML 2013 年收购，非上市
- Gigaphoton：小松制作所（6301.T）子公司，非上市
- Resonac 力森诺科：4004.T 上市（昭和电工+日立化成合并而来），旧名入 aliases
- Entegris：ENTG.US 纳斯达克上市（2022 收购 CMC Materials）
- Silfex：Lam Research 子公司，非上市
- 普莱克斯 Praxair：2018 年与 Linde 合并，主体并入 Linde（LIN.US，已在 batch_kr_tw_other 或 batch_eu 建档，复用其 company_id），普莱克斯作 aliases
- Edwards 爱德华：英国品牌、瑞典 Atlas Copco（ATCO-A.ST）旗下，非上市
