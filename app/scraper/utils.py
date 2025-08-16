from __future__ import annotations
import re
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Tuple, List, Dict, Any
from app.config import settings, DEFAULT_HEADERS

def normalize_base(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return base

async def fetch_text(client: httpx.AsyncClient, url: str) -> tuple[str | None, int | None]:
    try:
        r = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True, timeout=settings.request_timeout_seconds)
        if r.status_code >= 400:
            return None, r.status_code
        return r.text, r.status_code
    except Exception:
        return None, None

async def fetch_json(client: httpx.AsyncClient, url: str) -> tuple[dict | None, int | None]:
    try:
        r = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True, timeout=settings.request_timeout_seconds)
        if r.status_code >= 400:
            return None, r.status_code
        return r.json(), r.status_code
    except Exception:
        return None, None

def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

def absolute(base: str, path: str | None) -> str | None:
    if not path:
        return None
    return urljoin(base, path)

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d")

SOCIAL_DOMAINS = {
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "tiktok.com": "tiktok",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "twitter.com": "twitter",
    "x.com": "x",
    "linkedin.com": "linkedin",
    "pinterest.com": "pinterest",
}

def categorize_social(url: str) -> tuple[str | None, str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    for dom, name in SOCIAL_DOMAINS.items():
        if dom in host:
            return name, url
    return None, url

def unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    out = []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out
