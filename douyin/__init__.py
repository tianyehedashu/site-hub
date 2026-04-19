"""Douyin (抖音) creator platform site plugin.

Provides article/image publishing via ``mode: ui`` presets that
orchestrate head-image upload, crop, title fill, tiptap content insert,
CDN wait, and publish button click.

Var injection: ``mode: ui`` presets automatically get
``window.__flow_vars`` injected before any step runs (handled by
``_flow_run`` in dispatch.py), so eval steps can access
``window.__flow_vars.title``, ``window.__flow_vars.content_html``, etc.
"""

from __future__ import annotations

from ziniao_mcp.sites import SitePlugin


class DouyinPlugin(SitePlugin):
    """Plugin for creator.douyin.com publishing flows."""

    site_id = "douyin"


SITE_PLUGIN = DouyinPlugin
