---
name: google-flow-images
description: 通过 ziniao 子命令在已登录浏览器中调用 Google Labs（Flow）与 aisandbox：文生图（**Imagen 4 默认走 runImageFx；传 -V model_name_type=NARWHAL / GEM_PIX_2 自动切 batchGenerateImages 用 Nano Banana**）、参考图生成（batchGenerateImages + fifeUrl 下载 + --save-images 自动落盘；支持 0~N 张参考图 + 多张生成）、上传参考图等。触发词：Google Flow、labs.google、Imagen、Nano Banana、参考图、多参考图、多张生成、文生图、ziniao google-flow、--save-images。
allowed-tools: Bash(ziniao:*)
---

# Google Flow（Labs）图片生成 — Skill

在 **已登录 Google 的 Chrome** 中，用页面 Cookie 换 `access_token`，调用 `aisandbox-pa.googleapis.com`。**不要手写临时脚本**：用子命令 + `--save-images` 完成所有操作。

## 环境

1. `ziniao launch --user-data-dir "%LOCALAPPDATA%\Google\Chrome\User Data"`
2. 打开 `https://labs.google/fx/tools/flow` 确认会话有效  
3. `ziniao site update`（或确保 `site-hub/google-flow` 在 `~/.ziniao/repos/site-hub`）

## 子命令一览（`ziniao google-flow …`）

| 子命令 | 必填 | API | 作用 |
|--------|------|-----|------|
| `imagen-generate` | `-V prompt=` | `runImageFx` **或** `batchGenerateImages` | 文生图。**默认 Nano Banana Pro（`NARWHAL`）** 走 `batchGenerateImages` 返回 fifeUrl；Pro 配额耗尽时**默认自动降级到 `GEM_PIX_2`**（可 `-V fallback_model=""` 关闭）；`-V model_name_type=IMAGEN_3_5` 改走 `runImageFx` 用 Imagen 4。多张用 `-V candidates_count=N`（1~8）。**单张沿用 daemon auto 120s；count≥2 显式 `--timeout 300`** |
| `imagen-ref-generate` | `-V prompt=`（images/image 可选） | `batchGenerateImages` | Nano Banana 生图：有参考图做 style/subject 约束，无参考图等价于 Nano 纯文生图。**默认 `NARWHAL`**，可 `-V model=GEM_PIX_2` 切快速版；`-V images=a,b,...` 多参考；`-V count=N`（1~4）多张。**preset 声明 `default_timeout_ms=180000`（cover 1 参考 × count=1），count≥2 / 多参考图显式 `--timeout 300~480`** |
| `imagen-upload` | `-V image=` | `flow/uploadImage` | 仅上传参考图，返回 mediaId |
| `auth-session` | — | session | 调试会话 |
| `media-fetch` | `-V media_key=` | tRPC | 按 key 取资源 |

**全局**：所有 site 子命令支持 `-o file.json` 保存 JSON；图片优先用 `--save-images`。

## 核心使用场景

### 1. 文生图 + 图片落盘

```bash
# 默认：Nano Banana Pro（NARWHAL，Pro 耗尽自动降级 GEM_PIX_2）
# 单张 40~90s；daemon 已把 page_fetch 列为 slow（auto 120s），一般无需 --timeout
uv run ziniao google-flow imagen-generate \
  -V prompt="A red lantern in snow, Chinese watercolor style" \
  --save-images exports/flow-lantern
```

生成文件：`exports/flow-lantern-0.jpg`（按 magic bytes 自动扩展名）。返回 JSON 里 `usedModel` 可判断最终出图模型；`fallbackUsed: true` 即发生了降级。

多张：`-V candidates_count=4`（Pro 每张 40~90s，显式 `--timeout 480` 覆盖 daemon 默认 120s）

#### 1.1 切到 Imagen 4（摄影真实感，走 runImageFx）

