---
name: douyin-article-publish
description: 全流程抖音文章发布：大模型生成内容 + Google Flow 生成配图 + 自动发布到创作者平台。目标是发出值得被读完的作品，不是跑通流程。触发词：发布抖音、抖音发布、douyin publish、发抖音文章、抖音文章。
allowed-tools: Bash(ziniao:*), read, write, edit, exec
---

# 抖音文章发布

完整链路：**定主旨 → 写正文 → 做配图 → 装配 HTML → 本地校对 → 调 preset 发布**

Agent 负责 Phase 1–5（创意、内容、图文装配、校对），`ziniao douyin article-publish` 负责 Phase 6 的 UI 操作。

## 作品质量基准（先读这里）

**核心约束：我们在发作品，不是在发"占位内容"。** 做不到以下几条之前，不要进入 Phase 6 发布。

1. **文字有价值，不是填字数**。每一段都应回答一个具体问题、给出一个具体动作、或让读者产生一个具体感受；避免"总结式"、"小编我认为"、没有人物/动作的空泛情绪描述。
2. **标题不是列表题。** `5 招 / 3 个办法 / 10 个真相` 这类模板在抖音同质化严重，会被算法识别为低质。好标题通常 = **一个具体场景** + **一个反常识/共鸣点**。
3. **图文一体、视觉统一。** 全文图必须共享同一套画风、色温、笔触、时代感；头图是 hook，必须出现在正文里能被呼应的具象元素（人、动作、物件），不是泛"温馨感"。
4. **每段至少有一张图能呼应。** 抖音文章滑动节奏快，纯文字段落读完就划走；图是视觉锚点。图密度标准：`图数 ≥ 段数 / 2`（`build_html` 脚本会在 manifest 校验阶段直接卡住）。
5. **不将就。** NARWHAL 生成不满意就改 seed / 改 prompt 重生成，不要把"凑合能看"的图发出去。**宁少勿滥**——图质量差不如少一张。
6. **发布前必须本地预览**（Phase 5），确认一次整体观感，而不是信任 preset 返回值。

## 前置条件

**浏览器会话**：任选一种。ziniao 管理的是 session，不绑定固定端口。

- **方式 A · 由 ziniao 拉起 Chrome**（推荐，端口自动分配）

    ```bash
    ziniao launch --user-data-dir <profile 目录> --port 0 --name <会话名>
    ```

    - `--port 0` 让系统分配空闲端口
    - 用独立 profile，避免污染日常浏览器；首次使用需手动登录 `creator.douyin.com` 与 `labs.google`

- **方式 B · 连接已运行的 Chrome**

    ```bash
    ziniao connect <port> --name <会话名>
    ```

**当前会话切换**：`ziniao session list` 查；`ziniao session switch <id>` 长期切换；单次用 `ziniao --session <id> <cmd>`。后续命令全程不用再关心端口。

## Phase 1 · 选题与主旨

1. 根据用户输入定题；用户未指定时，挑**有具体场景**的选题（避免"成长 / 干货 / 生活方式"这种大而空的词）。
2. **一句话主旨**：在动笔前先写下来——"我要让读者读完这一篇后，得到/相信/打算做什么。"所有段落必须回答这一句。主旨不清晰就**先停下来重想**，不要硬凑。
3. 反例 vs 正例：
    - 反例：《3 个让你周末更舒服的小办法》（空泛）
    - 正例：《把闹钟往后拨两小时，是我今年做得最对的一件事》（具体场景 + 反常识 + 个人第一视角）

## Phase 2 · 正文

产出一份**结构化草稿**（纯文字先定形，不急着写 HTML）：

- **标题**：≤ 30 字，符合上面"作品质量基准 §2"。
- **正文 3–5 段**，每段 80–160 字，每段只承载一个核心点（一个场景、一个动作、一个观察）。
- **首段抓人**：用具体动作或具体数字开场，避免"在这个快节奏的时代…"式套话。
- **末段留余音**：一句可以被读者复述给朋友的话（金句、对比、反转或邀请）。
- **自查**：写完把每段第一句拎出来，独立读——能不能看懂大意？能→合格；不能→这段还没有聚焦。

## Phase 3 · 配图（视觉统一 + 每段呼应）

配图分三类（抖音会区分呈现）：

