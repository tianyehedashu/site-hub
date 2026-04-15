---
name: rakuten-ads
description: 乐天 RMS 广告数据与决策：选项化菜单（A～K）；**run_ad_batch.ps1 一键批次**（JST 区间 + Pack 字母 + 自动 aggregate）；**店铺隔离目录**（`-SiteSlug`）；Expert 默认 `rpp-exp-merchant` 取 slug；交付四块 + **Markdown 表格**呈现数值结论、按需下钻。触发词：乐天广告、RPP、TDA、ROAS、优惠券、DEAL、联盟、购入明细、广告复盘。
allowed-tools: Bash(ziniao:*)
---

# 乐天 RMS 广告报表

`ziniao rakuten <子命令>`：在已登录 RMS 的浏览器会话中请求后台接口，拉取 JSON/HTML/CSV。

**文档与工具**：主说明见本文；[`references/SCRIPTS.md`](references/SCRIPTS.md) 载 **接口集計窗长**、合并/汇总脚本用法、**`rpp-search-item` 跨自然月标准流程**（与 `merge_rpp_search_json.py` / `run_ad_batch` 边界对齐）；可执行脚本在 **`scripts/`**（**`run_ad_batch.ps1` 一键批次**、`aggregate_ad_exports.py`、`merge_*.py` 等）。扩展细节仅从本文链入 SCRIPTS，不叠套多级引用。

**Expert（エキスパート）**：乐天广告后台的**增强型报表**产品线，与标准 RPP/TDA 并列；接口路径常见 `rppexp`、`tdaexp`，对应 **`rpp-exp-*`**、**`tda-exp-*`**。调用报表类子命令须在请求头携带店铺 **`shop_url`（slug）**。**RPP-EXP** = 检索 Expert，**TDA-EXP** = 展示 Expert。slug **默认由 Agent 执行** `ziniao --json rakuten rpp-exp-merchant` 读取 `result.shopUrl`，**勿要求用户手填**；仅当**多店并行、代运营、不确定当前活动标签对应哪一家店**时，再请用户确认站点或切换 `open-store` 后重试。

## 前提

1. 已 `open-store` / `launch` 并登录 RMS。  


## 店铺与会话

1. **站点与会话一致**：拉数前确保 ziniao 当前会话即目标店（`ziniao open-store <site>` 或等价流程）；切换店铺后**重新打开 RMS 广告域**再执行子命令。  
2. **批次目录带店铺标识**：同一仓库内多店并存时，**必须**用 `run_ad_batch.ps1 -SiteSlug <slug>`（或手工将 `-o` 落在 `exports/<slug>/batch_<起>_<止>/`），避免 JSON 与 `summary.json` 混店。`slug` 可与 `shop_url`、店铺简称对齐，便于归档与对账。  
3. **Expert 的 `shop_url`**：**标准流程**为在当前店已登录前提下执行 `rpp-exp-merchant`，将返回的 `shopUrl` 填入 `rpp-exp-report*` / `tda-exp-report*` 的 `-V shop_url=`。**不向用户索要 slug**，除非存在多店歧义或 merchant 返回异常。

## 业务能力菜单（默认以选项呈现给用户）

### 执行与交付规范（必遵守）

