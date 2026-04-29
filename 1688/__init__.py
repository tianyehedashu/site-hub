"""1688 site presets — browser-context mtop image upload + search APIs.

Embeds MIT-licensed blueimp-md5 (``_md5_min.js``, IIFE root ``globalThis``)
for mtop H5 signatures. Public flow mirrors community reverse-engineering
(mtop upload + ``imageSearchOfferResultViewService``); 1688 may change
endpoints — errors return ``error`` / ``hint`` for agents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ziniao_mcp.sites._base import SitePlugin

_MD5_PATH = Path(__file__).with_name("_md5_min.js")


def _read_md5() -> str:
    if not _MD5_PATH.is_file():
        return ""
    return _MD5_PATH.read_text(encoding="utf-8")


def _strip_route(spec: dict[str, Any]) -> None:
    spec.pop("_ziniao_1688_route", None)


def _wrap_async(md5: str, inner_block: str) -> str:
    """``dispatch`` does ``await (`` *script* ``)`` — *script* must be one async IIFE."""
    if not md5:
        return (
            "(async () => JSON.stringify({error: 'internal', "
            "hint: 'missing site-hub/1688/_md5_min.js (run ziniao site update site-hub)'}))()"
        )
    return f"(async () => {{\n{md5}\n{inner_block}\n}})()"


# language=JavaScript
_HELPERS = r"""
const getCk = (name) => {
  const parts = document.cookie.split(';');
  for (const p of parts) {
    const s = p.trim();
    if (s.startsWith(name + '=')) return decodeURIComponent(s.slice(name.length + 1));
  }
  return '';
};
const stripDataUrl = (s) => String(s || '').replace(/^data:image\/\w+;base64,?/i, '');
const JSV = '2.7.2';
const VER = '1.0';
const API_KEY = '12574478';
const APP_NAME = 'searchImageUpload';
const APP_KEY = 'pvvljh1grxcmaay2vgpe9nb68gg9ueg2';
const TOKEN_API = 'mtop.ovs.traffic.landing.seotaglist.queryHotSearchWord';
const UPLOAD_API = 'mtop.1688.imageService.putImage';

/** Prefer XHR — 1688 页面常 hook ``fetch``（baxia），XHR 仍常为原生。 */
const xhrText = (method, url, headers, body) =>
  new Promise((resolve, reject) => {
    const x = new XMLHttpRequest();
    x.open(method, url, true);
    x.withCredentials = true;
    if (headers) {
      for (const [k, v] of Object.entries(headers)) {
        if (v != null && v !== '') x.setRequestHeader(k, String(v));
      }
    }
    x.onload = () => resolve(x.responseText || '');
    x.onerror = () => reject(new Error('xhr_failed'));
    x.send(body == null ? null : body);
  });
