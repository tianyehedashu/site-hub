---
name: rakuten
description: Rakuten RMS/RPP advertising and review data fetching via ziniao site presets. Use when the user needs to download Rakuten advertising reports (RPP, TDA, CPA, coupon), review CSVs, deal data, or search Rakuten RMS APIs. Triggers include "rakuten report", "rakuten advertising", "rakuten review", "楽天レポート", "RPP", "TDA", "Rakuten API", or any Rakuten seller data extraction request.
allowed-tools: Bash(ziniao:*)
---

# Rakuten Site Presets

Fetch Rakuten RMS advertising reports, review data, and more through page-context API calls. All presets use the browser's active login session — no API keys needed.

## Prerequisites

1. **Login first**: Open a browser tab and log in to [RMS](https://glogin.rms.rakuten.co.jp/) or the relevant Rakuten service page.
2. **Install site-hub repo** (if not already):
   ```bash
   ziniao site add https://github.com/tianyehedashu/site-hub.git
   ```

## Available Presets

### RPP (Search Ads) Reports

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten rpp-search` | RPP report search (paginated) | `start_date` *, `end_date` *, `selection_type` |
| `ziniao rakuten rpp-search-item` | RPP report by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten rpp-exp-report` | RPP expense report (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten rpp-exp-report-item` | RPP expense report by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten rpp-exp-merchant` | RPP merchant expense | `start_date` *, `end_date` * |

### TDA (Display Ads) Reports

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten tda-reports-search` | TDA report search (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten tda-reports-search-item` | TDA report by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten tda-exp-report` | TDA expense report (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten tda-exp-report-item` | TDA expense report by item (paginated) | `start_date` *, `end_date` * |

### CPA / Affiliate Reports

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten cpa-reports-search` | CPA report search | `start_date` *, `end_date` * |
| `ziniao rakuten afl-report-pending` | Affiliate pending report | `start_date` *, `end_date` * |

### Coupon & Deal Data

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten cpnadv-performance-retrieve` | Coupon performance (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten cpnadv-performance-retrieve-item` | Coupon performance by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten datatool-deal-csv` | Deal CSV download | `start_date` *, `end_date` * |

### Reviews

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten reviews-csv` | Review CSV download (CP932→UTF-8) | `last_days` (default 30) or `start_date` + `end_date` |

### Other

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten rmail-reports` | R-Mail report | `start_date` *, `end_date` * |
| `ziniao rakuten shared-purchase-detail` | Shared purchase detail | `start_date` *, `end_date` * |

## Common Workflows

### 1. Download RPP Daily Report (All Pages)

```bash
# Navigate to RPP page first (establishes session context)
ziniao navigate "https://ad.rms.rakuten.co.jp/rpp/reports"

# Fetch all pages of daily RPP data
ziniao rakuten rpp-search -V start_date=2026-03-01 -V end_date=2026-03-07 --all -o rpp_daily.json
```

`selection_type` values: `1`=daily, `2`=by campaign, `3`=by item, `4`=by keyword.

### 2. Download Review CSV

```bash
# Navigate to review page
ziniao navigate "https://review.rms.rakuten.co.jp/search/"

# Download last 30 days of reviews (auto CP932→UTF-8)
ziniao rakuten reviews-csv -o reviews.csv

# Or specify date range
ziniao rakuten reviews-csv -V start_date=2026-03-01 -V end_date=2026-04-01 -o reviews.csv
```

### 3. Download TDA Advertising Report

```bash
ziniao navigate "https://ad.rms.rakuten.co.jp/tda/reports"
ziniao rakuten tda-reports-search -V start_date=2026-03-01 -V end_date=2026-03-31 --all -o tda.json
```

### 4. Coupon Performance Analysis

```bash
ziniao rakuten cpnadv-performance-retrieve -V start_date=2026-03-01 -V end_date=2026-03-07 --all -o coupon.json
```

## Auth Notes

- **XSRF-protected endpoints** (RPP, TDA, etc.): The preset uses `header_inject` to automatically extract `XSRF-TOKEN` from cookies and add it to the request header. No manual configuration needed.
- **Cookie-only endpoints** (reviews, rmail, etc.): Standard browser cookie auth.
- All requests are made in the page context via `fetch()`, inheriting the browser tab's cookies.

## Pagination

Presets marked as "(paginated)" support:

- `--page N` — fetch a specific page
- `--all` — fetch all pages, merging items from `merge_items_field`
- `--all -o output.json` — save merged results to file

## Output Encoding

- `reviews-csv` preset: auto-decodes CP932 (Shift_JIS) to UTF-8 via `output_decode_encoding: cp932`.
- `datatool-deal-csv`: CSV output.
- Most other presets return JSON.

## Variables Convention

| Variable | Type | Description |
|----------|------|-------------|
| `start_date` | str (YYYY-MM-DD) | Report start date |
| `end_date` | str (YYYY-MM-DD) | Report end date |
| `selection_type` | int | Aggregation dimension (1=daily, 2=campaign, 3=item, 4=keyword) |
| `page` | int | Page number (default 1) |
| `last_days` | int | For reviews: number of days back from today (default 30, JST) |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Preset not found" | Run `ziniao site add https://github.com/tianyehedashu/site-hub.git` |
| 401/403 error | Login to RMS in the browser tab first |
| Empty results | Check date range; use `selection_type` to change aggregation |
| CSV garbled | `reviews-csv` auto-decodes; for others use `--decode-encoding cp932` |