1. **首次响应**（用户只说「乐天广告 / 拉报表 / 帮我看广告」等模糊需求时）：先给出下方 **A～K 编号菜单**，每项一行：**编号 + 短标题 + 一句业务价值**，末尾写「请回复 **编号**（可多项，如 `A+C`），并说明**统计区间**（起止日期或最近几周/几月）。」  
2. **用户已点选编号**：**默认不追问日期**——用户说「近7日/上周/本月/上月」等时，Agent **自行按 JST** 换算 `start_date`/`end_date`（`end_date`＝JST 前一自然日），并**优先**用 **`scripts/run_ad_batch.ps1 -Range … -Pack …`**（多店加 **`-SiteSlug`**）一键落盘+汇总（见下 **Agent 默认自动化**）。**Expert（D）** 由 Agent **自动** `rpp-exp-merchant` 取 slug，**不**因缺 slug 打断用户；仅 **区间含糊**（如「大促那段」）、**多店无法区分当前会话**时再简短确认。然后给出**业务结论**（预算建议、SKU 清单、风险点），避免堆砌技术细节。  
3. **用户已说清目标**（例如「上周 RPP 按商品复盘」）：可跳过菜单，直接执行并回报结论。  
4. **批次目录（防混入历史）**：本批所有 `ziniao … -o` 与合并产物落在**同一专用子目录**，勿与旧 JSON 混放在扁平 `exports/`。推荐：`exports/<店铺简写或 site>/batch_<start>_<end>/`（日期同 `-V` 的 `YYYY-MM-DD`）。**汇总只对该目录**执行 `aggregate_ad_exports.py -d <该目录>`（该脚本对 `-d` **不递归**，仅扫此目录一层内 `*.json`）。历史文件可移出批次目录，或将文件名改为 **`_` 开头**（`-d` 会跳过 `_*.json`）。备选：不扫目录，**显式传入本批文件列表**（见 [`references/SCRIPTS.md`](references/SCRIPTS.md)）。  
5. **拉数后的数值汇总（必遵守）**：多文件落盘后**必须**运行 `scripts/aggregate_ad_exports.py`（**类型识别与字段口径**见 [`references/SCRIPTS.md`](references/SCRIPTS.md)）。接口窗长或分页产生的多段 JSON，先用同目录 **`merge_rpp_search_json.py` / `merge_cpnadv_report_json.py`** 合并，再汇总。**禁止**在业务目录（含 `exports/`）新增一次性汇总脚本。Windows PowerShell **避免**多行 `python -c "…"`；显式调用脚本路径（例：`scripts/aggregate_ad_exports.py`，相对于 skill 目录）。汇总范围仅限 **第 4 条** 的批次目录或显式文件列表，避免混入历史 JSON。  
6. **对用户的交付结构（可读性优先，不等于删减能力）**：**默认**按下列四块输出，避免整屏粘贴脚本 STDOUT：① **区间 + JST 截止说明**（一行，含「截止为 JST 前一自然日、不含当日」）；② **店铺 + 本批目录与关键文件名**（含 `-SiteSlug` 或路径中的店铺段）；③ **结论**；④ **行动**（**≤3 条**可执行项，与下文策略矩阵一致）。  
   - **③ 结论的版式**：凡含**多项数值对比**（店汇总、按日 Top、按计划、按 SKU、RPP↔TDA↔券、券品与检索同 SKU 对照），**优先使用 Markdown 表格**呈现，列名用**业务语言**并注明**货币/单位**（如 花费(円)、ROAS、订单数）。表后以**短段落**归纳 2～4 句「结构 + 异常 + 交叉发现」，避免只有表没有判断。  
   - **下钻**：用户要求下钻时，在表格外补充 Top/Bottom 清单、高花费日、计划二次聚合说明等；可引用 `summary*.json` 中的结构化结果。  
   - **不要**把「默认简短」当成「省略分析义务」。

### Agent 默认自动化（减负）

