# 卖家精灵（SellerSprite）

Amazon 选品 / 关键词 / 市场分析 / 竞品与流量分析。预设均为 **Tier 1 Cookie 同源 fetch**，须在已登录 `www.sellersprite.com` 的浏览器标签页执行。

## 前提

1. `ziniao launch` 或 `open-store` 后登录卖家精灵。
2. 多 Chrome 实例时用 `ziniao --session chrome-<端口> sellersprite <action> ...` 显式指定会话。
3. 带复杂筛选的 POST 预设（`product-research`、`competing-lookup-v3` 等）**请求体须与网页抓包一致**；可用 `ziniao site fork` 扩展 body。

## 常用命令

```bash
ziniao site list | findstr sellersprite
ziniao --json sellersprite keyword-miner -V keyword=wireless charger -V page_num=1
ziniao --json sellersprite product-research -V market=1 -V page_num=1 -o product-p1.json
```

## Agent 技能

`sellersprite/skills/sellersprite-amazon-research/` — 安装：`ziniao skill install sellersprite-amazon-research`
