---
name: rakuten-reviews
description: Download and analyze Rakuten product review CSV data via ziniao site presets. Use when the user needs to export Rakuten reviews, analyze customer feedback, download review CSV, or query review.rms.rakuten.co.jp. Triggers include "rakuten review", "rakuten reviews CSV", "楽天レビュー", "customer feedback", "review download", or any Rakuten review data request.
allowed-tools: Bash(ziniao:*)
---

# Rakuten Review CSV Download

Download Rakuten product review data as CSV through page-context API calls. The preset auto-decodes CP932 (Shift_JIS) to UTF-8.

## Prerequisites

1. **Login first**: Open a browser tab and log in to [RMS](https://glogin.rms.rakuten.co.jp/) and navigate to [review.rms.rakuten.co.jp](https://review.rms.rakuten.co.jp/search/).
2. **Install site-hub repo** (if not already):
   ```bash
   ziniao site add https://github.com/tianyehedashu/site-hub.git
   ```

## Available Presets

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten reviews-csv` | Review CSV download (CP932 to UTF-8) | `last_days` (default 30) or `start_date` + `end_date` |

## Common Workflows

### 1. Download Recent Reviews (Last 30 Days)

```bash
ziniao navigate "https://review.rms.rakuten.co.jp/search/"
ziniao rakuten reviews-csv -o reviews.csv
```

### 2. Download Reviews by Date Range

```bash
ziniao rakuten reviews-csv -V start_date=2026-03-01 -V end_date=2026-04-01 -o reviews.csv
```

### 3. Download with Keyword Filter

```bash
ziniao rakuten reviews-csv -V kw="良い" -o reviews_filtered.csv
```

## Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `last_days` | int | 30 | Number of days back from today (JST). Used when start_date/end_date are omitted. |
| `start_date` | str | - | Start date (YYYY-MM-DD). Must be used together with end_date. |
| `end_date` | str | - | End date (YYYY-MM-DD). Must be used together with start_date. |
| `kw` | str | "" | Keyword filter (empty = all reviews) |
| `ao` | str | "A" | Sort order parameter |
| `st` | int | 1 | st parameter |
| `tc` | int | 0 | tc parameter |
| `ev` | int | 0 | ev parameter |

## Output Format

- Output is a CSV file, auto-decoded from CP932 (Shift_JIS) to UTF-8 via output_decode_encoding: cp932.
- Use `-o filename.csv` to save to file.

## Auth Notes

- **Cookie-based auth**: Standard browser cookie auth. No XSRF token needed.
- The request is made in the page context via fetch(), inheriting the browser tab cookies.
- The plugin (RakutenPlugin) dynamically constructs the review CSV URL with date parameters.

## Date Logic

The RakutenPlugin.before_fetch() handles date computation:
- If both start_date and end_date are provided: uses those dates directly.
- If neither is provided: computes from last_days (default 30) using JST (Asia/Tokyo) timezone.
- If only one is provided: raises an error.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Preset not found" | Run `ziniao site add https://github.com/tianyehedashu/site-hub.git` |
| 401/403 error | Login to RMS and navigate to review.rms.rakuten.co.jp |
| CSV garbled | The preset auto-decodes CP932; if still garbled, try --decode-encoding cp932 |
| Empty results | Check date range; ensure last_days covers the period with reviews |