1. **日期**：见上条第 2 点；`rpp-search-item` **不跨自然月**、超窗切段等**硬约束**仍以本文 **子命令附注** 与 SCRIPTS 表为准；脚本在「本月遇 JST 月初首日」时会 **Warning 并回退上月整月**（见脚本注释）。  
2. **一键批次**：让用户（或 Agent 代跑 shell）执行  
   `scripts/run_ad_batch.ps1 -Range Last7|Last30|ThisMonth|PrevMonth -Pack <字母> [-SiteSlug <店铺slug或简称>]`  
   字母与菜单对应：**A**＝复盘包（RPP/TDA item + 券店/券品），**B**＝仅 RPP+TDA item，**C**＝RPP 日+计划+item，**E**＝CPA，**F**＝仅券，**G**＝DEAL CSV；**H/I/J/K** 脚本内提示手工或另参；**D（Expert）** 不在此脚本内代跑，由 Agent 在批次目录落盘 **`rpp-exp-*` / `tda-exp-*`**（**先** `rpp-exp-merchant` 取 `shopUrl` 再传 `-V shop_url=`），再对**同一目录**跑 `aggregate_ad_exports.py`。  
   `-DryRun` 只打印；`-SkipCpnadv` 跳过券；`-NoAggregate` 不自动跑汇总；**`-SiteSlug`** 生成 `exports/<slug>/batch_*/`（**多店强烈建议**）。  
3. **回复忌冗长**：对用户说明「已用 `run_ad_batch -Pack AC -Range ThisMonth`（及 `-SiteSlug` 若有用）」即可，**勿重复**贴 6～8 条独立 `ziniao` 行，除非用户明确要求复制单条或脚本不可用。**结论层**用四块 + 表格，不把 `aggregate` 控制台全文当作交付正文。  
4. **失败回退**：接口超窗/分页或响应异常时，再引用 **merge_*.py**、**fetch_rpp_search_slices.ps1** 与下文附注（保持原有排障能力，不删）。

### 可选业务能力一览（对用户展示的选项文案）

| 编号 | 用户看到的名称（示例） | 能完成的具体业务 | 业务价值 |
|------|------------------------|------------------|----------|
| **A** | 周/月广告总复盘包 | 同一区间内**检索广告（RPP）+ 展示广告（TDA）+ 运用型优惠券**拉齐对照 | 看清钱花在哪类渠道、哪块更划算，直接支撑**下周预算表**与开会材料 |
| **B** | 按商品找「加投 / 减投」名单 | RPP、TDA 各自**按 SKU** 的表现排行与尾部拖累 | 把预算集中到**爆款与高 ROAS 品**，砍掉或收缩**长期吃预算不产出**的 SKU |
| **C** | 日 / 计划 / 商品体检（RPP） | **日、计划** 用 **`rpp-search`**（`selection_type` 1/2）；**按商品** 必须用 **`rpp-search-item`**（勿用 `rpp-search` + `selection_type=3` 替代，见附注） | 定位异常波动、计划结构问题与**拖后腿 SKU**；**搜索词/否词**在 RMS 后台处理 |
| **D** | Expert 深度报表（检索/展示） | RPP-EXP、TDA-EXP 店铺级与**按商品**趋势、分页拉全 | 适合**周报/月报**与老板视角：趋势、聚合周期对比，比单日截图更稳 |
| **E** | 成交成本与广告交叉核对 | CPA 报表与广告花费、订单对照 | 避免「点击很多却不赚钱」**误判为投放问题**，实为落地页或类目转化 |
| **F** | 优惠券与广告是否「打架」 | 优惠券整体 + **按商品** 与广告同期对比 | 防止**券把利润吃光**还误以为广告很成功；决定减券、收窄适用 SKU 或调整广告节奏 |
| **G** | DEAL 活动值不值 | DEAL 导出与同期广告数据对照 | 判断**报名 DEAL 是否带来净增量**，避免只为报表好看续报亏损活动 |
| **H** | 邮件（R-Mail）与广告节奏 | R-Mail 报告与广告高峰对照 | **错峰或统一主题**，减少顾客疲劳，分清邮件带来的量与广告带来的量 |
| **I** | 月度广告购入与结构 | 广告购入明细（按月） | **财务对账、费用结构**、大促月与平月对比，支撑现金流与采购节奏 |
| **J** | 联盟待结算跟进 | 联盟 pending | **回款预期、异常单**清理，避免 pending 堆积影响资金计划 |
| **K** | 历史策略解读与行动清单 | 在已有或刚拉取的数据上，按下文「运营策略」节输出 | 把数据落成**可执行三件事**（加预算/减预算/改商品），减少「有数没结论」 |