const xhrJson = async (method, url, headers, body) => JSON.parse(await xhrText(method, url, headers, body));
"""


def _image_search_block() -> str:
    return (
        _HELPERS
        + r"""
  const md5fn = globalThis.md5;
  if (typeof md5fn !== 'function') {
    return JSON.stringify({ error: 'md5_init_failed', hint: 'globalThis.md5 missing' });
  }
  const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__;
  const imageB64 = stripDataUrl(b.image || '');
  if (!imageB64) {
    return JSON.stringify({ error: 'missing_image', hint: 'Pass -V image=/path/to.jpg' });
  }

  try {
    await xhrText(
      'GET',
      'https://log.mmstat.com/eg.js?t=' + Date.now(),
      { referer: 'https://www.1688.com/' },
      null,
    );
  } catch (e) {}

  let tk = getCk('_m_h5_tk');
  if (!tk) {
    const tp = new URLSearchParams({
      jsv: JSV,
      appKey: API_KEY,
      t: String(Date.now()),
      api: TOKEN_API,
      v: VER,
      type: 'jsonp',
      dataType: 'jsonp',
      callback: 'mtopjsonp1',
      preventFallback: 'true',
      data: '{}',
    });
    await xhrText(
      'GET',
      'https://h5api.m.1688.com/h5/' + TOKEN_API.toLowerCase() + '/' + VER + '/?' + tp.toString(),
      { referer: 'https://www.1688.com/', origin: 'https://www.1688.com' },
      null,
    );
    tk = getCk('_m_h5_tk');
  }
  if (!tk) {
    return JSON.stringify({
      error: 'no_m_h5_tk',
      hint: 'Open https://www.1688.com in this tab and reload once.',
      action: 'ziniao navigate "https://www.1688.com/"',
    });
  }
  const token = tk.split('_')[0];
  const uploadDataStr = JSON.stringify({ imageBase64: imageB64, appName: APP_NAME, appKey: APP_KEY });
  const t = String(Date.now());
  const sign = md5fn(token + '&' + t + '&' + API_KEY + '&' + uploadDataStr);
  const up = new URLSearchParams({
    jsv: JSV,
    appKey: API_KEY,
    t,
    sign,
    api: UPLOAD_API,
    ignoreLogin: 'true',
    prefix: 'h5api',
    v: VER,
    ecode: '0',
    dataType: 'jsonp',
    jsonpIncPrefix: 'search1688',
    timeout: '20000',
    type: 'originaljson',
  });
  const uploadJson = await xhrJson(
    'POST',
    'https://h5api.m.1688.com/h5/' + UPLOAD_API.toLowerCase() + '/' + VER + '/?' + up.toString(),
    {
      'content-type': 'application/x-www-form-urlencoded',
      origin: 'https://www.1688.com',
      referer: 'https://www.1688.com/',
    },
    new URLSearchParams({ data: uploadDataStr }).toString(),
  );
  const imageId = (uploadJson.data || {}).imageId;
  const sessionId = (uploadJson.data || {}).sessionId;
  const requestId = (uploadJson.data || {}).requestId;
  if (!imageId) {
    return JSON.stringify({ error: 'upload_failed', detail: uploadJson });
  }
  const beginPage = Math.max(1, parseInt(String(b.begin_page || b.beginPage || '1'), 10) || 1);
  const pageSize = Math.min(60, Math.max(10, parseInt(String(b.page_size || b.pageSize || '40'), 10) || 40));
  const sp = new URLSearchParams({
    tab: 'imageSearch',
    imageAddress: '',
    imageId: String(imageId),
    imageIdList: String(imageId),
    beginPage: String(beginPage),
    pageSize: String(pageSize),
    pageName: 'image',
    sessionId: String(sessionId || ''),
  });
  const listJson = await xhrJson(
    'GET',
    'https://search.1688.com/service/imageSearchOfferResultViewService?' + sp.toString(),
    { origin: 'https://s.1688.com', referer: 'https://s.1688.com/' },
    null,
  );
  const data = (listJson.data || {}).data || {};
  const offerList = data.offerList || [];
  const pageCount = data.pageCount;
  const imageSearchUrl =
    'https://s.1688.com/youyuan/index.htm?tab=imageSearch&imageAddress=&imageId=' +
    encodeURIComponent(String(imageId)) +
    '&imageIdList=' +
    encodeURIComponent(String(imageId));
  return JSON.stringify({
    ok: true,
    imageId,
    sessionId,
    requestId,
    beginPage,
    pageSize,
    pageCount,
    imageSearchUrl,
    count: offerList.length,
    offers: offerList,
  });
