"""抖音文章装配器 —— 把 Google Flow 出的原图 + 正文草稿 拼装成可直接发布的素材。

输入：一个 ``manifest.json`` 清单（agent 按 SKILL.md 约定的格式产出）。
输出（写入 manifest 所在目录的 ``build/`` 子目录）：

- ``title.txt``     UTF-8 无 BOM，供 ``ziniao -V title=@file:`` 使用
- ``head.jpg``      正文头图（嵌在正文里，16:9），供 ``-V head_image=...`` 使用
- ``cover.jpg``     推荐页封面（3:4 竖图，1080x1440），供 ``-V cover_image=...`` 使用
- ``content.html``  正文 HTML（所有正文图均已 base64 内联），供 ``-V content_html=@file:`` 使用
- ``preview.html``  本地浏览器可直接打开的排版预览（图用原路径引用，方便快速校对）

脚本不做"发布"本身。发布由 ``ziniao douyin article-publish`` preset 负责。

依赖：Pillow（已出现在 ziniao 的 dev venv；若缺失，脚本会给出清晰的安装提示）。

manifest.json 格式：

.. code-block:: json

    {
      "title": "文章标题（≤30 字）",
      "style_prefix": "统一的英文风格前缀，参考 SKILL.md Phase 3",
      "head_image": {
        "src": "raw/head-0-fifeUrl.jpg",
        "alt": "头图文字替代"
      },
      "cover_image": {
        "src": "raw/cover.jpg",
        "note": "可选。若缺省，自动从 head_image.src 中心裁剪为 3:4。源图最长边建议 >=1440px 以免上抖音被拒。"
      },
      "blocks": [
        {"type": "p",   "text": "段落文字 1"},
        {"type": "img", "src": "raw/body-1.jpg", "alt": "图的文字替代"},
        {"type": "p",   "text": "段落文字 2"},
        {"type": "img", "src": "raw/body-2.jpg"},
        {"type": "p",   "text": "结尾段"}
      ]
    }

所有 ``src`` 既可是绝对路径，也可以相对于 manifest.json 所在目录解析。
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError as exc:
    sys.stderr.write(
        "[build_html] 需要 Pillow 才能缩放/编码图片。安装方式（任选其一）：\n"
        "  pip install Pillow\n"
        "  uv pip install Pillow\n"
        f"原始错误：{exc}\n"
    )
    sys.exit(2)

DEFAULT_WH = (640, 360)
DEFAULT_QUALITY = 75
COVER_WH = (1080, 1440)  # 抖音文章封面要求 3:4 竖图；低于此分辨率会被拒。
COVER_QUALITY = 90
CONTENT_HTML_SOFT_LIMIT_KB = 800  # 超过此阈值给出警告；抖音实测 1–2 MB 仍可工作


def _resolve(base: Path, ref: str) -> Path:
    p = Path(ref)
    return p if p.is_absolute() else (base / p).resolve()


def _jpeg_bytes(src: Path, wh: tuple[int, int], quality: int) -> bytes:
    with Image.open(src) as img:
        im = img.convert("RGB").resize(wh, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _cover_jpeg_bytes(src: Path, wh: tuple[int, int], quality: int) -> tuple[bytes, tuple[int, int]]:
    """中心裁剪到 3:4 比例，再放大到 ``wh``。返回 (jpeg, 源图尺寸)。"""
    with Image.open(src) as img:
        im = img.convert("RGB")
        sw, sh = im.size
        tw, th = wh
        target_ratio = tw / th
        src_ratio = sw / sh
        if src_ratio > target_ratio:
            new_w = int(sh * target_ratio)
            left = (sw - new_w) // 2
            im = im.crop((left, 0, left + new_w, sh))
        else:
            new_h = int(sw / target_ratio)
            top = (sh - new_h) // 2
            im = im.crop((0, top, sw, top + new_h))
        im = im.resize(wh, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue(), (sw, sh)


def _b64_data_uri(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")


def _render_paragraph(text: str) -> str:
    return f"<p>{html.escape(text)}</p>"


def _render_img_inline(data_uri: str, alt: str) -> str:
    safe_alt = html.escape(alt, quote=True)
    return f'<p><img src="{data_uri}" alt="{safe_alt}" style="max-width:100%"/></p>'


def _render_img_preview(src: Path, alt: str) -> str:
    safe_alt = html.escape(alt, quote=True)
    return (
        f'<p><img src="{src.as_uri()}" alt="{safe_alt}" '
        'style="max-width:640px;display:block;margin:16px auto"/></p>'
    )


def _render_preview_document(title: str, body_html: str, head_img: Path) -> str:
    head = (
        f'<figure style="text-align:center"><img src="{head_img.as_uri()}" '
        'style="max-width:640px" alt="头图"/><figcaption>头图</figcaption></figure>'
    )
    return (
        "<!doctype html><meta charset='utf-8'>"
        f"<title>{html.escape(title)} · 预览</title>"
        "<style>body{max-width:720px;margin:32px auto;padding:0 16px;"
        "font-family:-apple-system,'Segoe UI',sans-serif;line-height:1.8;"
        "color:#1a1a1a}"
        "h1{font-size:24px}p{font-size:16px;text-align:justify}"
        "img{border-radius:8px}</style>"
        f"<h1>{html.escape(title)}</h1>" + head + body_html
    )


def _validate(manifest: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    title = (manifest.get("title") or "").strip()
    if not title:
        errs.append("manifest.title 为空")
    elif len(title) > 30:
        errs.append(f"title 过长（{len(title)} > 30 字），抖音会截断")
    if not manifest.get("head_image", {}).get("src"):
        errs.append("manifest.head_image.src 缺失")
    blocks = manifest.get("blocks") or []
    if not blocks:
        errs.append("manifest.blocks 为空，正文无内容")
    has_text = any(b.get("type") == "p" and (b.get("text") or "").strip() for b in blocks)
    if not has_text:
        errs.append("manifest.blocks 没有任何非空文字段")
    img_blocks = [b for b in blocks if b.get("type") == "img"]
    p_blocks = [b for b in blocks if b.get("type") == "p"]
    if p_blocks and len(img_blocks) < max(1, len(p_blocks) // 2):
        errs.append(
            f"图文密度偏低：{len(p_blocks)} 段正文仅 {len(img_blocks)} 张图。"
            "SKILL 要求每段至少能对应到一张视觉呼应图（头图不计）。"
        )
    return errs


def build(manifest_path: Path, width: int, height: int, quality: int) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_dir = manifest_path.parent.resolve()

    errs = _validate(manifest)
    if errs:
        raise SystemExit("[build_html] manifest 校验失败：\n  - " + "\n  - ".join(errs))

    out_dir = base_dir / "build"
    out_dir.mkdir(parents=True, exist_ok=True)

    title: str = manifest["title"].strip()
    (out_dir / "title.txt").write_text(title, encoding="utf-8")

    head_ref = manifest["head_image"]["src"]
    head_src = _resolve(base_dir, head_ref)
    if not head_src.exists():
        raise SystemExit(f"[build_html] 头图不存在：{head_src}")
    head_jpeg = _jpeg_bytes(head_src, (width, height), quality)
    head_out = out_dir / "head.jpg"
    head_out.write_bytes(head_jpeg)

    cover_ref = (manifest.get("cover_image") or {}).get("src") or head_ref
    cover_src = _resolve(base_dir, cover_ref)
    if not cover_src.exists():
        raise SystemExit(f"[build_html] 封面源图不存在：{cover_src}")
    cover_jpeg, (cw, ch) = _cover_jpeg_bytes(cover_src, COVER_WH, COVER_QUALITY)
    cover_out = out_dir / "cover.jpg"
    cover_out.write_bytes(cover_jpeg)
    cover_warnings: list[str] = []
    if cw < COVER_WH[0] or ch < COVER_WH[1]:
        cover_warnings.append(
            f"封面源图分辨率偏低（{cw}x{ch} < {COVER_WH[0]}x{COVER_WH[1]}），"
            "抖音可能判定为『封面分辨率过低』。建议换一张更高分辨率的源图。"
        )

    content_parts: list[str] = []
    preview_parts: list[str] = []
    bytes_accum = 0

    for idx, block in enumerate(manifest.get("blocks") or []):
        btype = block.get("type")
        if btype == "p":
            text = (block.get("text") or "").strip()
            if not text:
                continue
            frag = _render_paragraph(text)
            content_parts.append(frag)
            preview_parts.append(frag)
        elif btype == "img":
            ref = block.get("src")
            if not ref:
                raise SystemExit(f"[build_html] blocks[{idx}] 缺少 src")
            src = _resolve(base_dir, ref)
            if not src.exists():
                raise SystemExit(f"[build_html] 图片不存在：{src}")
            jpeg = _jpeg_bytes(src, (width, height), quality)
            # 为预览，把缩放后的图另存一份；预览 html 引用此文件
            preview_img_path = out_dir / f"body-{idx}.jpg"
            preview_img_path.write_bytes(jpeg)
            alt = block.get("alt") or ""
            content_parts.append(_render_img_inline(_b64_data_uri(jpeg), alt))
            preview_parts.append(_render_img_preview(preview_img_path, alt))
            bytes_accum += len(jpeg)
        else:
            raise SystemExit(f"[build_html] blocks[{idx}] 未知 type={btype!r}（支持 p / img）")

    content_html = "".join(content_parts)
    (out_dir / "content.html").write_text(content_html, encoding="utf-8")

    preview_html = _render_preview_document(title, "".join(preview_parts), head_out)
    (out_dir / "preview.html").write_text(preview_html, encoding="utf-8")

    size_kb = len(content_html.encode("utf-8")) / 1024
    warnings: list[str] = list(cover_warnings)
    if size_kb > CONTENT_HTML_SOFT_LIMIT_KB:
        warnings.append(
            f"content.html 约 {size_kb:.1f} KB，超过软阈值 {CONTENT_HTML_SOFT_LIMIT_KB} KB；"
            "若发布超时可把 quality 降到 65 或 width 降到 512 重跑"
        )

    return {
        "title": title,
        "out_dir": str(out_dir),
        "head_image": str(head_out),
        "cover_image": str(cover_out),
        "cover_source_wh": [cw, ch],
        "content_html": str(out_dir / "content.html"),
        "title_file": str(out_dir / "title.txt"),
        "preview_html": str(out_dir / "preview.html"),
        "content_html_kb": round(size_kb, 1),
        "total_inline_image_bytes": bytes_accum,
        "paragraph_count": sum(1 for b in manifest.get("blocks") or [] if b.get("type") == "p"),
        "inline_image_count": sum(1 for b in manifest.get("blocks") or [] if b.get("type") == "img"),
        "warnings": warnings,
    }


def _format_publish_command(result: dict[str, Any]) -> str:
    return (
        "ziniao --timeout 300 douyin article-publish ^\n"
        f'  -V title=@file:{result["title_file"]} ^\n'
        f'  -V content_html=@file:{result["content_html"]} ^\n'
        f'  -V head_image="{result["head_image"]}" ^\n'
        f'  -V cover_image="{result["cover_image"]}"'
    )


def _force_utf8_stdout() -> None:
    # Windows 默认控制台常为 gbk/cp936，打印中文或 Unicode 符号会 UnicodeEncodeError。
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError):
                pass


def main() -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(description="抖音文章 HTML 装配器（manifest 驱动）")
    parser.add_argument("manifest", type=Path, help="manifest.json 路径")
    parser.add_argument("--width", type=int, default=DEFAULT_WH[0])
    parser.add_argument("--height", type=int, default=DEFAULT_WH[1])
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果（便于 Agent 解析）")
    args = parser.parse_args()

    if not args.manifest.exists():
        sys.stderr.write(f"[build_html] 找不到 manifest：{args.manifest}\n")
        return 2

    result = build(args.manifest.resolve(), args.width, args.height, args.quality)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"[build_html] OK 完成，写入目录：{result['out_dir']}")
    print(f"  title       : {result['title']}")
    print(f"  head_image  : {result['head_image']}")
    cw, ch = result['cover_source_wh']
    print(f"  cover_image : {result['cover_image']} (源图 {cw}x{ch} → {COVER_WH[0]}x{COVER_WH[1]})")
    print(f"  content.html: {result['content_html_kb']} KB "
          f"({result['paragraph_count']} 段正文 + {result['inline_image_count']} 张内联图)")
    print(f"  preview     : {result['preview_html']}")
    if result["warnings"]:
        print("  warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    print("\n下一步 · 本地预览（浏览器打开）：")
    print(f"  start {result['preview_html']}")
    print("\n下一步 · 直接发布：")
    print(_format_publish_command(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
