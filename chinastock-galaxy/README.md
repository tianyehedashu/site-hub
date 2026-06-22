# 中国银河证券（chinastock-galaxy）

持仓 / 资产类接口的 **Cookie 同源 fetch 模板**。银河各端（APP WebView、H5、交易端）真实 URL 与 JSON 字段因版本而异，须自行抓包后填入变量。

## 预设

| Action | 用途 |
|--------|------|
| `holdings-url` | 对完整 HTTPS URL 发起 GET |
| `holdings-post` | 对完整 URL 发起 POST，`post_json` 为 Request Payload |
| `holdings-relative` | 先打开 `landing_url`，再 fetch 同域相对路径 |

## 前提

登录银河相关页面后再调用；若接口要求 CSRF 或自定义头，请 `ziniao site fork` 后增加 `header_inject`。

## Agent 技能

`chinastock-galaxy/skills/chinastock-holdings/` — 安装：`ziniao skill install chinastock-holdings`