"""
    )


def _image_compare_block() -> str:
    return (
        _HELPERS
        + r"""
  const md5fn = globalThis.md5;
  if (typeof md5fn !== 'function') {
    return JSON.stringify({ error: 'md5_init_failed' });
  }
  const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__;
  const imageB64 = stripDataUrl(b.image || '');
  if (!imageB64) {
    return JSON.stringify({ error: 'missing_image' });
  }

  try {
    await xhrText(
      'GET',
      'https://log.mmstat.com/eg.js?t=' + Date.now(),
      { referer: 'https://www.1688.com/' },
      null,
    );
  } catch (e) {}
  let tk = getCk('_m_h5_tk');
  if (!tk) {
    const tp = new URLSearchParams({
      jsv: JSV, appKey: API_KEY, t: String(Date.now()), api: TOKEN_API, v: VER,
      type: 'jsonp', dataType: 'jsonp', callback: 'mtopjsonp1', preventFallback: 'true', data: '{}',
    });
    await xhrText(
      'GET',
      'https://h5api.m.1688.com/h5/' + TOKEN_API.toLowerCase() + '/' + VER + '/?' + tp.toString(),
      { referer: 'https://www.1688.com/', origin: 'https://www.1688.com' },
      null,
    );
    tk = getCk('_m_h5_tk');
  }
  if (!tk) {
    return JSON.stringify({ error: 'no_m_h5_tk', hint: 'Visit www.1688.com first' });
  }
  const token = tk.split('_')[0];
  const uploadDataStr = JSON.stringify({ imageBase64: imageB64, appName: APP_NAME, appKey: APP_KEY });
  const t = String(Date.now());
  const sign = md5fn(token + '&' + t + '&' + API_KEY + '&' + uploadDataStr);
  const up = new URLSearchParams({
    jsv: JSV, appKey: API_KEY, t, sign, api: UPLOAD_API, ignoreLogin: 'true', prefix: 'h5api', v: VER,
    ecode: '0', dataType: 'jsonp', jsonpIncPrefix: 'search1688', timeout: '20000', type: 'originaljson',
  });
  const uploadJson = await xhrJson(
    'POST',
    'https://h5api.m.1688.com/h5/' + UPLOAD_API.toLowerCase() + '/' + VER + '/?' + up.toString(),
    {
      'content-type': 'application/x-www-form-urlencoded',
      origin: 'https://www.1688.com',
      referer: 'https://www.1688.com/',
    },
    new URLSearchParams({ data: uploadDataStr }).toString(),
  );
  const imageId = (uploadJson.data || {}).imageId;
  const sessionId = (uploadJson.data || {}).sessionId;
  if (!imageId) {
    return JSON.stringify({ error: 'upload_failed', detail: uploadJson });
  }
  const maxPages = Math.min(10, Math.max(1, parseInt(String(b.max_pages || 3), 10) || 3));
  const pageSize = Math.min(60, Math.max(10, parseInt(String(b.page_size || 40), 10) || 40));
  const all = [];
  let pageCount = null;
  for (let p = 1; p <= maxPages; p++) {
    const sp = new URLSearchParams({
      tab: 'imageSearch',
      imageAddress: '',
      imageId: String(imageId),
      imageIdList: String(imageId),
      beginPage: String(p),
      pageSize: String(pageSize),
      pageName: 'image',
      sessionId: String(sessionId || ''),
    });
    const listJson = await xhrJson(
      'GET',
      'https://search.1688.com/service/imageSearchOfferResultViewService?' + sp.toString(),
      { origin: 'https://s.1688.com', referer: 'https://s.1688.com/' },
      null,
    );
    const data = (listJson.data || {}).data || {};
    const offerList = data.offerList || [];
    if (pageCount == null && data.pageCount != null) pageCount = data.pageCount;
    all.push(...offerList);
    if (!offerList.length) break;
    if (pageCount != null && p >= pageCount) break;
  }
  const prices = [];
  for (const o of all) {
    const op = (((o.tradePrice || {}).offerPrice || {}).priceInfo || {}).price;
    if (op != null && op !== '') {
      const n = parseFloat(String(op));
      if (!Number.isNaN(n)) prices.push(n);
    }
  }
  prices.sort((a, b) => a - b);
  const mid = prices.length ? prices[Math.floor((prices.length - 1) / 2)] : null;
  return JSON.stringify({
    ok: true,
    imageId,
    sessionId,
    pages_fetched: maxPages,
    pageCount,
    count: all.length,
    offers: all,
    stats: {
      price_min: prices.length ? prices[0] : null,
      price_max: prices.length ? prices[prices.length - 1] : null,
      price_median: mid,
      sample_size: prices.length,
    },
  });