```bash
uv run ziniao google-flow imagen-generate \
  -V prompt="..." -V model_name_type=IMAGEN_3_5 \
  --save-images exports/flow-lantern-imagen
```

Imagen 4 快且偏摄影真实感；Nano Banana 系偏创意/编辑/文字进图。

#### 1.2 切到 Nano Banana 2（更快档）

```bash
uv run ziniao google-flow imagen-generate \
  -V prompt="..." -V model_name_type=GEM_PIX_2 -V fallback_model=NARWHAL \
  --save-images exports/flow-lantern-fast
```

#### 1.3 关闭自动降级（严格要求指定模型）

```bash
uv run ziniao google-flow imagen-generate \
  -V prompt="..." -V fallback_model="" \
  --save-images exports/flow-lantern-strict
```

耗尽时直接返回 429 给调用方，便于编排层决策。

### 2. Nano Banana 生图（0~N 参考图）

#### 2.0 纯文生图（不传参考图）

```bash
uv run ziniao google-flow imagen-ref-generate \
  -V prompt="Sun Wukong riding clouds, Chinese ink painting" \
  --save-images exports/flow-nano-text
```

不传 `image` / `images` 时 `imageInputs[]` 为空，**直接做 Nano 纯文生图**。默认 `NARWHAL`；Pro 配额耗尽时 `-V model=GEM_PIX_2`。

#### 2.1 单参考图（向后兼容）

```bash
uv run ziniao google-flow imagen-ref-generate -V image=./ref.png -V prompt="Remove headband, guofeng ink painting" --save-images exports/flow-ref-out
```

> PowerShell 一行，勿用 `\` 续行；反斜杠在 PS 不是续行符，必须一行写完或改用反引号 `` ` ``。

#### 2.2 多张参考图（`images` 逗号分隔）

```bash
uv run ziniao google-flow imagen-ref-generate -V images="./subject.png,./style.jpg,https://host/mood.webp" -V prompt="Blend subject pose with style palette, cinematic lighting" --save-images exports/flow-multi-ref
```

- `images` 优先级高于 `image`（若两者都填，仅用 `images`）。
- 每个条目独立解析：本地路径 → 读文件；`http(s)://` → daemon 侧抓取；其他当作 base64 直通。

#### 2.3 一次生成多张（`-V count=N`，1~4）

```bash
uv run ziniao google-flow imagen-ref-generate -V image=./ref.png -V prompt="Sun Wukong riding clouds above cherry blossoms, ink wash" -V count=3 --save-images exports/flow-multi-out
```

每张自动用**不同 seed**（`-V seed=0` 随机；`-V seed=42` 则 42/43/44…可复现）。

#### 2.4 切回 Nano Banana 2（`GEM_PIX_2`，更快 / Pro 配额耗尽时）

```bash
uv run ziniao google-flow imagen-ref-generate -V images="./a.png,./b.png" -V prompt="Quick draft" -V model=GEM_PIX_2 -V count=2 --save-images exports/flow-fast
```

> 默认是 Pro (`NARWHAL`)；`GEM_PIX_2` 用于赶时间或 Pro 当日配额耗尽时兜底。

流程全自动（`batchGenerateImages`）：
1. 获取 session token + 创建 Flow 项目（或复用 `-V project_id=`）
2. 依次上传每张参考图 → 收集 mediaId 列表
3. 获取 reCAPTCHA Enterprise token（action=`IMAGE_GENERATION`）
4. 构造 `requests[]`：`count` 个 item，每个 item 的 `imageInputs` 包含全部参考图，每个 item 用不同 seed
5. 从返回的 `media[].image.generatedImage.fifeUrl`（GCS 签名 URL）下载每张图
6. 保存到 `--save-images PREFIX` → `PREFIX-0.jpg`、`PREFIX-1.jpg`…

#### 2.5 复用已有项目

