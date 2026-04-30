"""1688 site-hub plugin tests (run from ziniao repo root: ``uv run pytest site-hub/tests/``)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_INIT = _ROOT / "1688" / "__init__.py"


def _load_1688_module():
    spec = importlib.util.spec_from_file_location("site_hub_1688_plugin", _INIT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_image_search_preset_route() -> None:
    preset = json.loads((_ROOT / "1688" / "image-search.json").read_text(encoding="utf-8"))
    assert preset.get("_ziniao_1688_route") == "image-search"
    assert preset.get("mode") == "js"


def test_keyword_search_preset_route() -> None:
    preset = json.loads((_ROOT / "1688" / "keyword-search.json").read_text(encoding="utf-8"))
    assert preset.get("_ziniao_1688_route") == "keyword-search"
    assert preset.get("mode") == "js"


def test_before_fetch_strips_route_and_injects_script() -> None:
    mod = _load_1688_module()
    plugin = mod.Site1688Plugin()
    spec = json.loads((_ROOT / "1688" / "image-search.json").read_text(encoding="utf-8"))
    spec["body"] = json.dumps({"image": "dGVzdA==", "begin_page": 1, "page_size": 40})
    out = plugin.before_fetch(spec)
    assert out.get("_ziniao_1688_route") is None
    assert out.get("mode") == "js"
    script = out.get("script", "")
    assert "imageSearchOfferResultViewService" in script
    assert "md5" in script.lower() or "globalThis.md5" in script


@pytest.mark.parametrize(
    "name,body_obj,needle",
    [
        ("image-compare", {"image": "e30=", "max_pages": 2, "page_size": 40}, "imageSearchOfferResultViewService"),
        ("keyword-search", {"q": "test", "begin_page": 1, "page_size": 20}, "marketOfferResultViewService"),
        ("product", {"offer_id": "123"}, "detail.1688.com/offer/"),
        ("supplier", {"shop_url": "https://example.1688.com"}, "companyName"),
        ("media-save", {"offer_id": "123"}, "cbu01"),
    ],
)
def test_routes_inject_script(name: str, body_obj: dict, needle: str) -> None:
    mod = _load_1688_module()
    plugin = mod.Site1688Plugin()
    spec = json.loads((_ROOT / "1688" / f"{name}.json").read_text(encoding="utf-8"))
    spec["body"] = json.dumps(body_obj)
    out = plugin.before_fetch(spec)
    assert out.get("_ziniao_1688_route") is None
    script = out.get("script", "")
    assert len(script) > 50
    assert needle in script


def test_keyword_search_script_includes_charset_utf8() -> None:
    """Regression: without charset=utf8, marketOfferResultViewService often returns empty offerList."""
    mod = _load_1688_module()
    plugin = mod.Site1688Plugin()
    spec = json.loads((_ROOT / "1688" / "keyword-search.json").read_text(encoding="utf-8"))
    spec["body"] = json.dumps({"q": "test", "begin_page": 1, "page_size": 20})
    out = plugin.before_fetch(spec)
    script = out.get("script", "")
    assert "charset" in script
    assert "utf8" in script


def test_missing_md5_error_script() -> None:
    mod = _load_1688_module()
    orig = mod._read_md5

    def _empty() -> str:
        return ""

    mod._read_md5 = _empty  # type: ignore[method-assign]
    try:
        s = mod._image_search_js()
        assert "missing" in s.lower() or "internal" in s.lower()
    finally:
        mod._read_md5 = orig  # type: ignore[method-assign]
