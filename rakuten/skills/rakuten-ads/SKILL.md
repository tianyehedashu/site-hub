---
name: rakuten-ads
description: Fetch Rakuten RMS advertising reports (RPP search ads, TDA display ads, CPA, coupon performance) via ziniao site presets. Use when the user needs to download Rakuten ad reports, analyze RPP/TDA performance, export coupon data, or query Rakuten advertising APIs. Triggers include "rakuten ads", "rakuten advertising", "RPP report", "TDA report", "楽天広告", "coupon performance", or any Rakuten ad data request.
allowed-tools: Bash(ziniao:*)
---

# Rakuten Advertising Reports

Fetch Rakuten RMS advertising reports through page-context API calls. All presets use the browser''s active login session - no API keys needed.

## Prerequisites

1. **Login first**: Open a browser tab and log in to [RMS](https://glogin.rms.rakuten.co.jp/).
2. **Install site-hub repo** (if not already):
   ```bash
   ziniao site add https://github.com/tianyehedashu/site-hub.git
   ```

## Available Presets

### RPP (Search Ads)

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten rpp-search` | RPP report search (paginated) | `start_date` *, `end_date` *, `selection_type` |
| `ziniao rakuten rpp-search-item` | RPP report by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten rpp-exp-report` | RPP expense report (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten rpp-exp-report-item` | RPP expense report by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten rpp-exp-merchant` | RPP merchant expense | `start_date` *, `end_date` * |

### TDA (Display Ads)

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten tda-reports-search` | TDA report search (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten tda-reports-search-item` | TDA report by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten tda-exp-report` | TDA expense report (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten tda-exp-report-item` | TDA expense report by item (paginated) | `start_date` *, `end_date` * |

### CPA / Affiliate

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten cpa-reports-search` | CPA report search | `start_date` *, `end_date` * |
| `ziniao rakuten afl-report-pending` | Affiliate pending report | `start_date` *, `end_date` * |

### Coupon & Deal

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten cpnadv-performance-retrieve` | Coupon performance (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten cpnadv-performance-retrieve-item` | Coupon performance by item (paginated) | `start_date` *, `end_date` * |
| `ziniao rakuten datatool-deal-csv` | Deal CSV download | `start_date` *, `end_date` * |

### Other

| Command | Description | Key Variables |
|---------|-------------|---------------|
| `ziniao rakuten rmail-reports` | R-Mail report | `start_date` *, `end_date` * |
| `ziniao rakuten shared-purchase-detail` | Shared purchase detail | `start_date` *, `end_date` * |

## Common Workflows

### 1. Download RPP Daily Report (All Pages)

```bash
ziniao navigate "https://ad.rms.rakuten.co.jp/rpp/reports"
ziniao rakuten rpp-search -V start_date=2026-03-01 -V end_date=2026-03-07 --all -o rpp_daily.json
```

`selection_type` values: `1`=daily, `2`=by campaign, `3`=by item, `4`=by keyword.

### 2. Download TDA Advertising Report

```bash
ziniao navigate "https://ad.rms.rakuten.co.jp/tda/reports"
ziniao rakuten tda-reports-search -V start_date=2026-03-01 -V end_date=2026-03-31 --all -o tda.json
```

### 3. Coupon Performance Analysis

```bash
ziniao rakuten cpnadv-performance-retrieve -V start_date=2026-03-01 -V end_date=2026-03-07 --all -o coupon.json
```

### 4. Deal Data Export

```bash
ziniao rakuten datatool-deal-csv -V start_date=2026-03-01 -V end_date=2026-03-31 -o deals.csv
```

## Auth Notes

- **XSRF-protected endpoints** (RPP, TDA, etc.): The preset uses `header_inject` to automatically extract `XSRF-TOKEN` from cookies and add it to the request header. No manual configuration needed.
- All requests are made in the page context via `fetch()`, inheriting the browser tab''s cookies.

## Pagination

Presets marked as "(paginated)" support:

- `--page N` - fetch a specific page
- `--all` - fetch all pages, merging items from `merge_items_field`
- `--all -o output.json` - save merged results to file

## Variables

| Variable | Type | Description |
|----------|------|-------------|
| `start_date` | str (YYYY-MM-DD) | Report start date |
| `end_date` | str (YYYY-MM-DD) | Report end date |
| `selection_type` | int | Aggregation dimension (1=daily, 2=campaign, 3=item, 4=keyword) |
| `page` | int | Page number (default 1) |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Preset not found" | Run `ziniao site add https://github.com/tianyehedashu/site-hub.git` |
| 401/403 error | Login to RMS in the browser tab first |
| Empty results | Check date range; use `selection_type` to change aggregation |