```bash
uv run ziniao google-flow imagen-ref-generate -V image=./ref.png -V prompt="..." -V project_id="6f472ba3-32ca-483f-9805-7df4abd0b647" --save-images exports/flow-ref-v2
```

### 3. 仅上传参考图

```bash
uv run ziniao google-flow imagen-upload \
  -V image=./ref.png \
  -V prompt="记录意图（仅元数据）"
```

返回 `mediaId` / `workflowId`。

## 变量类型

### `type: file`（单文件）
`-V image=./a.png`、HTTP(S) URL、或 base64。本地大文件自动走 `@@ZFILE@@` 路径标记（避免 daemon TCP 1MB 限制）。

### `type: file_list`（多文件）
`-V images=a.png,b.png,https://host/c.webp`（逗号分隔）。空串 → `[]`；每个元素独立解析为 `@@ZFILE@@` / `@@ZURL@@` / base64 直通。daemon 收到后递归展开为 base64 数组，preset JS 里 `b.images` 是 `string[]`。

## 模型与配额

> Google 对 labs.google 的图像模型**按账号 × 模型 × 日**独立计配额（`PUBLIC_ERROR_PER_MODEL_DAILY_QUOTA_REACHED`）；具体额度未公开，UTC 0 点前后重置。下表只收录**已实证可调**的枚举，避免写入未验证值。

### 模型支持矩阵

| UI 名称 | 枚举值（传给 `-V model=` / `-V model_name_type=`） | 用途端点 | 子命令 | 参考图 | 画幅支持 | 配额池 |
|--------|-----------------------------------------------|---------|-------|--------|---------|--------|
| **Nano Banana Pro** | `NARWHAL` *(imagen-generate + imagen-ref-generate 默认)* | `batchGenerateImages` | `imagen-generate`（默认）/ `imagen-ref-generate` | ✅（可选） | SQUARE / PORTRAIT / LANDSCAPE | 独立（**更紧**） |
| **Nano Banana 2** | `GEM_PIX_2` *(imagen-generate 默认 fallback)* | `batchGenerateImages` | `imagen-generate`（降级）/ `imagen-ref-generate` | ✅（可选） | SQUARE / PORTRAIT / LANDSCAPE | 独立 |
| **Imagen 4** | `IMAGEN_3_5` | `runImageFx` | `imagen-generate`（需显式 `-V model_name_type=IMAGEN_3_5`） | ❌ | 4 种（见下） | 独立 |

- **为什么参考图默认 NARWHAL**：Pro 出图细节更稳定，且配额独立于 GEM_PIX_2；当 Pro 耗尽时再 `-V model=GEM_PIX_2` 作为备份。
- **端点互斥**：`runImageFx` 只接受 Imagen 枚举（传 `GEM_PIX_2` / `NARWHAL` 直接返回 `400 INVALID_ARGUMENT`）；Nano 只能走 `batchGenerateImages`。`imagen-generate` 预设已内建按模型路由，调用方零感知。
- **耗时差异**：GEM_PIX_2 ≈ 10~25s/张；NARWHAL ≈ 40~90s/张。
- **超时策略（重要）**：
  - `imagen-generate` 单张：**沿用 daemon `_SLOW_COMMANDS` auto 120s**（Pro p99 ≤ 120s，卡死能在 2 分钟内暴露）。
  - `imagen-ref-generate` 单张（1 张参考 × count=1）：preset 预置 `default_timeout_ms=180000`，给参考图上传留余量。
  - 多张（`candidates_count` / `count ≥ 2`）或多张参考图：**agent 自行 `--timeout 300~480`**，按 `每张 120s × 数量` 粗估。
  - CLI `--timeout N` 始终优先于 preset 默认；不要靠拉大 preset 默认值兜底，否则程序卡死会延迟发现。
- **图片完整性**：三者返回都带 SynthID 隐形水印。

### 配额性质速查

