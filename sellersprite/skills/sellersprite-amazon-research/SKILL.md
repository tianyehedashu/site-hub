---
name: sellersprite-amazon-research
description: 卖家精灵 Amazon 选品与关键词：选产品、查竞品、关键词挖掘/反查/流量对比、选市场与市场分析（v2/v3 网页 API）。触发词：卖家精灵、SellerSprite、sellersprite、选产品、查竞品、关键词挖掘、选市场、市场分析、关键词反查、流量词。
allowed-tools: Bash(ziniao:*)
---

# 卖家精灵 · Amazon 选品与关键词

在 **已登录** `www.sellersprite.com` 的浏览器标签页内，用 `ziniao sellersprite <action>` 调用网页同源 API（Cookie 认证，无需开放平台 Key）。

**预设与变量完整列表**见 [references/PRESETS.md](references/PRESETS.md)。

## 前提

1. `ziniao launch --url https://www.sellersprite.com` 或已有 Chrome 会话，**完成登录**。
2. 多实例时显式指定：`ziniao --session chrome-<端口> sellersprite <action> ...`（`session list` 查端口）。
3. 带复杂筛选的 POST（`product-research`、`competing-lookup-v3`、`relation-traffic-extend-v3` 等）**body 须与网页抓包一致**；默认 body 仅为最小示例，用 `ziniao site fork sellersprite/<action>` 扩展。

## 能力地图

| 业务 | 代表 action | 说明 |
|------|-------------|------|
| 选产品 | `product-research` | v3 主列表，支持 `--all` 分页 |
| 查竞品 | `competing-lookup-v3` | v3 主列表；配合 `asin-resolve` → `node-peers` 两步走 |
| 关键词挖掘 | `keyword-miner` | 拓展词；翻页用 `-V page_num` |
| 关键词收录 | `keyword-checker-v2-page` | 返回 HTML，非 JSON |
| 关键词反查 / 流量 | `relation-reversing-v3` 等 | 见 PRESETS 表 |
| 选市场 / 市场分析 | `market-research-*` | v2 为主；含 HTML 与 JSON 混合 |

## 推荐工作流

### 1. 关键词拓展

```bash
ziniao navigate "https://www.sellersprite.com/v3/keyword-miner"
ziniao --json sellersprite keyword-miner -V keyword="yoga mat" -V page_num=1
```

### 2. 选产品（分页拉全）

```bash
ziniao navigate "https://www.sellersprite.com/v3/product-research"
ziniao --json sellersprite product-research -V market=1 -V page_num=1 --all -o product-research.json
```

⚠️ 若筛选条件复杂，先在网页点「开始筛选」→ DevTools 复制 Request Payload → fork 预设替换 body。

### 3. 查竞品（ASIN → 同类目列表）

```bash
ziniao --json sellersprite competing-lookup-asin-resolve-v3 -V asin=B0XXXX
# 从返回取 nodeIdPath，再：
ziniao --json sellersprite competing-lookup-node-peers-v3 -V node_id_path="172282:541966:..."
```

### 4. 关键词反查

```bash
ziniao navigate "https://www.sellersprite.com/v3/keyword-reverse"
ziniao --json sellersprite relation-reversing-v3 -V asin=B0XXXX -V market=US
```

### 5. 选市场 / 报告数据

- 表单筛选用 `market-research-form`（HTML）。
- 图表 JSON 用 `market-research-report-v2`、`market-research-keyword-trend-v2` 等；`node_id_path` 在 URL 中须 **URL 编码**。

## 运维

```bash
ziniao site list | findstr sellersprite   # Windows
ziniao site show sellersprite/keyword-miner
ziniao site update site-hub               # 更新预设
```

## 故障排查

| 现象 | 处理 |
|------|------|
| 401 / 跳转登录 | 当前 tab 未登录；重新 navigate 到卖家精灵并完成登录 |
| 空 body 超大结果 / 超时 | POST 预设勿传空 body；fork 后只保留必要筛选字段 |
| 验证码 | 人工完成后再执行；勿自动化绕过 |
| 连错 Chrome | `session list` + `--session` |

## 与开放平台 API 的关系

部分 v3 路径与 SellerSprite 开放平台 REST 相近，但 **字段名与鉴权不同**。本 skill 只覆盖 **网页 Cookie 会话**；开放平台请用官方 API Key，勿混用预设 URL。