**组合建议**：日常 **A+B**；大促前后 **C**；汇报 **D**；让利异常 **F**；对账 **I**；联盟 **J**。

### 编号与数据来源对应（执行参考；对用户不必展开命令）

| 编号 | 主要 `ziniao rakuten` 子命令 |
|------|------------------------------|
| A | `rpp-search-item`、`tda-reports-search-item`、`cpnadv-performance-retrieve`（按需 `…-item` 与分页） |
| B | 同 A，以 item 报表为主 |
| C | **`rpp-search`**（`selection_type`：**1 日 / 2 计划**）+ **`rpp-search-item`**（**按商品**；勿单用 `rpp-search` + `selection_type=3`） |
| D | `rpp-exp-merchant` → `rpp-exp-report` / `rpp-exp-report-item`、`tda-exp-report` / `tda-exp-report-item` |
| E | `cpa-reports-search`，与 A/B 数据对照 |
| F | `cpnadv-performance-retrieve`、`cpnadv-performance-retrieve-item`，与 A/B 同区间 |
| G | `datatool-deal-csv`，与 A/B 同区间对照 |
| H | `rmail-reports`，与按日 `rpp-search` 等对照 |
| I | `shared-purchase-detail` |
| J | `afl-report-pending` |
| K | 不单独对应命令；基于已拉数据 + 下文「基于历史广告数据的运营策略」产出结论 |

### 用户可说的极简话术（仍触发选项）

- 「乐天广告帮我看看」→ 先输出 **A～K 菜单**。  
- 「只要按商品谁该加投」→ 对应 **B**（可再问日期）。  
- 「券和广告一起复盘」→ **A** 或 **F**（确认是否要商品维度）。

具体拉数用的子命令、参数与运营策略细节见下文 **速查表**（含 **子命令附注**）、**常用命令与附注**、**基于历史广告数据的运营策略**。

## 速查表

通用：`-V key=value`、`-o` 落盘、`--json`。

| # | 子命令 | 说明 |
|---|--------|------|
| 1 | `rpp-search` | 检索型广告（RPP），默认店铺侧汇总；**按日/按计划** 用 `selection_type` 1/2（**按商品见 #1′**） |
| 1′ | `rpp-search-item` | RPP **按商品** 的正式入口；**`--all`**（勿用 `#1` + `selection_type=3` 替代） |
| 2 | `rpp-exp-report` | RPP-EXP 报表；**`shop_url`** |
| 2′ | `rpp-exp-report-item` | RPP-EXP 按商品 |
| 2补 | `rpp-exp-merchant` | 当前店 `shopUrl` 等（**不要** `shop_url`） |
| 3 | `cpa-reports-search` | CPA |
| 4 | `cpnadv-performance-retrieve` | 运用型优惠券 |
| 4′ | `cpnadv-performance-retrieve-item` | 同上按商品；表单；`-V page=` |
| 5 | `tda-reports-search` | 定向展示（TDA） |
| 5′ | `tda-reports-search-item` | TDA 按商品（默认参数对齐后台按商品视图） |
| 6 | `tda-exp-report` | TDA-EXP；**`shop_url`** |
| 6′ | `tda-exp-report-item` | TDA-EXP 按商品 |
| 7 | `rmail-reports` | R-Mail（HTML） |
| 8 | `datatool-deal-csv` | DEAL CSV |
| 9 | `shared-purchase-detail` | 广告购入明细 |
| 10 | `afl-report-pending` | 联盟 pending |

列 **#** 仅内部对照；以 `ziniao site list` / `rakuten --help` 为准。

### 子命令附注（约束、异常处置、示例）

以下与上表 **子命令名** 一一对应；拉数前**优先查阅对应命令本节**，再套用通用日期口径（见 **「广告报表的日期区间」**）。

#### `rpp-search`（表 `#1`）

