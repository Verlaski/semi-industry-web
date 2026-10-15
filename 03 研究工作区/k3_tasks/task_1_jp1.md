# task_1：日本公司批1（35 行）

输入：`verify_batches\batch_jp_1.json`
输出：`verify_out\batch_jp_1.result.json`（batch 字段写 "batch_jp_1"）

逐行核验日本公司：法定名称、通行中文名、注册地（日本）、上市状态、东证代码（xxxx.T 格式）、多地上市、更名/重组史入 aliases。

已知雷区（重点核验）：
- JSR：2024 年被 JIC 私有化退市——应判非上市并注明归属
- Kokusai Electric（日立国际电气）：2023-10 在东证 IPO，代码 6525.T
- Hitachi High-Tech：日立子公司，确认当前是否仍上市（8036.T 历史代码）
- JX金属：JX Advanced Metals，2025-03 东证 IPO，核实代码（疑 5016.T）
- Fujikin（富士金）、樫山工业、NAMICS、千住金属、关东化学：疑为非上市，需正面证据（官网无上市信息可注 C 级"未见上市记录"）
- Shinkawa（新川）：上市状态不确定，重点查
- Panasonic 语境是"松下电子材料"：主体建 Panasonic Holdings 6752.T，entity_decision 注明材料事业部归属

初验可用 Yahoo chart 接口批量确认代码有效性和公司英文名（exchangeName=Tokyo、currency=JPY），但上市状态结论仍以 JPX/公司 IR/权威财经页为准，证据 URL 记录实际打开的页面。
