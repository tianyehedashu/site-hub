---
name: site-development
description: Build new site adapters (presets + plugins) for the ziniao site system. Use when the user needs to create a new site, add presets for a website, reverse-engineer a logged-in API, or write a SitePlugin. Triggers include "new site", "add preset", "site adapter", "API template", "site plugin", "site development", or any request to extend ziniao's site preset library.
allowed-tools: Bash(ziniao:*)
---

# Site Adapter Development Guide

Build site adapters for ziniao: JSON presets for declarative API calls, optional Python plugins for complex logic, and SKILL.md for agent discovery.

## Architecture Overview

```
site-hub/
└── <site-name>/              ← kebab-case site ID (e.g. rakuten, amazon-jp)
    ├── __init__.py            ← Optional SitePlugin (complex auth, dynamic URLs)
    ├── <action>.json          ← Preset templates (one per API endpoint)
    └── skills/                ← Agent skills (agentskills.io spec)
        └── <site>-<topic>/    ← kebab-case skill name
            └── SKILL.md       ← Agent-facing documentation
```

Discovery priority: user-local (`~/.ziniao/sites/`) → repos (`~/.ziniao/repos/`) → entry_points → builtin (`ziniao_mcp/sites/`).

## Core Workflow

```
Step 1: Reverse-engineer the API (browser DevTools + ziniao network)
Step 2: Choose the tier (fetch / header_inject / mode:js / plugin)
Step 3: Write the preset JSON  (fetch OR mode:js with script)
Step 4: Write the plugin (only for Tier 4 signature/state-machine cases)
Step 5: Test with ziniao CLI
Step 6: Add skills/ and commit to site-hub
```