1. **正文头图（head）** —— 嵌在正文顶部，承担阅读开场。必须含**人物或动作或有情绪的物件**，不是纯风景/纯物件摆拍；画面要能被正文其中一段呼应（比如正文讲"把闹钟往后拨"，头图就该出现床头、闹钟、被拉上的窗帘之类）。推荐 16:9。
2. **推荐封面（cover）** —— 独立字段，抖音列表页/推荐流显示。**必须 3:4 竖图、分辨率 ≥ 1080×1440**，否则抖音会报 `封面分辨率过低`；可以是头图的竖版变体（同风格、同主体、重新构图一次），也可以直接复用 head_image 的源图由 `build_html.py` 自动中心裁剪成 3:4（源图长边 ≥ 1440 才够）。
3. **段内图（body）** —— 承担阅读节奏与记忆点。每张图锚定**其所在段的核心名词或动作**，不重复、不装饰、不凑数。

### 视觉统一

在 Phase 3 开始前，**先固定一个英文 style prefix**，后续所有图复用这条前缀不变：

```text
bright flat vector illustration style, warm vibrant colors, coherent palette of warm ochre, muted green and soft cream, clean minimal composition, no text, 16:9 aspect ratio
```

调色板、笔触、构图密度都收敛在这里。`bright flat vector` 可以换成 `soft watercolor / isometric 3d / retro printmaking / line-art with pastel fill` 等，一旦选定就**整篇统一**。

### 出图命令

```bash
ziniao --timeout 240 google-flow imagen-generate \
  -V prompt="<style prefix>, <scene description in English>" \
  -V model_name_type=NARWHAL \
  -V candidates_count=1 \
  --save-images <workdir>/raw/<name>
```

- 模型固定 `NARWHAL`（Nano Banana Pro），出图质感比默认 Imagen 更稳
- `--timeout 240` 给足裕量（实测单图 40–60s）
- `<workdir>` 是本次任务的专属工作目录，`raw/` 存放原图（未压缩，供后续重选/重试）

### prompt 写作要点

- **不是翻译中文占位，是重新描述画面**。中文提示词里的情绪词（"惬意、温暖、治愈"）在英文里要落到**具象元素**（`a half-drunk coffee / sunlight through sheer curtains / a lazy cat curled on a linen blanket`）。
- 包含：**主体物 + 环境 + 光线 + 情绪副词**（1–2 个），每项限 1 个短语，整体不超过 60 词。
- **重生成门槛要低**：构图奇怪、人脸变形、和正文意象对不上——立刻换 seed 或改 prompt 再生成，**不把凑合的留下**。

## Phase 4 · 装配 HTML（manifest 驱动）

由 skill 自带脚本 `scripts/build_html.py` 统一装配，**不要让 Agent 临时手写拼接脚本**。

### 产出 manifest.json

在 `<workdir>/manifest.json` 里声明本篇所有素材与排版顺序。这是**结构契约**，不是内容模板——字段语义和约束见下表，再结合本篇主题自由填写。

| 字段 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `title` | 是 | str | ≤30 字。超过会被抖音截断，脚本会报错。 |
| `style_prefix` | 否 | str | 仅作备忘，记录本篇 Google Flow 用的英文风格前缀；脚本不消费，但便于重跑/续写时保持视觉统一。 |
| `head_image.src` | 是 | path | 正文头图（嵌在正文顶部）。相对 manifest 目录解析，也可绝对路径。推荐 16:9。 |
| `head_image.alt` | 否 | str | 无障碍文本；留空也可以。 |
| `cover_image.src` | 否 | path | 推荐页封面源图。**缺省时 `build_html` 会从 `head_image.src` 中心裁成 3:4**，此时 head 源图的**长边必须 ≥1440**；否则请**单独出一张 3:4 竖图**（`aspect ratio 3:4` / `--aspect 3:4`）放这里。 |
| `blocks` | 是 | list | 按顺序就是抖音文章正文的排版顺序。每项要么 `{"type":"p","text":...}`，要么 `{"type":"img","src":...,"alt":...}`。段数 ≥1，非空段 ≥1；**图数 ≥ 段数/2**（脚本会直接卡住）。 |

最小可跑骨架（把中文占位替换成本篇真实内容，图按段配齐）：

```json
{
  "title": "<本篇标题，≤30字>",
  "style_prefix": "<Phase 3 定的英文风格前缀，单行>",
  "head_image": {
    "src": "raw/<head>.jpg",
    "alt": "<头图一句话描述>"
  },
  "cover_image": {
    "src": "raw/<cover-portrait>.jpg"
  },
  "blocks": [
    {"type": "p",   "text": "<第 1 段正文，80–160 字>"},
    {"type": "img", "src": "raw/<body-1>.jpg", "alt": "<呼应第 1 段的视觉锚点>"},
    {"type": "p",   "text": "<第 2 段>"},
    {"type": "img", "src": "raw/<body-2>.jpg", "alt": "<呼应第 2 段>"},
    {"type": "p",   "text": "<结尾段，一句可被复述的话>"}
  ]
}
```

