# flow-demo — Declarative UI Flows showcase

Two end-to-end presets that exercise every `mode: ui` capability in `ziniao` against a free, public practice site ([quotes.toscrape.com](http://quotes.toscrape.com/)). Use them as copy-paste starters when you need to build a UI-first adapter.

| Preset | Features exercised |
|--------|--------------------|
| [`quotes-scrape.json`](quotes-scrape.json) | `navigate` → `wait` → `extract` (text / attribute / eval / querySelectorAll) → `output_contract` |
| [`login-and-extract.json`](login-and-extract.json) | `fill` → `click` → `wait` → `extract` + `type: secret` (env source) + full-chain masking |

Background and schema reference: [`docs/site-ui-flows.md`](../../docs/site-ui-flows.md).

## Prerequisites

1. `ziniao site repo add` this repo (or run from the main project where `site-hub/` is auto-scanned).
2. Chrome / 紫鸟会话已打开 — `ziniao --session <id> session info` 确认。

## Run: quotes-scrape

```bash
ziniao flow-demo quotes-scrape
ziniao flow-demo quotes-scrape -V tag=love
ziniao --json flow-demo quotes-scrape -V tag=inspirational
```

Expected output (`--json`, trimmed):

```jsonc
{
  "ok": true,
  "extracted": {
    "page_title": "Quotes to Scrape",
    "quotes": [
      { "text": "...", "author": "Jane Austen", "tags": ["aliteracy", "books"] },
      ...
    ],
    "next_href": "/tag/humor/page/2/"
  },
  "output": {
    "tag": "humor",
    "title": "Quotes to Scrape",
    "quotes": [...],
    "next": "/tag/humor/page/2/"
  }
}
```

## Run: login-and-extract

```bash
# PowerShell
$env:ZINIAO_DEMO_PWD = "admin"
ziniao flow-demo login-and-extract

# bash / zsh
export ZINIAO_DEMO_PWD=admin
ziniao flow-demo login-and-extract
```

**Verify masking**: temporarily break a selector (e.g. change `input#username` → `input#wrong`) and re-run. The generated `exports/flow-errors/*.err.txt` / snapshot must never contain the plaintext password — only `***`. The validator additionally **rejects** any preset that references a `secret` var in a URL / selector / script field.

## What the presets illustrate

- **`extract.kind: eval`** — arbitrary JS returning structured objects, stored in `extracted[<as>]`.
- **`extract.kind: attribute`** — grabs `href` from `li.next a`.
- **`extract.kind: querySelectorAll`** — array of quote authors.
- **Step 间引用** — `output_contract` maps the final shape using `$.extracted.*` and `$.vars.*` paths.
- **失败 artefacts** — any failure writes `exports/flow-errors/<stamp>-<step_id>.{png,html,err.txt}`; the paths appear in `result.failures[i]` for agent self-healing.
- **`type: secret` 全链脱敏** — resolved secret values are collected into `spec._ziniao_secret_values` and replaced with `***` in every log / error / artefact line before being emitted.