- **按商品（SKU）维度**：凡需要 **RPP 按商品** 列表、排行、加减投 SKU 等，**一律使用 `rpp-search-item`**（见表 `#1′`）。**不要**仅用 **`rpp-search -V selection_type=3`** 充当按商品主数据源：与请求体中的 **`periodType=2`** 等组合时易与乐天侧约定冲突，接口常返回 **`TODO`**（无效或未支持组合），表现为拉数失败、空表或不可解析占位，**不可靠**。
- **参数**：`selection_type` — **1 按日 / 2 按计划**；`3` 在本文档中**不推荐**用于生产拉数（按商品请用 **`rpp-search-item`**）。另有 `campaign_type`（完整枚举以 `ziniao rakuten rpp-search --help` 为准）。**本文不约定通过 ziniao 拉取「按关键词」维度的 RPP 报表**；关键词级导出、否词与出价调整在 **RMS 检索广告后台**完成。  
- **`selection_type=2`（按计划）**：返回体常为 **「计划 × 日」多行明细**，汇总时需按 `campaignName`（及业务所需其它键）**二次聚合**，勿将单行误认为单计划全期总计。  
- **集計期間**：`終了は開始から3ヶ月以内`（自 `start_date` 起连续三个自然月；可跨月但不超窗）。超窗 → 分段 + `merge_rpp_search_json.py`（表见 [references/SCRIPTS.md](references/SCRIPTS.md)）。  
- **`end_date`**：须 **JST 前一自然日**（非当日）；区间勿含**未来日**；否则常见 `集計期間の条件を正しく指定してください。`  
- **仍失败**：在已满足上两条前提下，再 **7～14 自然日** 切段合并（大体量 / 计划×日维）。

近 7 日（**`end_date` = JST 前一自然日**；`start_date` = 该日前推 6 日；生产请按 **JST** 换算）：

```powershell
$end = (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')
$start = (Get-Date).AddDays(-6).ToString('yyyy-MM-dd')
ziniao rakuten rpp-search -V start_date=$start -V end_date=$end --all
```

#### `rpp-search-item`（表 `#1′`）

- **定位**：**RPP 按商品** 的**唯一推荐** ziniao 子命令；与 **`rpp-search` + `selection_type=3`** 不等价，后者易与 **`periodType=2`** 冲突导致乐天返回 **`TODO`**（见 **`rpp-search`** 附注）。
- **`end_date`**：**JST 前一自然日**（非当日）；否则常见 `集計期間の条件を正しく指定してください。` 用户说「含今天」时仍传昨日并注明截止日。  
- **集計期間**：`1ヶ月以内` = **不跨自然月**。跨自然月时：**按月切段**各拉一次 `rpp-search-item`，再用 **`merge_rpp_search_json.py`** 拼成单一 `rpp_item` 文件后汇总；**`run_ad_batch.ps1` 不会自动拆 item**，滚动 `Last30` 等跨月场景须按该流程补全。逐步说明、`_` 文件名约定与汇总解读见 [references/SCRIPTS.md](references/SCRIPTS.md) **「`rpp-search-item` 跨自然月：标准流程」**。  
- **仍失败**：确认未跨月后，再 **7～14 日** 切段。同月内近 30 日：`end_date`=JST 昨日，`start_date`=该日 **前推 29 日**；跨月则按月拆段。同区间 `rpp-search` 按日仍失败则周/双周切片合并。

近 7 日、**满足 item 结束日约束**（`end_date` = 本地**昨日**，`start_date` = 本地今日 − 7 日；生产请按 **JST**）：

```powershell
$end = (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')
$start = (Get-Date).AddDays(-7).ToString('yyyy-MM-dd')
ziniao rakuten rpp-search-item -V start_date=$start -V end_date=$end --all
```

#### `cpnadv-performance-retrieve` / `cpnadv-performance-retrieve-item`（表 `#4` / `#4′`）