| 维度 | 是否共享 | 说明 |
|------|---------|------|
| 同账号 · 同模型 · 同日 | 共用同一池 | 超出即 429 `RESOURCE_EXHAUSTED` |
| 同账号 · **跨模型** | 独立池 | `GEM_PIX_2` 用完仍可跑 `NARWHAL` / `IMAGEN_3_5` |
| 同账号 · **跨端点** | 独立池 | `runImageFx` 配额不影响 `batchGenerateImages` |
| 跨账号（不同 Google 登录） | 独立池 | 换 Profile / 换账号可刷新 |
| UTC 0:00 前后 | 自动重置 | 日界附近若临近耗尽，跨日即可恢复 |

### 配额自检原则

账户与日期强相关，skill 不固化"某天谁可用"。调用前如果不确定：

1. 跑下面"最小探测命令"里对应的一条（消耗 1 次配额），拿回来 `ok:true` 即证可用。
2. 命中 `429 / PUBLIC_ERROR_PER_MODEL_DAILY_QUOTA_REACHED` → 走下一节的三种应对。
3. 只信**最近一次的真实响应**，不要参考历史样本。

### 配额耗尽时的三种应对

1. **自动降级（推荐，零人工干预）**：在 `imagen-generate` 中加 `-V fallback_model=...`。Nano 主模型命中 `PUBLIC_ERROR_PER_MODEL_DAILY_QUOTA_REACHED` 时，preset 会**复用同一 projectId + 获取新的 reCAPTCHA token** 自动重试 fallback 模型。仅支持 Nano 之间互为降级（`GEM_PIX_2 ↔ NARWHAL`）。

   ```bash
   # 优先快、省 Pro 配额；GEM_PIX_2 耗尽时退回 NARWHAL
   uv run ziniao google-flow imagen-generate \
     -V prompt="..." -V model_name_type=GEM_PIX_2 -V fallback_model=NARWHAL \
     --save-images exports/out
   ```

   返回 JSON 里 `fallbackUsed: true, usedModel: "NARWHAL"` 可在编排层读取，判断是否触发了降级。

2. **跨端点手动切换**：`runImageFx`（Imagen）配额独立于 `batchGenerateImages`（Nano），改 `model_name_type=IMAGEN_3_5` 即可换池子。

3. **跨账号 / 跨日**：换 Chrome Profile（不同 Google 登录）或等 UTC 0:00 重置。

### 最小探测命令（消耗 1 次配额）

```bash
# 文生图 / IMAGEN_3_5 池（runImageFx，< 10s）
uv run ziniao google-flow imagen-generate -V prompt="dot" -V model_name_type=IMAGEN_3_5 -V candidates_count=1 --save-images exports/_probe_imagen

# Nano Banana 2 池（batchGenerateImages，纯文生图即可探测，~25s）
uv run ziniao google-flow imagen-generate -V prompt="dot" -V model_name_type=GEM_PIX_2 -V fallback_model="" --save-images exports/_probe_gem

# Nano Banana Pro 池（单张 40~90s，daemon auto 120s 足够）
uv run ziniao google-flow imagen-generate -V prompt="dot" -V model_name_type=NARWHAL -V fallback_model="" --save-images exports/_probe_pro
```

拿到 `ok:false status:429 reason:PUBLIC_ERROR_PER_MODEL_DAILY_QUOTA_REACHED` 即视为该模型池**当日耗尽**；用 `-V fallback_model=...` 自动转池，或手动切表中另一池继续工作。

### 其它疑似枚举（未实证，勿盲抄）

Flow / Labs 的 webpack bundle 里可能还出现 `IMAGEN_3_5_FAST`、`VEO_*`（视频）等 `*NameType`；本 skill **不收录**未在 `runImageFx` / `batchGenerateImages` 上实际回过 200 的值。若需扩展，请先用 `ziniao network list` 抓一次 UI 真实调用确认字段名，再 PR 回表。

## 画幅枚举（`aspect_ratio`）

