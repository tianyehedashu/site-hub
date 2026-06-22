# 卖家精灵预设一览

预设 ID 形如 `sellersprite/<action>`。均需 **Cookie 登录**；POST 类筛选接口请对照 DevTools Request Payload，必要时 `ziniao site fork`。

## 选产品 / 查竞品（v3）

| Action | 说明 | 分页 |
|--------|------|------|
| `product-research` | 选产品主列表 `POST /v3/api/product-research` | `--all`（`pageNum`） |
| `competing-lookup-v3` | 查竞品主列表 `POST /v3/api/competing-lookup` | `--all` |
| `competing-lookup-asin-resolve-v3` | 输入 ASIN 解析 `nodeIdPath`（查竞品第一步） | 单页 |
| `competing-lookup-node-peers-v3` | 已知 `nodeIdPath` 拉同类目竞品 | `--all` |
| `competitor-lookup-nodes-v2` | 查竞品类目树 `GET .../nodes?marketId=` | 单页 |
| `competing-lookup-query-quota-v3` | 查竞品剩余查询次数 | 单页 |
| `competing-lookup-export-v3` | 查竞品导出任务 `POST .../export` | 单页 |

## 关键词（v3 / v2）

| Action | 说明 | 分页 |
|--------|------|------|
| `keyword-miner` | 关键词挖掘 `POST /v3/api/keyword-miner` | 手动 `-V page_num` |
| `keyword-checker-v2-page` | 关键词收录页 HTML（v2） | 单页 |

## 关键词反查 / 流量（v3 relation）

| Action | 说明 |
|--------|------|
| `relation-config-v3` | 反查/流量模块配置 |
| `relation-reversing-v3` | 关键词反查主列表（`-V asin=`） |
| `relation-ta-high-frequency-words-v3` | 反查高频词 |
| `relation-traffic-prepare-v3` | 流量词准备/刷新任务 |
| `relation-traffic-variations-stat-v3` | 流量词变体统计 |
| `relation-traffic-extend-v3` | 拓展流量词主表（须 fork body） |
| `relation-multi-stat-traffics-v3` | 多 ASIN 流量统计 |
| `relation-stat-keywords-v3` | 流量对比-关键词统计（须 fork body） |

## 选市场 / 市场分析（v2）

| Action | 说明 |
|--------|------|
| `market-research-form` | 选市场表单 POST → **HTML** |
| `market-research-tags` | 标签列表 JSON |
| `market-research-analyze-v2` | 刷新节点 analyze（两参路径） |
| `market-research-analyze-month-v2` | 刷新节点 analyze（三参，含月份表 ID） |
| `market-research-detail-v2` | 市场分析报告页 HTML |
| `market-research-report-v2` | 图表数据 report JSON |
| `market-research-keyword-trend-v2` | 行业需求关键词趋势 |
| `market-research-ai-analysis-v2` | AI 解读任务提交（form-urlencoded） |
| `ai-analysis-daily-quota-v3` | AI 分析当日剩余次数 |

## 常用变量

- `market` / `market_id`：站点 ID（常见 `1` = 美国）
- `month`：月份 `yyyyMM`
- `page_num` / `page_size`：对应 body 的 `pageNum` / `pageSize`
- `node_id_path`：类目路径，含 `:` 时在 URL 中须 **URL 编码**（`172282%3A281407`）
- `asin`：亚马逊 ASIN

## 示例

```bash
ziniao --json sellersprite keyword-miner -V keyword="wireless charger" -V page_num=1
ziniao --json sellersprite product-research -V market=1 -V page_num=1 --all -o products.json
ziniao --json sellersprite relation-reversing-v3 -V asin=B0XXXX -V market=US
ziniao --json sellersprite market-research-tags -V market_id=1
```

## 注意

- `product-research` 与 `competing-lookup-v3` 请求体形态相近但 **URL 与业务不同**，勿混用。
- 验证码 / 登录失效时先人工完成验证再重试。
- 多 Chrome：`ziniao --session chrome-<端口> sellersprite <action> ...`
