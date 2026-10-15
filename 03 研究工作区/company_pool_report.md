# 龙头公司候选池统计与研究准备

用途：说明提取覆盖、统计口径及下一步调研。读者：项目负责人及研究人员。
最后更新时间：2026-10-15。对应版本：V1.1 研究准备（非正式公司库）。

本轮仅处理本地源数据，未开展上市信息外部核验。候选行可能仍是组合主体，数量不等于经核实法人数量。

## 统计结果

| 指标 | 数量 |
| --- | ---: |
| 一级/二级 leader 原始数组引用 | 396 |
| 一级原始引用 | 259 |
| 二级原始引用 | 137 |
| 明确并列拆开后记录（粗去重前） | 408 |
| 粗去重后候选公司行 | 249 |
| 自动折叠重复记录（前者减后者） | 159 |
| 不同原始名称写法 | 311 |
| 需要复核的候选行 | 156 |
| 含ticker_hint/ticker_hints的候选 | 20 |
| 仅一级出现 | 176 |
| 仅二级新增发现 | 37 |
| 一级和二级均出现 | 36 |

原始引用按数组元素计数；明确顿号、分号并列可拆出多个occurrence。斜杠不自动拆主体。合并数是重复记录数，不是已验证别名企业对数。

| 原始数据/层级/角色 | 引用数 |
| --- | ---: |
| equipment/L1/china | 59 |
| equipment/L1/global | 86 |
| equipment/L2/china | 38 |
| equipment/L2/global | 99 |
| materials/L1/china | 46 |
| materials/L1/global | 68 |

| 角色 | 候选行（可交叉） | 拆分后引用 |
| --- | ---: | ---: |
| global leader | 145 | 260 |
| china leader | 108 | 148 |

## 国家地区

仅汇总原country和名称明确地区；不按china角色补注册地，多值不任选一项。

| 证据汇总地区 | 候选行 |
| --- | ---: |
| 中国 | 4 |
| 美国 | 26 |
| 日本 | 69 |
| 韩国 | 9 |
| 中国台湾 | 7 |
| 荷兰 | 3 |
| 德国 | 12 |
| 英国 | 1 |
| 法国 | 2 |
| 瑞士 | 1 |
| 奥地利 | 3 |
| 新加坡 | 1 |
| 中国香港 | 0 |
| 其他 | 0 |
| 缺失 | 105 |
| 多值/其他原文：中国/韩国 | 1 |
| 多值/其他原文：中国香港/新加坡 | 1 |
| 多值/其他原文：奥地利/德国 | 1 |
| 多值/其他原文：德国/日本 | 1 |
| 多值/其他原文：德国/美国 | 2 |

## 主要公司主数据脏点

分类可交叉，按涉及候选行数排序。

| 问题类别 | 候选行 |
| --- | ---: |
| 国家地区缺失 | 105 |
| 中文英文名称无法可靠对应 | 45 |
| 母公司 / 子公司 / 品牌关系 | 25 |
| 股票代码异常或待确认 | 23 |
| 疑似重复主体 | 20 |
| 斜杠组合企业 | 16 |
| 其他无法机械判断的问题 | 6 |
| 同一 ticker_hint 对应多个候选主体 | 0 |

核心问题是公司身份和赛道说明混写、国内龙头常缺注册地、简称与全称并存、斜杠多主体，以及母子公司/品牌/收购前后名称边界不清。

## 仅一级出现的候选