- **日期**：`start_date` / `end_date` 为 `YYYY-MM-DD`，JST 与 **广告报表的日期区间**一致；与 RPP/TDA 对照时**区间须对齐**。  
- **分页**：`--all` 或 `-V page=`（item 变体同）。路由与请求由 **ziniao preset** 处理，与其它 `rakuten` 子命令一样在已登录会话中直接调用即可。

#### `tda-reports-search-item`（表 `#5′`）

- **`--all`** 分页；日期 JST、`YYYY-MM-DD`。**集計期間**：`開始から3ヶ月以内`（同 `rpp-search`，非 item 之 1 月）；见 [references/SCRIPTS.md](references/SCRIPTS.md)。

#### 通用：极小响应体与 `"errors"`

- 若文件体积极小（约数十～数百字节）且含 `"errors"`：多为会话失效、XSRF、域名或参数不符合 preset。**核对 `ad.rms.rakuten.co.jp` 登录与活动标签**；并对照本条以上各命令附注逐项排查。

### 按商品（`*-item`）一行例

**`rpp-search-item` / `cpnadv-*`** 的结束日等专项约束，以 **上文「子命令附注」对应条目** 为准（勿仅照抄下列日期）。

```powershell
ziniao rakuten rpp-search-item -V start_date=2026-03-01 -V end_date=2026-03-31 --all
ziniao rakuten cpnadv-performance-retrieve-item -V start_date=2026-03-01 -V end_date=2026-03-07 -V page=0
ziniao rakuten tda-reports-search-item -V start_date=2026-03-01 -V end_date=2026-03-07
ziniao rakuten rpp-exp-report-item -V start_date=2026-03-01 -V end_date=2026-03-05 -V shop_url=<slug>
ziniao rakuten tda-exp-report-item -V start_date=2026-03-01 -V end_date=2026-03-05 -V shop_url=<slug>
# 可选 -V search_product_name=
```


## 广告报表的日期区间

**通用口径**（各命令**专项约束**见上文 **速查表 · 子命令附注**）：

- **广告类子命令**（`rpp-search`、`cpnadv-*`、`tda-*`、`*-exp-*` 等）不提供 `last_days`，须由调用方计算 **`start_date` / `end_date`**（`YYYY-MM-DD`）并经 `-V` 传入。  
- 区间一般为 **起止自然日均闭合**；日界以 **RMS / 日本时间（JST）** 为准。运行环境与 JST 不一致时，须在脚本中 **显式换算** 后再传参。

仅 **JST 前一自然日** 单日（常用于监控；**`rpp-search`**）：

```powershell
$d = (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')
ziniao rakuten rpp-search -V start_date=$d -V end_date=$d --all
```

`datatool-deal-csv` 使用 **无横杠** `YYYYMMDD`。若已有 `$start`/`$end`（`yyyy-MM-dd`），可先转换再传参：

```powershell
$dealStart = $start.Replace('-', '')
$dealEnd = $end.Replace('-', '')
ziniao rakuten datatool-deal-csv -V start_date=$dealStart -V end_date=$dealEnd -V period=daily
```

## 常用命令（缩略）

**日常优先**：`scripts/run_ad_batch.ps1`（见 **Agent 默认自动化**）+ 失败时再查本节与附注。

| 场景 | 命令入口 |
|------|-----------|
| 标准 RPP 日/计划 | `ziniao rakuten rpp-search` · `selection_type` **1**＝按日 **2**＝按计划 |
| RPP 按商品（唯一推荐） | `ziniao rakuten rpp-search-item … --all`（勿用 `selection_type=3`） |
| TDA 按商品 | `ziniao rakuten tda-reports-search-item … --all` |
| 券 | `cpnadv-performance-retrieve` / `cpnadv-performance-retrieve-item` · `--all` 与分页见 `--help` |

## 管理

`ziniao site list` · `site show rakuten/<名>` · `site fork` · `site disable`