写法约束（脚本会强制，违反直接退出）：

- `src` 相对 manifest 所在目录解析；也支持绝对路径。文件必须真的存在。
- `blocks` 里 `p`/`img` 顺序自由，但最终顺序 = 抖音正文的顺序——段落和图要**贴合**（图紧跟呼应它的段落，不是一股脑堆在末尾）。
- **图密度硬门槛**：`count(img) >= ceil(count(p) / 2)`。纯文案流的抖音文章留存极差，这条是质量兜底。
- 不要在 `blocks` 里重复放 `head_image.src`；头图由 preset 独立上传到编辑器顶部，重复放正文里会出现两遍。
- 文件名里尽量包含段落语义（`body-wakeup-0.jpg` 比 `body-1.jpg` 半年后重看更友好），但不是强制。

### 跑装配

```bash
python <skill-dir>/scripts/build_html.py <workdir>/manifest.json
```

`<skill-dir>` 固定为 `C:\Users\Administrator\.ziniao\repos\site-hub\douyin\skills\douyin-article-publish`（ziniao 安装后 skill 会同步到这里；在本仓库内开发时也可直接指向 `site-hub/douyin/skills/douyin-article-publish`）。

脚本自动产出到 `<workdir>/build/`：

- `title.txt`     —— UTF-8 无 BOM
- `head.jpg`      —— 正文头图，缩放到 640×360 / JPEG q=75
- `cover.jpg`     —— 推荐封面，中心裁剪到 1080×1440 / JPEG q=90
- `content.html`  —— 正文图已 base64 内联
- `preview.html`  —— 本地浏览器可打开的排版预览

若 cover 源图分辨率低于 1080×1440，脚本会打印 warning，这时请换一张更大的源图重跑 —— 否则抖音会拒绝封面。

脚本末尾会直接打印出 Phase 6 的发布命令，可以复制粘贴。

## Phase 5 · 本地预览校对（必做）

```powershell
start <workdir>\build\preview.html
```

用浏览器打开后自查四件事：

1. **标题** 够不够吸引——把它拎出来单独念一遍，不吸引就回 Phase 2 改
2. **头图** 一眼能不能看懂在讲什么，构图有没有硬伤
3. **每段首句** 能不能独立成立（用 `Ctrl+F` 跳过图看纯文字）
4. **图文走位**：图是紧跟那段、还是跑偏了——跑偏就调 manifest 顺序

预览不满意，回 Phase 2 / 3 / 4 对应阶段返工。不要带着"差不多"的感觉进入 Phase 6。

## Phase 6 · 调用 preset 发布

```bash
ziniao --timeout 300 douyin article-publish \
  -V title=@file:<workdir>\build\title.txt \
  -V content_html=@file:<workdir>\build\content.html \
  -V head_image="<workdir>\build\head.jpg" \
  -V cover_image="<workdir>\build\cover.jpg"
```

preset 内部编排（`~/.ziniao/repos/site-hub/douyin/article-publish.json`）：

1. 导航到文章编辑页 → `clear-overlay` 清除遮罩
2. `upload-react` 通过 CDP `FileChooserOpened` 上传**正文头图**（`addIcon[0]`）
3. `inject-vars` 注入 flow_vars → `eval` React setter 填标题 → tiptap API 插正文 HTML
4. `eval await_promise` 轮询所有 `<img>` 从 blob 换成 CDN（最多 ~120s）
5. `eval` 标记第二个 `addIcon` → `upload-react` 上传**推荐封面**（3:4 竖图）
6. `wait` 等 `.semi-modal-body` 出现 → `eval` 点 modal 里的「确定」完成裁剪
7. `eval await_promise` 轮询 modal 关闭
8. `eval` 滚到底部 → 点「发布」
9. `eval await_promise` 轮询 URL 是否跳到 `/content/manage`（或 toast 出现"发布成功"）

**参数硬规则**：

- `content_html` 和 `title` 必须走 `@file:` —— 直接传字符串会被 PowerShell 截断或在 CJK 场景下编码出错
- `head_image` / `cover_image` 传**本地磁盘路径**，不是 base64 或 data URI
- `cover_image` 必须 **3:4 竖图且 ≥1080×1440**，不符合抖音会拒绝（`build_html.py` 会统一到这个规格）

## Phase 7 · 发布后验证

