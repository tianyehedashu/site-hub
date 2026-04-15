# site-hub

Community-driven site presets & plugins for automated web data fetching.

Each site directory contains JSON preset templates and an optional Python plugin (`__init__.py`).

## Directory layout

```
<site>/
  <action>.json      # Preset template (URL, headers, vars, pagination, auth …)
  __init__.py        # Optional SitePlugin for complex logic
```

Example: `rakuten/rpp-search.json` + `rakuten/__init__.py`.

## Usage

```bash
# Add this repo as a preset source
ziniao site add https://github.com/tianyehedashu/site-hub.git

# List available presets
ziniao site list

# Update to latest
ziniao site update site-hub
```

## Contributing

PRs welcome! Add a new `<site>/` directory with your JSON presets and an optional `__init__.py` plugin.