- `IMAGE_ASPECT_RATIO_LANDSCAPE`（默认，16:9）
- `IMAGE_ASPECT_RATIO_PORTRAIT`（竖版）
- `IMAGE_ASPECT_RATIO_SQUARE`（正方）
- `IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE`（4:3）

## 技术细节

### reCAPTCHA Enterprise

`batchGenerateImages` 要求 reCAPTCHA Enterprise token：
- Site Key: `6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV`
- Action: `IMAGE_GENERATION`
- 从页面 `grecaptcha.enterprise.execute()` 获取
- Content-Type 使用 `text/plain;charset=UTF-8`（避免 CORS preflight）

### imageInputs 与多张生成矩阵

单个 request 的 `imageInputs` 支持多张参考图（subject / style / mood mix）：

```json
{
  "imageInputs": [
    { "imageInputType": "IMAGE_INPUT_TYPE_REFERENCE", "name": "<mediaId_1>" },
    { "imageInputType": "IMAGE_INPUT_TYPE_REFERENCE", "name": "<mediaId_2>" }
  ]
}
```

**每个 request 只返回 1 张图**；要一次出 N 张，请在 `requests[]` 放 N 个 item（不同 seed）。预设脚本已按此模式组装：M 张参考图 × N 次 count = N 张输出。

> 🚫 **不要**用 `candidatesCount` 字段（已实测返回 `Unknown name "candidatesCount"`）。
> ✅ 正确姿势：`requests[]` 多种子 + 每 item 相同 `imageInputs`。

`IMAGE_INPUT_TYPE_BASE_IMAGE` 用于基础图编辑场景（当前 CLI 默认均用 `REFERENCE`）。

### 项目管理

- 不指定 `project_id` 时自动通过 `project.createProject` tRPC 创建
- `uploadImage` 返回的 `mediaId` 自动传入 `batchGenerateImages`
- `projectId` 可跨次复用（在 Flow 页面也可看到对应项目）

## 排障

| 现象 | 处理 |
|------|------|
| reCAPTCHA 403 | 确认页面已加载 Flow（需要 `grecaptcha.enterprise` 可用）；刷新页面重试 |
| 终端卡死 / JSON 巨大 | 使用 `--save-images`；勿在无 `-o` 时用 `--json` 处理大 base64 |
| 上传失败 | 图 ≥ 约 64×64；单文件 ≤ 20MB（Google 侧限制） |
| `session` 无 token | 使用已登录 Profile 启动 Chrome 并打开 Flow |
| fifeUrl 下载失败 | URL 有效期约 6 小时；过期需重新生成 |
| `RESOURCE_EXHAUSTED` / `PUBLIC_ERROR_PER_MODEL_DAILY_QUOTA_REACHED` | 当前账号当日该模型配额耗尽；最快解法：`imagen-generate` 加 `-V fallback_model=NARWHAL`（或 `GEM_PIX_2`），preset 会自动换池重试；或手动改 `model_name_type` 切到 Imagen/另一 Nano |
| `reCAPTCHA evaluation failed` / `PUBLIC_ERROR_UNUSUAL_ACTIVITY` (403) | reCAPTCHA Enterprise token 被风控：常见原因是同一 token 复用、或页面 `grecaptcha` 久未交互。preset 内部已为每次 batch 请求申请新 token；若仍失败，刷新 `labs.google/fx/tools/flow` 页面后重试 |
| NARWHAL 超时 | 单张 p99 ≤ 120s（沿用 daemon auto）；`imagen-ref-generate` 单张走 preset 180s；多张 / 多参考图显式 `--timeout 300~480` |
| `Unknown name "candidatesCount"` | `batchGenerateImages` 不支持该字段；改用 `-V count=N` 由 preset 组装多个 requests |

## 合规

遵守 [Google 条款](https://policies.google.com/terms)；输出可能含 SynthID 水印。
