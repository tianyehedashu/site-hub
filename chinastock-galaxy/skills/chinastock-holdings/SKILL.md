---
name: chinastock-holdings
description: 中国银河证券持仓/资产接口模板：GET 完整 URL、POST JSON、同域相对路径 fetch。须在已登录银河 H5/交易页的标签页执行；URL 须自行抓包。触发词：银河证券、chinastock、持仓、资产、银河 H5。
allowed-tools: Bash(ziniao:*)
---

# 中国银河 · 持仓 / 资产（模板预设）

`chinastock-galaxy` 提供 **三种 Cookie 同源 fetch 模板**，不包含固定业务 URL——银河 APP WebView、H5、交易端各版本接口 path 不同，须 **DevTools / `ziniao network list` 抓包** 后填入变量。

## 前提

1. `ziniao launch` 或连接已有 Chrome，打开银河相关页面并完成 **登录**。
2. 抓包时确认：Method（GET/POST）、完整 URL、Request Payload、必要 Header（CSRF 等）。
3. 若需自定义头，执行 `ziniao site fork chinastock-galaxy/holdings-post` 并增加 `header_inject`。

## 三个预设

| Action | 何时用 |
|--------|--------|
| `holdings-url` | Network 里是 **完整 HTTPS URL**（GET） |
| `holdings-post` | **POST** + JSON body |
| `holdings-relative` | 只有 **同域相对 path**（如 `/api/v1/positions`），先 `navigate_url` 到交易页 |

## 示例

### GET 完整 URL

```bash
ziniao --json chinastock-galaxy holdings-url -V holdings_url="https://example.chinastock.com.cn/trade/api/v1/asset?token=..."
```

### POST JSON

```bash
ziniao --json chinastock-galaxy holdings-post \
  -V holdings_url="https://example.chinastock.com.cn/trade/api/v1/positions" \
  -V post_json='{"pageNo":1,"pageSize":50}'
```

`post_json` 必须是 **合法 JSON 字符串**（与抓包 Request Payload 一致）。

### 相对路径

```bash
ziniao --json chinastock-galaxy holdings-relative \
  -V landing_url="https://example.chinastock.com.cn/trade/" \
  -V relative_path="/api/v1/positions"
```

脚本会在 `location.origin + relative_path` 上 `fetch`，自动带 Cookie。

## 抓包流程

```bash
ziniao network list --clear
# 在浏览器打开持仓页、刷新或切换 tab 触发接口
ziniao network list --filter "chinastock" --json
```

复制 `url`、`method`、`requestBody` 到对应预设变量。

## 注意

- 预设 **不保证** 跨版本兼容；接口变更后重新抓包并 fork。
- 勿将含 token 的 URL 提交到公开仓库；变量仅在本地 `-V` 传入。
- 相对路径预设依赖 `landing_url` 与接口 **同域**，否则 Cookie 不会带上。