"""
    )


def _image_search_js() -> str:
    return _wrap_async(_read_md5(), _image_search_block())


def _image_compare_js() -> str:
    return _wrap_async(_read_md5(), _image_compare_block())


def _product_js() -> str:
    return r"""(async () => {
  const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__;
  const oid = String(b.offer_id || b.offerId || '').trim();
  if (!oid) {
    return JSON.stringify({ error: 'missing_offer_id', hint: 'Pass -V offer_id=1234567890' });
  }
  const url = 'https://detail.1688.com/offer/' + encodeURIComponent(oid) + '.html';
  const html = document.documentElement ? document.documentElement.outerHTML : '';
  let title = '';
  const tm = html.match(/<title>([^<]{1,500})<\/title>/i);
  if (tm) title = tm[1].trim();
  let subject = '';
  const sm = html.match(/"subject"\s*:\s*"([^"\\]{1,800})"/);
  if (sm) subject = sm[1].replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
  const imgs = [];
  const imgRe = /https:\/\/cbu01\.alicdn\.com[^"'\s<>]{10,400}/g;
  let m;
  while ((m = imgRe.exec(html)) !== null) {
    if (imgs.length < 40 && !imgs.includes(m[0])) imgs.push(m[0]);
  }
  const head = title + (html || '').slice(0, 12000);
  if (/验证码拦截|安全验证|人机验证|滑动验证|请完成验证|captcha|punish/i.test(head)) {
    return JSON.stringify({
      ok: false,
      error: 'offer_page_captcha',
      hint: '详情页触发风控/验证码。请在当前标签页登录 1688 并完成验证后再执行本预设。',
      action: 'ziniao navigate "https://www.1688.com/"',
      offer_id: oid,
      detail_url: url,
      title: title || null,
    });
  }
  const looks404 =
    /(^|\\s)404(\\s|-|$)/i.test(title) ||
    /页面不存在|找不到该商品|商品已下架|offerId无效|无效的商品/i.test(title + subject) ||
    /"offerStatus"\\s*:\\s*"(deleted|expired)"/i.test(html);
  if (looks404) {
    return JSON.stringify({
      ok: false,
      error: 'offer_page_not_found',
      hint: '非有效商品详情页（常见为 404 / 已下架）。请换有效 offer_id，或先图搜从结果里取 id。',
      action: 'ziniao --json 1688 image-search -V image=你的图.jpg',
      offer_id: oid,
      detail_url: url,
      title: title || null,
    });
  }
  return JSON.stringify({
    ok: true,
    offer_id: oid,
    detail_url: url,
    title: title || subject || null,
    subject: subject || null,
    image_urls_sample: imgs.slice(0, 12),
    note: 'HTML scrape — fields may drift when 1688 updates templates.',
  });
})()"""


def _supplier_js() -> str:
    return r"""(async () => {
  const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__;
  const shopUrl = String(b.shop_url || '').trim();
  if (!shopUrl) {
    return JSON.stringify({ error: 'missing_shop_url', hint: 'Pass -V shop_url=https://xxx.1688.com' });
  }
  const html = document.documentElement ? document.documentElement.outerHTML : '';
  let pageTitle = '';
  const tm = html.match(/<title>([^<]{1,500})<\/title>/i);
  if (tm) pageTitle = tm[1].trim();
  let company = '';
  const cm = html.match(/"companyName"\s*:\s*"([^"\\]{1,400})"/);
  if (cm) company = cm[1].replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
  if (/404|页面不存在|访问被拒绝|店铺不存在/i.test(pageTitle + html.slice(0, 20000))) {
    return JSON.stringify({
      ok: false,
      error: 'shop_page_not_found',
      hint: '店铺页无效或已关闭（常见为 404）。请核对 shop_url。',
      shop_url: shopUrl,
      page_title: pageTitle || null,
    });
  }
  return JSON.stringify({
    ok: true,
    shop_url: shopUrl,
    page_title: pageTitle || null,
    company_name: company || null,
    note: 'Lightweight HTML signals — extend with mtop for richer shop data.',
  });
})()"""


def _media_save_js() -> str:
    return r"""(async () => {
  const b = typeof __BODY__ === 'string' ? JSON.parse(__BODY__) : __BODY__;
  const oid = String(b.offer_id || '').trim();
  if (!oid) {
    return JSON.stringify({ error: 'missing_offer_id' });
  }
  const url = 'https://detail.1688.com/offer/' + encodeURIComponent(oid) + '.html';
  const html = document.documentElement ? document.documentElement.outerHTML : '';
  const imgs = [];
  const imgRe = /https:\/\/cbu01\.alicdn\.com[^"'\s<>]{10,400}/g;
  let m;
  while ((m = imgRe.exec(html)) !== null) {
    if (imgs.length < 24 && !imgs.includes(m[0])) imgs.push(m[0]);
  }
  if (imgs.length === 0) {
    return JSON.stringify({
      ok: false,
      error: 'no_offer_images',
      hint: '详情页无可用主图 URL，多为 404 / 已下架或模板变更。',
      offer_id: oid,
      detail_url: url,
    });
  }
  const items = imgs.map((image) => ({ image }));
  return JSON.stringify({ ok: true, offer_id: oid, items });
})()"""


class Site1688Plugin(SitePlugin):
    site_id = "1688"

    def before_fetch(self, request: dict[str, Any], *, tab: Any = None, store: Any = None) -> dict[str, Any]:
        route = request.get("_ziniao_1688_route")
        if route == "image-search":
            request["mode"] = "js"
            request["script"] = _image_search_js()
            _strip_route(request)
        elif route == "image-compare":
            request["mode"] = "js"
            request["script"] = _image_compare_js()
            _strip_route(request)
        elif route == "product":
            request["mode"] = "js"
            request["script"] = _product_js()
            _strip_route(request)
        elif route == "supplier":
            request["mode"] = "js"
            request["script"] = _supplier_js()
            _strip_route(request)
        elif route == "media-save":
            request["mode"] = "js"
            request["script"] = _media_save_js()
            _strip_route(request)
        return request


SITE_PLUGIN = Site1688Plugin
