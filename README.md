# site-hub

**一行命令，调用任意站点的已登录接口。**

site-hub 是 [ziniao](https://github.com/tianyehedashu/ziniao-mcp) 的官方站点预设仓库。每个站点提供 JSON 模板（URL、参数、分页、认证）和可选 Python 插件，配合 ziniao 浏览器登录态，无需 API Key 即可抓取数据。

## 现已支持

| 站点 | 预设数 | 说明 |
|------|--------|------|
| **Rakuten** | 17 | RPP/TDA/CPA 广告报表、评论 CSV、RMail、优惠券、订单等 |

> 持续扩展中。查看最新列表：`ziniao site list`

## 快速开始

```bash
# 1. 安装 ziniao
uv tool install ziniao

# 2. 首次使用自动拉取本仓库，或手动更新
ziniao site update

# 3. 在浏览器中登录目标站点，然后直接调用
ziniao rakuten rpp-search -V start_date=2026-03-01 -V end_date=2026-03-07
```

更多命令：

```bash
ziniao site list                    # 查看所有预设
ziniao site show rakuten/rpp-search # 查看预设详情与参数
ziniao site update                  # 更新到最新版
```

## AI Agent 集成

每个站点可附带 `skills/` 目录，包含面向 AI agent 的 SKILL.md。通过 `ziniao skill` 命令安装到 Cursor / Trae / Claude Code 等工具：

```bash
ziniao skill list                        # 查看可安装的 skills
ziniao skill install rakuten-ads         # 安装到 Cursor（默认）
ziniao skill install rakuten-ads -a all  # 安装到所有 agent
```

## 目录结构

```
site-hub/
├── rakuten/
│   ├── rpp-search.json          # 预设模板：RPP 广告报表
│   ├── reviews-csv.json         # 预设模板：评论 CSV
│   ├── ...                      # 更多预设
│   ├── __init__.py              # 可选插件：认证注入、后处理
│   └── skills/
│       ├── rakuten-ads/         # AI Skill：广告报表操作指南
│       │   └── SKILL.md
│       └── rakuten-reviews/     # AI Skill：评论操作指南
│           └── SKILL.md
└── skills/
    └── site-development/        # AI Skill：站点开发指南
        └── SKILL.md
```

- **`<action>.json`** — 声明式预设模板（URL、method、headers、vars、分页、认证策略）
- **`__init__.py`** — 可选 `SitePlugin` 子类，处理复杂认证、动态 URL、响应后处理
- **`skills/<name>/SKILL.md`** — AI agent 技能描述（agentskills.io 规范）

## 贡献

新增站点只需添加一个目录：

```
<site-name>/
  <action>.json      # 最少一个预设
  __init__.py        # 可选
```

开发指南：`ziniao skill install site-development` 安装到 agent，或直接阅读 [SKILL.md](skills/site-development/SKILL.md)。

PR welcome。