1. **preset 返回值**：所有步骤 `ok: true` 且 `failures: []`；特别关注 `wait_publish_result.result` —— JSON 里 `ok: true` 且 `reason` 为 `url_changed` 或 `toast` 才算真正发布成功。若 `reason: toast_error`，**必须**读 `toast` 字段诊断（常见：`没有选择封面`、`封面分辨率过低`、`正文内容不能少于100字`）。
2. **后台确认**：访问 <https://creator.douyin.com/creator-micro/content/manage?default_tab=article>，在「全部作品」或「审核中」里**按标题搜一遍**（注意抖音列表可能有缓存，刷新或切 tab）。
3. **找不到怎么办**：
    - 若 `wait_publish_result` 报 `toast_error`，按 toast 文案回 Phase 3/4 修素材
    - 若 URL 已跳到 manage 但列表搜不到，可能是正文或标题触发了敏感词 / 版权审核被平台静默拦下；或后台索引延迟（≥ 5 分钟再刷新）

## 技术细节

### 上传机制

CDP `Page.setInterceptFileChooserDialog` 拦截 → nodriver `elem.click()` 触发真实鼠标事件（命中 React `onClick`）→ `FileChooserOpened` 事件 → `DOM.setFileInputFiles(backendNodeId=…)`。**不**走 `createElement` hook 或 `DataTransfer`（React 不会响应）。

### 变量二次注入

抖音 SPA 在上传/裁剪后会重建 React fiber 树，`window.__flow_vars` 可能被清掉。`inject-vars` 动作从 preset 持有的 `flow_vars` 重新注入；超过 50 KB 的值（如 `content_html`）单独注入以避免 CDP eval 超时。

### 正文插入

通过 React fiber 定位 tiptap editor 实例，依次调 `editor.commands.clearContent()` + `editor.commands.insertContent(html)`。

## 故障排查

| 现象 | 可能原因 | 处置 |
| --- | --- | --- |
| CLI 侧 `ConnectionResetError` / 120s 无响应 | daemon 事件循环被阻塞（通常是日志放大） | 见下文「日志位置与调级」，确认 `logging_setup` 生效 |
| `mcp_debug.log` / `daemon.log` 飞速增长 | 有代码路径绕过了 `logging_setup` | `uv tool install --reinstall --from <repo> ziniao` 重装本地源码 |
| imagen-generate 超时 | NARWHAL 单图 >120s | `--timeout 240`（或更高） |
| manifest 校验失败：图密度偏低 | 段数过多或图过少 | 补图或合并/删段，满足 `img ≥ p/2` |
| 发布按钮 disabled | 头图未成功上传 / 正文为空 / 封面未设置 | 看 daemon.log 里 `upload-react` 是否出现 `FileChooserOpened` |
| 图片在正文里是裂图 | base64 含换行或未 URL-safe | 检查 `build_html.py` 输出；通常不会出现，因为脚本用 `b64encode(...).decode("ascii")` |
| `wait_publish_result` 报 toast `没有选择封面` | 封面未上传 / 封面 modal 未点「确定」 | 检查 preset 的 `upload_cover` / `confirm_cover_crop` 步骤；也可能抖音改了 modal 的 className（搜索 `.semi-modal-body`） |
| `封面分辨率过低，请重新上传` | cover 源图 < 1080×1440 | 换更高分辨率源图重跑 `build_html.py`；脚本本身不会放大到 1080×1440 以上 |
| 所有步骤 ok、toast 显示"发布成功"，但管理页搜不到 | 内容触发平台静默审核；或后台索引延迟 | 手动打开编辑页 F12 看 publish XHR 的响应；等 ≥5 分钟再刷新 |

**日志位置与调级**：

- `~/.ziniao/mcp_debug.log`：MCP server（Cursor 里的 `ziniao serve` 进程）
- `~/.ziniao/daemon.log`：daemon 进程
- 均走 `RotatingFileHandler`（默认 20 MB × 3 份），根级别 WARNING（应用自身 INFO），nodriver / websockets 强制 ERROR
- 需要更细日志时临时 `$env:ZINIAO_LOG_LEVEL="DEBUG"` 再复现

## 目录约定

一次发布任务建议的工作目录布局：

```text
<workdir>/
├── manifest.json        # 由 Agent 产出，描述整篇
├── raw/                 # Google Flow 原图落盘（供重选/重试）
│   ├── head-0-fifeUrl.jpg
│   ├── cover-portrait-0-fifeUrl.jpg   # 可选；缺省由 head 自动裁切
│   ├── body-sleep-0-fifeUrl.jpg
│   └── ...
└── build/               # build_html.py 的产物（Phase 4 自动生成）
    ├── title.txt
    ├── head.jpg         # 640×360 / 正文头图
    ├── cover.jpg        # 1080×1440 / 推荐封面
    ├── content.html
    └── preview.html
```

`<workdir>` 可以是任意可写路径（`%TEMP%\douyin-<timestamp>` / 项目 cwd 下子目录等），本 skill 不做约束。
