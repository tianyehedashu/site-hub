# 1688 预设与变量（ziniao CLI）

预设 ID 形如 `1688/<action>`。均需当前浏览器标签页具备 **1688 登录 cookie**；图搜类建议先在本标签打开 `https://www.1688.com/` 以便写入 `_m_h5_tk` 等 mtop 相关 cookie。

全局选项：`ziniao --json …` 输出 `{ success, data, error }` 信封；`mode: js` 返回体会出现在 `data` 内（解析后的 JSON 字段）。

## `1688/image-search`

- **说明**：单页以图搜款（mtop 上传 + 结果列表）。
- **navigate_url**：`https://www.1688.com/`
- **变量**


| 变量           | 类型   | 必填  | 默认  | 说明                        |
| ------------ | ---- | --- | --- | ------------------------- |
| `image`      | file | 是   | —   | 本地路径、http(s) URL 或 base64 |
| `begin_page` | int  | 否   | 1   | 结果页码（从 1 起）               |
| `page_size`  | int  | 否   | 40  | 每页条数（约 10–60）             |


- **示例**

```bash
ziniao --json 1688 image-search -V image=./ref.jpg -V begin_page=1 -V page_size=40
```

## `1688/image-compare`

- **说明**：多页聚合比价（同图搜链路，合并多页后给价格 min/max/median 等统计）。
- **navigate_url**：`https://www.1688.com/`
- **变量**


| 变量          | 类型   | 必填  | 默认  | 说明           |
| ----------- | ---- | --- | --- | ------------ |
| `image`     | file | 是   | —   | 待搜图片         |
| `max_pages` | int  | 否   | 3   | 最多拉取页数（1–10） |
| `page_size` | int  | 否   | 40  | 每页条数         |


- **示例**

```bash
ziniao --json 1688 image-compare -V image=./ref.jpg -V max_pages=3
```

## `1688/product`

- **说明**：打开详情页后从 HTML 抽取标题、`subject`、若干 `cbu01` 主图 URL（启发式，模板变更可能漂移）。
- **navigate_url**：`https://detail.1688.com/offer/{{offer_id}}.html`
- **变量**


| 变量         | 类型  | 必填  | 说明             |
| ---------- | --- | --- | -------------- |
| `offer_id` | str | 是   | 详情 URL 中的数字 ID |


- **示例**

```bash
ziniao --json 1688 product -V offer_id=<在售数字ID>
```

## `1688/supplier`

- **说明**：店铺首页 HTML，抽取标题与可选 `companyName` 片段。
- **navigate_url**：`{{shop_url}}`（由变量注入）
- **变量**


| 变量         | 类型  | 必填  | 说明                                |
| ---------- | --- | --- | --------------------------------- |
| `shop_url` | str | 是   | 店铺首页 URL，如 `https://xxx.1688.com` |


- **示例**

```bash
ziniao --json 1688 supplier -V shop_url=https://example.1688.com
```

## `1688/media-save`

- **说明**：从详情 HTML 解析 `cbu01` 图片 URL；配合 CLI `**--save-images <前缀>`** 按 `media_contract` 落盘。
- **navigate_url**：`https://detail.1688.com/offer/{{offer_id}}.html`
- **变量**：同 `1688/product` 的 `offer_id`（必填 str）。
- **示例**

```bash
ziniao --json 1688 media-save -V offer_id=<在售数字ID> --save-images exports/1688/offer
```

## 成功 / 失败语义（`data` 内 JSON）

以下字段为脚本返回体中的常见键；`--json` 外层 `success: false` 时通常伴有顶层 `error` 字符串（与 `data` 内 `error` 对齐或等价）。


| 预设                               | 成功                                              | 常见失败 `error`                                                    |
| -------------------------------- | ----------------------------------------------- | --------------------------------------------------------------- |
| `product`                        | `ok: true`，常有 `subject` 和/或 `image_urls_sample` | `offer_page_not_found`（404/下架/无效页）；`offer_page_captcha`（验证码/风控） |
| `media-save`                     | `ok: true` 且 `items` 非空                         | `no_offer_images`（无 cbu01 图，多为无效页或模板变更）                         |
| `supplier`                       | `ok: true`                                      | `shop_page_not_found`                                           |
| `image-search` / `image-compare` | 无统一 `ok` 字段时以返回 `error` 键为准；成功时含 `offers` 或统计字段 | `missing_image`、`no_m_h5_tk`、`upload_failed` 等                  |


**正例**：须在**已登录**且**未出现验证码拦截**的会话中，对**当前在售** `offer_id` 调用；未登录环境常见 `offer_page_captcha`，不算成功正例。

**列表来源**：`ziniao site list` 中 `[repo]` 表示来自 `site-hub` 仓库克隆目录（`ziniao site update site-hub` 更新）。