# 1688（site-hub）

预设：`image-search`、`image-compare`、`product`、`supplier`、`media-save`。均需浏览器 **1688 登录态**；图搜类需先打开 `https://www.1688.com/` 以便写入 `_m_h5_tk` 等 mtop cookie。

## 与主仓 `site-hub/` 目录的关系

源码在本仓库的 `1688/` 下；`ziniao` CLI 默认从 `~/.ziniao/repos/site-hub/` 加载。本地改完未 push 时，见仓库根 [README.md](../README.md) 的「本地开发与运行时目录」。

## 成功 / 失败语义

- **`1688/product`**：在**已登录且无验证码拦截**的 tab 中，有效在售详情应返回 JSON 内 `ok: true` 且通常含 `subject` 和/或 `image_urls_sample`。**404、下架、无效 offer** → `ok: false`、`error: offer_page_not_found`。**风控/验证码页**（标题或 HTML 片段命中拦截文案）→ `ok: false`、`error: offer_page_captcha`（需先打开 `www.1688.com` 登录并完成验证）。以上情况 CLI `--json` 外层均为 `success: false`。
- **`1688/media-save`**：无 `cbu01` 主图时 `ok: false`、`error: no_offer_images`。
- **`1688/supplier`**：无效店铺页 `ok: false`、`error: shop_page_not_found`。
- **验证**：正例请使用**当前在售**的 `offer_id` 且在浏览器中已登录；仅用命令行未登录环境可能得到 `offer_page_captcha`，不算成功正例。负例可回归 `offer_page_not_found` / `offer_page_captcha`。

## 常用命令

```bash
ziniao --json 1688 product -V offer_id=<在售数字ID>
ziniao --json 1688 image-search -V image=./your.jpg
```

第三方声明见同目录 [NOTICE.md](NOTICE.md)。

## Agent 技能

路径：`1688/skills/1688-sourcing/`。该目录内 **SKILL 与 `references/*` 自包含**（不依赖 skill 目录外的 Markdown）；安装：`ziniao skill install 1688-sourcing`（需已 `ziniao site update` 拉取 site-hub）。本 README 供仓库浏览者索引，Agent 以已安装 skill 正文为准。