AMEC、DJEL、KINGSTONE、LEADMICRO、NAURA、PNCS、RSIC、SKYVERSE、上海新阳、上海锡喜、东莞亚聚电子、中环领先、中瓷电子、中电科43所/合肥圣达、中科仪、中科信、中科科化、中船特气、京仪装备、先锋精科、兴森科技、兴福电子、凯德石英、北京七星流量计、北京华丞电子、华海诚科、华特气体、南大光电、同飞股份、国科精密、安集科技、富创精密、康强电子、彤程新材、德邦科技、恒硕科技、恒运昌、新松机器人、新莱应材、晶瑞电材、有研新材、汉钟精机、江丰电子、江化微、沪硅产业、河北中瓷、深南电路、清溢光电、潮州三环、烁科精微、烟台一诺、珂玛科技、珠海越亚、石英股份、神州半导体、神工股份、福晶科技、科益虹源、立昂微、精测电子、紫金佳博、至正股份、臻宝科技、英杰电气/英杰晨晖、茂莱光学、菲利华、衡所华威、西安奕材、路维光电、金宏气体、隆华科技、雅克科技、飞凯材料、鼎龙股份、龙图光罩、UPCHEMICAL、CHANGWAH、GLOBALWAFERS、NANYAPCB、UNIMICRON、长春塑封料、AAMI、AT&S、BASF、BERLINERGLAS、CARLZEISSSMT、HENKEL、HERAEUS、MERCKKGAA、PFEIFFER、SILTRONIC、TRUMPF、TRUMPFHÜTTINGER、LINDE、默克MERCKKGAA/霍尼韦尔HONEYWELL、DAIFUKU、DAIHEN、DNP、FERROTEC、FUJIFILM、FUJIKIN、FUJIMI、GIGAPHOTON、HIRATA、HORIBA、HOYA、IBIDEN、JSR、JXMETALS、KANTOCHEMICAL、KASHIYAMA、KYOCERA、LINTEC、MARUWA、MITSUBISHICHEMICAL、MITSUIHIGH-TEC、NAGASE、NAMICS、NGK/NTK、NGKINSULATORS、NGKINSULATORS/NTKCERATEC日本碍子、NIKON/CANON、NITERRA、NITTO、PANASONIC、RESONAC、RORZE、SCREENHOLDINGS、SENJUMETAL、SHIN-ETSU、SHINKO、SHINKOELECTRIC、SHINWACONTROLS、SMC、STELLACHEMIFA、SUMCO、SUMITOMOBAKELITE、SUMITOMOELECTRIC、TAIYONIPPONSANSO、TANAKA、TOK、TOPPANPHOTOMASK、TOSOH、TOTO、东京电子/东京精密、住友化学、住友重工/SENSUMITOMO、泰谷诺、AIRLIQUIDE、EGIDE、COMET、ADVANCEDENERGY、ADVANCEDTHERMALSCIENCESATS、AIRPRODUCTS、BROOKSAUTOMATION、BROOKSINSTRUMENT、COORSTEK、CYMER、DUPONT、ENTEGRIS、HONEYWELL、ICHORSYSTEMS、MKSINSTRUMENTS、MOMENTIVE、PHOTRONICS、SILFEX、ULTRACLEANHOLDINGSUCT、普莱克斯、EDWARDS、HAESUNGDS、HANAMATERIALS、MKE、SKMATERIALS、SKSILTRON、SOULBRAIN/LAKEMATERIALS/DNF、UNISEM/FST

## 仅二级新增发现的候选

上海中艺、凯格精机、吾拾微、和研科技、大族封测、大族激光/大族封测、奥特维、宇晶股份、微见智能、德龙激光、文一科技、旺矽科技、格朗瑞、猎奇智能、精智达、联动科技、芯慧联、芯睿科技、迈为股份、青禾晶元、惠特科技、鸿劲精密、EVG、EXELLIQ、EVG/SUSS、ATOTECH、G&N/冈本OKAMOTO、ACCRETECH、APICYAMADA/YAMAHAROBOTICS、SCREEN、SHINKAWA、SUMITOMO/SEN住友重工、YAMADA/APICYAMADA、CLASSONETECHNOLOGY、FORMFACTOR、HANWHA、TECHWING

## 处理规则与实施验证