For Next.js / RSC apps, skim *[Reversing Next.js / RSC Apps — Quick Checklist](#reversing-nextjs--rsc-apps--quick-checklist)* in Step 2b before Step 1 — it tells RSC / tRPC / Route Handler / 3rd-party REST apart and picks which to target.

## Step 1: Reverse-Engineer the API

### 1.1 Capture Network Traffic

Open the target site in a browser tab and use ziniao to capture requests:

```bash
# Connect to browser
ziniao launch --url "https://target-site.com"

# Navigate to the page that triggers the API
ziniao navigate "https://target-site.com/dashboard"
ziniao wait "body"

# Enable network monitoring and trigger the action
ziniao network list --clear
# ... perform the action in browser ...
ziniao network list --filter "api.target-site.com" --json
```

Or use `fetch-save` to auto-generate a preset from a captured request:

```bash
ziniao network list --clear
# ... trigger the API in browser ...
ziniao network fetch-save --filter "api/endpoint" -o preset.json
```

### 1.2 Identify Key Fields

From the captured request, note:

| Field | What to Look For |
|-------|------------------|
| `url` | Full API endpoint URL |
| `method` | GET or POST |
| `requestHeaders` | Auth headers (Cookie, Bearer, CSRF, custom signatures) |
| `requestBody` | POST payload structure and format (JSON vs form-encoded) |
| `responseBody` | Response data structure for pagination fields |

### 1.3 Determine Auth Complexity

| Observed Headers | Auth Type | Tier |
|----------------|-----------|------|
| Only Cookie (no special headers) | `cookie` | **Tier 1** — `mode: fetch` preset |
| CSRF token in Cookie + header | `xsrf` | **Tier 2** — `mode: fetch` + `header_inject` |
| Bearer / custom token from page state | `token` | **Tier 2** — `mode: fetch` + `header_inject` (source: eval) |
| Multi-step: session → project → upload → generate | — | **Tier 3** — `mode: js` (see *Step 2b*) |
| reCAPTCHA Enterprise token required per call | — | **Tier 3** — `mode: js` calling `grecaptcha.enterprise.execute` (see *Step 2b*) |
| No public API — UI-only (login / export button / 2FA / form fill / DOM scrape / hybrid UI→API) | — | **Tier 2.5** — `mode: ui` (see *Step 2c*) |
| Complex signatures (X-s, X-t, etc.) / state machine | — | **Tier 4** — Python `SitePlugin` (see *Step 3*) |
| No auth needed | `none` | **Tier 1** — `mode: fetch` preset |

Quick test for Tier 1 feasibility:

```bash
ziniao eval --await "fetch('/api/endpoint', {credentials:'include'}).then(r => r.json())"
```

If this returns valid data → Tier 1.

## Step 2: Write the Preset JSON

### Minimal Preset (Tier 1 — Cookie Only)

```json
{
  "name": "Site·Action Name",
  "description": "What this preset does; shown in `ziniao site list`.",
  "auth": { "type": "cookie", "hint": "Login to target-site.com first" },
  "navigate_url": "https://target-site.com/page",
  "mode": "fetch",
  "url": "https://api.target-site.com/v1/endpoint",
  "method": "GET",
  "headers": {
    "Accept": "application/json"
  },
  "vars": {
    "start_date": {
      "type": "str",
      "required": true,
      "description": "Start date (YYYY-MM-DD)",
      "example": "2026-01-01"
    },
    "page": {
      "type": "int",
      "default": 1,
      "description": "Page number"
    }
  }
}
```

### Preset with CSRF Token (Tier 2)

Add `header_inject` to dynamically read tokens at request time:

```json
{
  "auth": { "type": "xsrf", "hint": "Login to RMS first" },
  "header_inject": [
    { "header": "X-XSRF-TOKEN", "source": "cookie", "key": "XSRF-TOKEN" }
  ]
}
```

`header_inject` source types:

| Source | How It Reads | Use Case |
|--------|-------------|----------|
| `cookie` | `document.cookie` regex match | XSRF/CSRF tokens |
| `localStorage` | `localStorage.getItem(key)` | SPA JWT storage |
| `sessionStorage` | `sessionStorage.getItem(key)` | Temporary session tokens |
| `eval` | `eval(expression)` | meta tags, global variables, DOM attributes |

`transform` field: optional value template with `${value}` placeholder (e.g. `"Bearer ${value}"`).

### Preset with Pagination

```json
{
  "pagination": {
    "type": "body_field",
    "page_field": "page",
    "total_field": "data.totalPage",
    "start": 1,
    "max_pages": 500,
    "merge_items_field": "data.items"
  }
}
```

This enables `--page N` and `--all` on the CLI. `merge_items_field` specifies the JSON path to the array that gets concatenated across pages.

### Preset with Encoding Conversion

For sites returning non-UTF-8 responses (e.g. Japanese Shift_JIS CSV):

```json
{
  "output_decode_encoding": "cp932"
}
```

This auto-decodes the response when using `-o file.csv`.

### Full Preset with POST Body

```json
{
  "name": "Site·Report Search",
  "description": "Paginated report search API",
  "auth": { "type": "xsrf" },
  "navigate_url": "https://target-site.com/reports",
  "pagination": {
    "type": "body_field",
    "page_field": "page",
    "total_field": "data.totalPages",
    "start": 1,
    "merge_items_field": "data.records"
  },
  "mode": "fetch",
  "url": "https://api.target-site.com/reports/search",
  "method": "POST",
  "headers": {
    "Accept": "application/json",
    "Content-Type": "application/json"
  },
  "header_inject": [
    { "header": "X-XSRF-TOKEN", "source": "cookie", "key": "XSRF-TOKEN" }
  ],
  "vars": {
    "start_date": {
      "type": "str",
      "required": true,
      "description": "Start date (YYYY-MM-DD)"
    },
    "end_date": {
      "type": "str",
      "required": true,
      "description": "End date (YYYY-MM-DD)"
    },
    "page": {
      "type": "int",
      "default": 1,
      "description": "Page number"
    }
  },
  "body": {
    "page": "{{page}}",
    "startDate": "{{start_date}}",
    "endDate": "{{end_date}}"
  }
}
```

Variables are rendered via `{{var_name}}` substitution in `url`, `body`, and `headers` values.

### Variable Types

Besides `str` / `int` / `float` / `bool`, ziniao supports two file-oriented types that auto-resolve to base64 via the daemon (bypassing the ~1 MB TCP message cap through `@@ZFILE@@` / `@@ZURL@@` file refs):

| Type | Accepts | Rendered Value | Use Case |
|------|---------|----------------|----------|
| `file` | local path / `http(s)://` / base64 / data URL | base64 string (via file ref) | Single reference image / document upload |
| `file_list` | comma-separated list of the above | JSON array of base64 strings | Multi-reference image inputs |

```json
"vars": {
  "image": {
    "type": "file",
    "required": false,
    "description": "Reference image: local path, URL or base64."
  },
  "images": {
    "type": "file_list",
    "default": "",
    "description": "Multi references (comma-separated): a.png,b.png,https://x/y.jpg"
  }
}
```

Inside the preset body (or a `mode: js` script), the rendered value is already a plain base64 string (or an array of them) ready to embed in API payloads.

## Step 2b: `mode: js` for Multi-Step Flows

Use `mode: js` when a single API call is not enough — e.g. upload → create project → reCAPTCHA → generate → poll. The `script` field is a JavaScript source string executed in the page context (with cookies, `grecaptcha`, etc. available). It MUST return a JSON-serialisable value.

```json
{
  "name": "Site·Generate With References",
  "mode": "js",
  "navigate_url": "https://target-site.com/app",
  "vars": {
    "prompt":  { "type": "str",       "required": true },
    "images":  { "type": "file_list", "default": "" },
    "count":   { "type": "int",       "default": 1 }
  },
  "body": {
    "prompt":  "{{prompt}}",
    "images":  "{{images}}",
    "count":   "{{count}}"
  },
  "script": "(async () => { const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__; /* ... multi-step logic using b.prompt / b.images / b.count ... */ return { images: outputs }; })()"
}
```

Key rules:

- The **rendered `body`** is injected into the script as a pre-declared global called **`__BODY__`** (a JSON string); parse it once at the top of the script (`const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__;`). There is **no** `{{body}}` placeholder — `{{var_name}}` substitution only applies to values inside `url` / `body` / `headers` / `script` fields themselves.
- All `{{var_name}}` substitution happens **before** the JS is evaluated; never rely on `{{var}}` syntax inside strings the browser will forward back.
- For large base64 inputs, prefer `type: file` / `file_list` — the daemon resolves `@@ZFILE@@` / `@@ZURL@@` refs server-side, so the rendered `body` already contains plain base64 when the script unpacks `__BODY__`.
- Timeouts: `page_fetch` auto-upgrades to 120 s via `_SLOW_COMMANDS`. If a single call is expected to exceed that (slow models, `count >= 2`, large uploads), pass `--timeout 300` explicitly on the CLI.

## Step 2c: `mode: ui` for UI-Only Flows (Tier 2.5)

Use `mode: ui` when the site has **no public API** (or you need to stitch login + form fill + export button) — everything that historically forced you into fragile ad-hoc scripts. The preset declares `steps[]`; each step is an ordered UI action that reuses the same primitives agents can call directly. Full whitelist (see [docs/site-ui-flows.md §3.2](../../../docs/site-ui-flows.md)):

- **Interaction**: `click`, `fill`, `type_text`, `insert_text` (CDP `Input.insertText`, Slate/ProseMirror), `press_key`, `hover`, `dblclick`, `upload`, `upload-hijack` (SPA 隐藏 input), `upload-react` (React/SPA via CDP `setInterceptFileChooserDialog`)
- **Navigation / waits**: `navigate`, `wait`
- **DOM utilities**: `clear-overlay` (主动清弹窗/遮罩，`click` 与 `upload-hijack` 内部已自动先跑), `screenshot`, `snapshot`
- **Scripting**: `eval` (返回值存入 `step.value`), `extract` (`kind: text | html | attribute | querySelectorAll | table | eval`), `fetch` (inline HTTP，带浏览器 cookie)
- **Flow glue**: `inject-file` (读取本地文本写入 `window[var]`，喂大 HTML/JSON 给后续 `eval`), `inject-vars` (SPA 上下文重置后重新注入 `window.__flow_vars`；`_flow_run` 启动已自动跑一次，大值 ≥50KB 会单独注入)

```jsonc
{
  "name": "Example · UI Export",
  "mode": "ui",
  "navigate_url": "https://site.com/dashboard",
  "vars": {
    "start_date": { "type": "str",    "required": true },
    "password":   { "type": "secret", "source": "keyring:myapp:admin", "required": true }
  },
  "steps": [
    { "id": "pw",     "action": "fill",     "selector": "#pw",            "value": "{{password}}" },
    { "id": "submit", "action": "click",    "selector": "button[type=submit]" },
    { "id": "wait",   "action": "wait",     "selector": "a.download",     "timeout": 30 },
    { "id": "grab",   "action": "extract",  "as": "download_url",
      "selector": "a.download", "kind": "attribute", "attr": "href" },
    { "id": "dl",     "action": "fetch",    "method": "GET",
      "url": "{{extracted.download_url}}",  "save_body_to": "exports/report.csv" }
  ],
  "output_contract": {
    "download_url": "$.extracted.download_url",
    "file":         "$.steps.dl.saved_path"
  }
}
```

Key rules:

- **Step-to-step data flow**: `{{steps.<id>.value}}`, `{{steps.<id>.saved_path}}`, `{{extracted.<as>}}` are rendered **per step** (after variable rendering). This unlocks hybrid flows: UI click → DOM extract → inline `fetch` continues with the extracted URL / token.
- **`action: extract`** supports `kind: text | html | attribute | querySelectorAll | table | eval`; result lands in `extracted[<as>]`. `as` is required.
- **`action: fetch`** runs inside the browser context (cookies available), mirroring `mode: fetch` semantics — use `save_body_to` to persist binary bodies straight to disk.
- **`type: secret` variables** (keyring / env / interactive stdin) are fully redacted from failure artefacts and logs; the validator **rejects** presets that reference a secret var outside `fill.value`, `type_text.text`, `insert_text.text`, `fetch.body`, `fetch.headers` (no secrets in URLs, selectors, scripts).
- **Failure artefacts**: first hard failure writes `exports/flow-errors/<stamp>-<step_id>.{png,html,err.txt}` and returns `{ok: false, failures: [...]}`. Pass `step.continue_on_error=true` to let the flow soldier on.
- **Timeouts**: `flow_run` auto-upgrades to 120 s; pass `--timeout 300` (or longer) for multi-step flows with heavy UI waits.

Full reference (schema, all `extract` kinds, secret sources, artefact shape): [docs/site-ui-flows.md](../../../docs/site-ui-flows.md).

> **Rule of thumb**: if the site has a stable API, use Tier 1 / 2 / 3. Reach for `mode: ui` **only** when UI is the contract — it is slower, noisier, and more fragile.

### CORS Bypass for Third-Party Backends

Many Next.js / SPA apps call a separate API origin (e.g. `aisandbox-pa.googleapis.com`). A browser-side `fetch` with `Content-Type: application/json` triggers a CORS preflight that the backend often rejects. Two proven workarounds:

1. **Content-Type downgrade (preferred for JSON POSTs):** send JSON with `Content-Type: text/plain;charset=UTF-8`. Most REST backends still parse the body as JSON, and this avoids the preflight entirely.
2. **Reuse same-origin tRPC / Route Handlers**: if the Next.js app exposes an equivalent tRPC procedure (e.g. `project.createProject`), call it via `/api/trpc/...` on the primary origin — same-origin, no preflight.

### Reversing Next.js / RSC Apps — Quick Checklist

Before Step 1 on any Next.js / RSC app, confirm **which API type** the UI actually hits (each has a different reversing strategy):

| API Type | Signal in DevTools | Ziniao Mode |
|---------|---------------------|-------------|
| RSC payload | `?_rsc=...` with `text/x-component` body | Avoid — no stable schema |
| tRPC | `/api/trpc/<procedure>` with `input=` / batch JSON | `mode: fetch` (same-origin) |
| Route Handler | `/api/*` returning JSON | `mode: fetch` |
| 3rd-party REST | different origin (e.g. `*.googleapis.com`) | `mode: fetch` or `mode: js` + CORS bypass |

Reversing workflow (five steps):

1. **HAR capture** the full UI interaction with DevTools → save → grep for your action's keyword.
2. **Identify auth surface** — which cookie / bearer / anti-CSRF token gates the call.
3. **Drill layers** — an RSC payload almost always wraps an underlying tRPC or REST call; chase down the non-RSC one.
4. **Pick a CORS-safe entry** — prefer same-origin tRPC / Route Handler; otherwise use `Content-Type: text/plain;charset=UTF-8`.
5. **Extract constants from webpack bundles** (`site key`, `action` strings, enum names) by searching the chunked JS with the token you saw in HAR.

### Media Output — Declaring a Save Contract

`--save-images <prefix>` persists media produced by your preset. **The core framework knows no site-specific field names** (`encodedImage` / `fifeUrl` / `artifacts` / `b64_json` / …) — each site declares its own contract via one of three tiers:

#### Tier A — Declarative JSON (zero Python, covers 80% of sites)

Add a top-level `media_contract` list to your preset JSON. Two rule shapes, mix freely:

| Rule | Use For |
|------|---------|
| `{"items_at": "<dotted>", "fields": [{"key": "...", "source": "base64"|"url"}, …], "stem_suffix": "..."}` | Iterate a list and extract one or more media fields per element |
| `{"at": "<dotted>", "source": "base64"|"url", "stem_suffix": "-logo"}` | Pick one specific field anywhere in the response |

- **Dotted paths** walk dict keys *and* numeric list indices: `data.pages.0.items` resolves `result["data"]["pages"][0]["items"]`. Negative indices (`arr.-1.url`) are accepted.
- **`stem_suffix`** supports `{idx}` (list index) and `{field}` (field key) placeholders. Omit it to get safe defaults:
  - Single-field list rule → `-{idx}` → `prefix-0.jpg`, `prefix-1.jpg`
  - Multi-field list rule → `-{idx}-{field}` → `prefix-0-encodedImage.png`, `prefix-0-fifeUrl.jpg`
- **Collision guard**: a multi-field rule with a user-supplied `stem_suffix` that lacks `{field}` is **rejected** at compile time (`ValueError("…collide…")`). The framework refuses to silently overwrite files.
- **Silent skips**: rules whose dotted path doesn't resolve, whose fields are missing, or whose `url` source value doesn't start with `http(s)://` are dropped quietly — one bad entry in a long contract won't break the whole `--save-images` run.

Example (Google Flow's `imagen-generate` returning both inline base64 and signed CDN URLs):

```jsonc
{
  "mode": "js",
  "script": "...",
  "media_contract": [
    {
      "items_at": "images",
      "fields": [
        { "key": "encodedImage", "source": "base64" },
        { "key": "fifeUrl",      "source": "url" }
      ]
    }
  ]
}
```

A site returning a single top-level logo + a nested thumbnail list:

```jsonc
{
  "media_contract": [
    { "at": "logo_url", "source": "url", "stem_suffix": "-logo" },
    {
      "items_at": "data.thumbnails",
      "fields": [{ "key": "b64", "source": "base64" }]
    }
  ]
}
```

#### Tier B — Python Plugin Override

When you need runtime logic the declarative form can't express (conditional on status codes, computed file names, synthesising items from multiple response branches), override `SitePlugin.media_contract(result, spec)`:

```python
class MySitePlugin(SitePlugin):
    site_id = "my-site"

    def media_contract(self, result: dict, spec: dict) -> list[dict]:
        if result.get("status") != "ready":
            return []
        return [{
            "source":       "url",
            "value":        result["signed_url"],
            "stem_suffix":  "-result",
            "path":         ["signed_url"],
        }]
```

Each **save item** is a 4-key dict:

| Key | Meaning |
|-----|---------|
| `source` | `"base64"` or `"url"` |
| `value` | the base64 payload or the URL |
| `stem_suffix` | appended to `--save-images <prefix>` |
| `path` | dict keys / list indices pointing back into *result*; patched with `"[saved: <filename>]"` after write so the printed JSON stays compact |

#### Tier C — Do Nothing

The default `SitePlugin.media_contract` returns `[]` when the preset has no `media_contract` block **and** no subclass overrides the method. Use when your preset returns no media — `--save-images` becomes a no-op (not an error).

#### Reusing atomic helpers elsewhere

If you persist bytes from inside a plugin's `after_fetch`, a `mode: js` post-processor, or a `mode: ui` step, import the atomic primitives directly from `ziniao_mcp.sites.save_media` instead of duplicating extension detection:

- `save_base64_as_file(b64, "exports/<site>/<name>")` → decodes + writes, extension auto-detected from magic bytes (`.png` / `.pdf` / `.zip` / `.bin` / …).
- `download_url_to_file(url, "exports/<site>/<name>")` → HTTP GET + writes, extension from Content-Type → magic fallback; pass `headers=` for auth if the URL isn't pre-signed.
- `apply_media_contract(result, items, prefix)` → the orchestrator the CLI uses; call it manually if you want contract-driven saves outside `--save-images` (e.g. from a scheduled job).

Both atomic functions return the actual `Path` written (or `None` on failure) and create the parent directory as needed — treat them as the canonical way to persist bytes so exports stay consistent across sites.

## Response Output Contract

The *non-media* sibling of `media_contract`: most JSON APIs wrap real data in an envelope like `{"status": "SUCCESS", "data": {...}}`. Instead of writing a Python `after_fetch` that just calls `json.loads(body)` and copies `data` to the top level, declare it in the preset JSON — the same three tiers as media:

#### Tier A — Declarative (recommended for JSON envelopes)

Add a top-level `response_contract` block:

```jsonc
{
  // ...,
  "response_contract": {
    "parse": "json",
    "lift": [
      { "from": "data",     "to": "parsed",   "when_eq": { "status": "SUCCESS" } },
      { "from": "meta.trace", "to": "trace_id" }
    ]
  }
}
```

Semantics:

- `parse`: currently only `"json"`. Non-matching / missing → contract is a no-op.
- `lift[].from`: dotted path into the parsed tree (same syntax as `media_contract`, supports list indices like `pages.0.url`).
- `lift[].to`: flat top-level key on the response dict (nested paths like `a.b` are rejected by design).
- `lift[].when_eq`: optional `{path: literal}` — *all* paths must equal the expected literal for the rule to run (AND). Omit to apply unconditionally.
- Any single rule that fails (missing path, JSON decode error, `when_eq` miss) is **silently skipped** — a partial response never crashes the CLI.

#### Tier B — Python override

When you need regex, numeric comparison, boolean OR, async enrichment, or anything else the declarative form can't express, override `SitePlugin.after_fetch(response, spec)`. Call `super().after_fetch(response, spec)` first if you still want the preset's declarative rules to run:

```python
class MyPlugin(SitePlugin):
    def after_fetch(self, response: dict, spec: dict) -> dict:
        super().after_fetch(response, spec)  # apply any declarative rules first
        body = response.get("body", "")
        if body and "<CRITICAL>" in body:
            response["alert"] = True
        return response
```

#### Tier C — Do Nothing

Omit the block entirely and don't override `after_fetch`. The default implementation is a no-op on the response, which is correct for presets that either don't return JSON at all (CSV, binary) or whose consumers already work on `response["body"]` directly.

## Step 3: Write the Plugin (Tier 4)

Only needed when declarative presets can't handle the logic (dynamic URL construction, complex auth signatures, response parsing). Most sites only need JSON presets.

Create `<site>/__init__.py`:

```python
"""Site plugin for <site-name>.

Loaded by ziniao_mcp.sites.get_plugin() from the repo directory.
Uses absolute import because this file lives outside the ziniao_mcp package.
"""

from __future__ import annotations
from ziniao_mcp.sites._base import SitePlugin


class MySitePlugin(SitePlugin):
    site_id = "my-site"

    def before_fetch(self, request: dict, *, tab=None, store=None) -> dict:
        # Modify request before it's sent to the browser.
        # Use cases: dynamic URL construction, timestamp computation,
        # reading custom variables from request["_ziniao_merged_vars"]
        return request

    def after_fetch(self, response: dict, spec: dict) -> dict:
        # Post-process the raw response.
        # response has: status, statusText, body (raw text); spec is the rendered preset.
        # For simple JSON parse + lift, prefer a declarative `response_contract`
        # block in the preset JSON (see §Response Output Contract) — the base
        # class implementation reads it for you.  Override here only when you
        # need runtime logic (status-code branching, regex, enrichment, …).
        return super().after_fetch(response, spec)


SITE_PLUGIN = MySitePlugin
```

### Plugin Hooks

| Hook | Called When | Input | Returns |
|------|------------|-------|--------|
| `before_fetch` | Before building the fetch JS | `request` dict + `tab`/`store` | Modified `request` dict |
| `after_fetch` | After receiving raw response | `response` dict + `spec` dict | Modified `response` dict — default reads `spec["response_contract"]` (see §Response Output Contract); override for runtime logic |
| `paginate` | For custom pagination logic | `fetch_fn` + `request` + `first_response` | `AsyncIterator[dict]` |
| `media_contract` | Before `--save-images` writes files | `result` dict + `spec` dict | `list[dict]` of save items — default reads `spec["media_contract"]`; override for runtime logic (see §Media Output) |

### Plugin Access to Variables

Merged CLI variables are available in `before_fetch`:

```python
merged = request.pop("_ziniao_merged_vars", None)
start_date = str(merged.get("start_date", "")).strip()
```

## Step 4: Test

```bash
# Install the site-hub repo (if not already)
ziniao site add https://github.com/tianyehedashu/site-hub.git

# Verify the preset appears
ziniao site list | grep my-site

# Show preset details
ziniao site show my-site/my-action

# Test single request
ziniao my-site my-action -V param1=value1 -o result.json

# Test pagination
ziniao my-site my-action -V param1=value1 --all -o all_results.json

# Test with JSON output for scripting
ziniao my-site my-action -V param1=value1 --json

# For image-generating presets: verify --save-images replaces base64 with file paths
ziniao my-site my-action -V prompt="test" --save-images out/test --timeout 180
```

## Step 5: Add Agent Skills

Each site can expose multiple skills following the [agentskills.io](https://agentskills.io/specification) spec:

```
<site>/skills/
├── <site>-<topic-a>/    ← kebab-case, name field must match directory name
│   └── SKILL.md
└── <site>-<topic-b>/
    └── SKILL.md
```

SKILL.md format:

```markdown
---
name: <site>-<topic>
description: One-line description of when to use this skill.
allowed-tools: Bash(ziniao:*)
---

# Skill Title

## Prerequisites
1. Login to the site in browser
2. Install site-hub repo

## Available Presets
| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao <site> <action>` | ... | ... |

## Common Workflows
### 1. Workflow Title
\`\`\`bash
ziniao navigate "https://..."
ziniao <site> <action> -V key=value -o output.json
\`\`\`
```

Rules:
- `name` must match the directory name, kebab-case only
- `description` should include trigger keywords for agent matching
- Keep it concise: agents load name+description first, full content on demand

## Step 6: Commit to site-hub

```bash
cd site-hub
mkdir -p <site-name>/skills/<site>-<topic>
# Add: <action>.json, __init__.py (if plugin), skills/<topic>/SKILL.md
git add .
git commit -m "feat: add <site-name> site adapter"
git push
```

Users update via `ziniao site update`.

## JSON Template Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name (shown in `site list`) |
| `description` | Yes | What this preset does |
| `auth.type` | Yes | `cookie` / `xsrf` / `token` / `none` |
| `auth.hint` | No | Human-readable login instruction |
| `navigate_url` | No | Auto-navigate before fetch if not on this page |
| `mode` | No | `fetch` (default) or `js` (custom page script) |
| `url` | Yes | API endpoint URL (supports `{{vars}}`) |
| `method` | Yes | `GET` or `POST` |
| `headers` | No | Static HTTP headers |
| `header_inject` | No | Dynamic header injection rules |
| `vars` | No | Template variable definitions with type/required/default |
| `body` | No | Request body (JSON object or form-encoded string; supports `{{vars}}`) |
| `script` | Only for `mode:js` | JavaScript source executed in page context; receives `{{body}}` as a substituted literal and must `return` a JSON value |
| `pagination` | No | Pagination config for `--page` / `--all` support |
| `output_decode_encoding` | No | Default `--decode-encoding` for `-o` (e.g. `cp932`) |
| `media_contract` | No | Declarative rules for `--save-images` (see §Media Output). Compiled by the default `SitePlugin.media_contract`; override in a plugin for runtime logic. |
| `response_contract` | No | Declarative body-parse + lift rules (see §Response Output Contract). Applied by the default `SitePlugin.after_fetch`; override in a plugin for runtime logic. |

`vars[].type` accepted values: `str` · `int` · `float` · `bool` · `file` · `file_list` (see §Variable Types).

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 401/403 | Ensure browser tab is logged in; check `header_inject` header names match actual requests |
| Empty results | Check date range and parameter values; use `selection_type` or similar dimension params |
| Preset not found | Run `ziniao site add https://github.com/tianyehedashu/site-hub.git` then `ziniao site update` |
| Garbled CSV | Add `output_decode_encoding` to preset or use `--decode-encoding cp932` on CLI |
| CSRF token missing | Verify cookie name in `header_inject[].key` matches the actual cookie; some sites use `_csrf` in meta tag → use `source: eval` |
| Variable not rendered | Check `{{var_name}}` syntax in `url`/`body`/`headers`; var must be declared in `vars` |
| CORS preflight blocked on 3rd-party API | Switch `Content-Type` to `text/plain;charset=UTF-8` in the `mode:js` `fetch`, or call the same-origin tRPC/Route-Handler equivalent |
| `ConnectionResetError` / 1 MB daemon cap on upload | Use `type: file` / `file_list` instead of passing base64 through `-V`; the daemon resolves `@@ZFILE@@` / `@@ZURL@@` refs server-side |
| Request times out on long generations | Add `page_fetch` cases rely on `_SLOW_COMMANDS` (120 s); for `count >= 2` / slower models, pass `--timeout 300` explicitly |
| reCAPTCHA Enterprise 403 | Inspect `window.grecaptcha.enterprise` and webpack bundles to find the correct `site key` + `action` string; both are case-sensitive |
| Need a reusable CDN URL in the response | Prefer signed URLs (`source: url` in `media_contract`) over inline base64 so `--save-images` streams the bytes instead of allocating huge strings through the daemon |
| `--save-images` writes nothing / silently overwrites a file | Either your preset has no `media_contract` block *and* no plugin override (→ add one, see §Media Output), or a multi-field rule is using a `stem_suffix` without `{field}`; the compiler now raises `ValueError("…collide…")` with the offending rule highlighted |
| `response["parsed"]` suddenly missing after upgrade | An older plugin used to synthesize `parsed` in `after_fetch`; that Python has been replaced by declarative `response_contract`. Add the block to the preset JSON (see §Response Output Contract) — the default `after_fetch` will lift it back. |

## Case Studies

| Site | Tier | Highlights |
|------|------|-----------|
| [`rakuten/`](../../rakuten/) | Tier 2 (`mode: fetch` + `xsrf`) | XSRF cookie injection, pagination with `body_field`, Shift_JIS CSV decoding |
| [`google-flow/`](../../google-flow/) | Tier 3 (`mode: js`) | Multi-step: session → `uploadImage` → `project.createProject` tRPC → reCAPTCHA Enterprise → `batchGenerateImages` → `fifeUrl` download. See [`google-flow/README.md`](../../google-flow/README.md) for the full architecture. |
