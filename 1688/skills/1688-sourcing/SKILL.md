---
name: 1688-sourcing
description: 1688 找品与 ziniao 预设（图搜、详情、店铺、落盘）；触发词：1688、以图搜款、跨境找品、site-hub 1688。
allowed-tools: Bash(ziniao:*)
---

# 1688 货源（ziniao site-hub）

本 skill **自包含**：预设 ID、变量、CLI 示例与成功/失败语义见 **[references/PRESETS.md](references/PRESETS.md)**；第三方说明见 **[references/THIRD_PARTY.md](references/THIRD_PARTY.md)**。不要依赖本目录以外的 Markdown 或仓库文件来完成决策。

## 快速入口

1. 确认已安装站点仓库：`ziniao site update site-hub`（或等价方式使 `1688/*` 预设出现在 `ziniao site list` 且来源为 `[repo]`）。
2. 在已登录 1688 的浏览器会话中，按 [references/PRESETS.md](references/PRESETS.md) 选用预设并传 `-V`。
3. 判读结果：优先看 `--json` 的 `success` 与 `data` / `error`；详情页遇验证码见 PRESETS 中 `offer_page_captcha` 说明。