1. 读取现有源文件，一级/二级字符串或字典均支持，类型异常立即报错。
2. 拆开明确并列、剥离冒号后说明，提取代码提示，完整保留备注和引用原文；斜杠组合只标记。
3. 相同中/英文清洗名粗去重；所有名称变体、代码、地区和逐条引用均保留，简称包含关系只列复核。
4. 生成草稿、八类复核清单和统计，再独立遍历原始数据校验覆盖、类型及定位。
5. 限定文件范围后本地提交，不推送或合并。

原脚本实跑得到285行，含说明文本导致的伪公司，不能当作有效主体数。未发现阻止运行的语法错误；发现逻辑问题：二级字符串仅按中点拆分，说明混入名称；漏拆顿号/分号并列；二级字典被忽略；仅识别末尾括号，中途代码残留；代码备注整体塞入ticker；国内缺地区；中国香港/新加坡被武断归新加坡；只留首个名称、代码、地区及角色；tracks集合丢失逐条原文和位置；正则过滤变音字符。

根目录无README.md，以交付目录现有README为准。Windows命令行使用UTF-8及PYTHONIOENCODING=utf-8，脚本也会设置输出编码。

## 草稿新增字段说明

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| normalized_key | string | 清洗和粗去重辅助键；不是最终company_id |
| name_cn_variants / name_en_variants | string[] | 同组全部清洗名，代表名称只取其中一项 |
| country_regions / country_region | string[] / string | 全部地区证据；显示值用斜杠连接，多值保留复核 |
| country_basis | string | 地区取值依据，不将china角色当作注册地 |
| ticker_hints / ticker_hint | string[] / string | 全部代码线索；只有唯一值时填单值；未经证券代码核验 |
| review_reasons | object[] | category为八类问题代码，reason为具体原因；与review_required及review_reason同步 |
| occurrences | object[] | 每次有效引用；同一位置并列多家公司分别保留一条 |
| occurrence.dataset / track_id / sub_name / role | string | 数据集、赛道、细分名称、global或china角色 |
| occurrence.level / sub_index / leader_index / piece_index | int / int或null / int / int | 层级1或2；数组位置从0起；一级sub_index为null |
| occurrence.source_pointer | string | 原始JSON中leader元素的精确路径，配合dataset及piece_index定位 |
| occurrence.source_text / raw_name | string | 完整原始leader文字 / 剥离说明后的名称片段 |
| occurrence.country_raw / country_regions | string / string[] | 原始country字段和本次引用的地区证据 |
| occurrence.source_metadata | object | 原始share、tag、products、source_id等赛道关系属性，仅存引用内 |
| statistics | object | 原始引用、拆分记录、候选和复核数量，校验时独立重算 |

无最终company_id、上市状态或证券市场确认字段。空地区与组合主体属于已登记Review，结构/覆盖错误属于Error。

## 下一阶段上市信息调研批次

先解决主体边界及疑似重复，再按国家/市场分批。常规每批15—25个候选，复杂关系每批8—12个。先确定归属，避免交叉领用。

1. 主体关系批：斜杠组合、品牌/子公司、收购及疑似重复，先确定拆分、关联或合并。
2. 代码线索批：含代码、IPO或辅导编号，核验法定名称、交易所、代码性质及有效日期。
3. 地区缺失批：用官网或交易所披露确认注册主体/地区，再分配上市研究。
4. 已有地区海外批：日本；美国；中国台湾/韩国；欧洲；其他及多地区分别处理。
5. 整合批：同ticker、多地上市和历史别名交叉核验，最后才确定company_id。

每项保留候选辅助键、全部原始引用、确认主体、来源网址、访问日期和结论。normalized_key随清洗规则变化，不是最终company_id。

## 范围与复现

`python "03 研究工作区/extract_companies.py"` 生成三个草稿；
`python "03 研究工作区/validate_company_pool.py"` 校验。Error非零退出，已列明Review不影响通过。

自由文本note中偶然提及的企业未全量识别；括号内收购对象/品牌保留为线索，不自动生成主体。材料二级目前只有note，无结构化leader；未向正式数据补写。
