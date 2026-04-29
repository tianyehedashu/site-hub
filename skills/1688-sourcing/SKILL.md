---
name: 1688-sourcing
description: 1688 找品与 ziniao 预设（图搜、详情、店铺、落盘）；触发词：1688、以图搜款、跨境找品、site-hub 1688。
allowed-tools: Bash(ziniao:*)
---

# 1688 货源（site-hub）

预设与参数见同仓库 **[1688/README.md](../../1688/README.md)**。

要点：

- 预设来源为 **site-hub**（`ziniao site list` 中 `[repo]`），不在 ziniao 核心包内置。
- 未登录或触发风控时，`1688/product` 可能返回 `offer_page_captcha`；登录并完成验证后再试。
- 正例应在**无验证码拦截**的会话下出现 `ok: true` 且含 `subject` 或主图 URL；纯 404/下架为 `offer_page_not_found`。
