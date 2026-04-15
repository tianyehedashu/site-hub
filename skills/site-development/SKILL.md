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
Step 2: Choose the tier (fetch / header_inject / plugin)
Step 3: Write the preset JSON
Step 4: Write the plugin (if needed)
Step 5: Test with ziniao CLI
Step 6: Add skills/ and commit to site-hub
```

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
----------------|-----------|------|
| Only Cookie (no special headers) | `cookie` | **Tier 1** — fetch preset only |
| CSRF token in Cookie + header | `xsrf` | **Tier 2** — preset with `header_inject` |
| Bearer / custom token from page state | `token` | **Tier 2** — preset with `header_inject` (source: eval) |
| Complex signatures (X-s, X-t, etc.) | — | **Tier 3** — SitePlugin required |
| No auth needed | `none` | **Tier 1** — fetch preset only |

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

## Step 3: Write the Plugin (Tier 3)

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

    def after_fetch(self, response: dict, request: dict) -> dict:
        # Post-process the raw response.
        # response has: status, statusText, body (raw text)
        # Attach response["parsed"] for downstream consumers.
        return response


SITE_PLUGIN = MySitePlugin
```

### Plugin Hooks

| Hook | Called When | Input | Returns |
|------|------------|-------|--------|
| `before_fetch` | Before building the fetch JS | `request` dict + `tab`/`store` | Modified `request` dict |
| `after_fetch` | After receiving raw response | `response` dict + `request` dict | Modified `response` dict |
| `paginate` | For custom pagination logic | `fetch_fn` + `request` + `first_response` | `AsyncIterator[dict]` |

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
iniao site show my-site/my-action

# Test single request
ziniao my-site my-action -V param1=value1 -o result.json

# Test pagination
ziniao my-site my-action -V param1=value1 --all -o all_results.json

# Test with JSON output for scripting
ziniao my-site my-action -V param1=value1 --json
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
| `pagination` | No | Pagination config for `--page` / `--all` support |
| `output_decode_encoding` | No | Default `--decode-encoding` for `-o` (e.g. `cp932`) |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 401/403 | Ensure browser tab is logged in; check `header_inject` header names match actual requests |
| Empty results | Check date range and parameter values; use `selection_type` or similar dimension params |
| Preset not found | Run `ziniao site add https://github.com/tianyehedashu/site-hub.git` then `ziniao site update` |
| Garbled CSV | Add `output_decode_encoding` to preset or use `--decode-encoding cp932` on CLI |
| CSRF token missing | Verify cookie name in `header_inject[].key` matches the actual cookie; some sites use `_csrf` in meta tag → use `source: eval` |
| Variable not rendered | Check `{{var_name}}` syntax in `url`/`body`/`headers`; var must be declared in `vars` |
