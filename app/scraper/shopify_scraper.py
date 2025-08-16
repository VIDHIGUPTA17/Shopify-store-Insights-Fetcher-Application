from __future__ import annotations
import re, datetime
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.scraper.utils import (
    normalize_base, fetch_text, fetch_json, make_soup, absolute,
    EMAIL_RE, PHONE_RE, categorize_social, unique_preserve_order
)
from app.models.schemas import (
    Product, Policy, FAQ, SocialHandles, ContactDetails, About, ImportantLinks, Policies, BrandContext, ScrapeMeta
)

PRODUCT_LINK_RE = re.compile(r"/products/([a-zA-Z0-9\-\._]+)")

async def fetch_products_catalog(client: httpx.AsyncClient, base: str) -> List[Product]:
    # Try /products.json (pagination optional)
    products: List[Product] = []
    url = urljoin(base, "/products.json?limit=250")
    data, status = await fetch_json(client, url)
    if data and isinstance(data, dict) and "products" in data:
        for p in data["products"]:
            handle = p.get("handle")
            title = p.get("title")
            vendor = p.get("vendor")
            product_type = p.get("product_type")
            tags = p.get("tags")
            images = [img.get("src") for img in p.get("images", []) if img.get("src")]
            prod = Product(
                id=p.get("id"),
                handle=handle,
                title=title,
                vendor=vendor,
                product_type=product_type,
                tags=tags if isinstance(tags, list) else (tags.split(",") if isinstance(tags, str) else None),
                images=images,
                url=urljoin(base, f"/products/{handle}") if handle else None
            )
            products.append(prod)
        return products

    # Fallback: parse /collections/all
    html, _ = await fetch_text(client, urljoin(base, "/collections/all"))
    if not html:
        return products
    soup = make_soup(html)
    links = soup.select("a[href*='/products/']")
    seen = set()
    for a in links:
        href = a.get("href")
        if not href: 
            continue
        m = PRODUCT_LINK_RE.search(href)
        if not m:
            continue
        handle = m.group(1)
        if handle in seen:
            continue
        seen.add(handle)
        title = (a.get("title") or a.text or "").strip() or None
        img = a.find("img")
        img_src = img.get("src") if img else None
        prod = Product(handle=handle, title=title, images=[img_src] if img_src else None, url=urljoin(base, f"/products/{handle}"))
        products.append(prod)
    return products

def _extract_product_from_card(a_tag) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return handle, title, image"""
    href = a_tag.get("href")
    if not href:
        return None, None, None
    m = PRODUCT_LINK_RE.search(href)
    if not m:
        return None, None, None
    handle = m.group(1)
    title = (a_tag.get("title") or a_tag.text or "").strip() or None
    img = a_tag.find("img")
    img_src = img.get("src") if img else None
    return handle, title, img_src

async def fetch_hero_products(client: httpx.AsyncClient, base: str) -> List[Product]:
    html, _ = await fetch_text(client, base + "/")
    prods: List[Product] = []
    if not html:
        return prods
    soup = make_soup(html)
    # Common theme patterns: product cards or featured collections on homepage
    cards = soup.select("a[href*='/products/']")
    seen = set()
    for a in cards[:50]:  # limit to top 50 links for homepage
        handle, title, img_src = _extract_product_from_card(a)
        if not handle or handle in seen:
            continue
        seen.add(handle)
        prods.append(Product(handle=handle, title=title, images=[img_src] if img_src else None, url=urljoin(base, f"/products/{handle}")))
    return prods

async def discover_footer_links(client: httpx.AsyncClient, base: str) -> Dict[str, str]:
    html, _ = await fetch_text(client, base + "/")
    links: Dict[str, str] = {}
    if not html:
        return links
    soup = make_soup(html)
    for a in soup.select("footer a[href]"):
        label = (a.text or "").strip().lower()
        href = a.get("href")
        if not href:
            continue
        url = urljoin(base, href)
        links[label] = url
    return links

async def fetch_policy_page(client: httpx.AsyncClient, base: str, kind: str, links_map: Dict[str, str]) -> Policy | None:
    candidates = [
        f"/policies/{kind}-policy",
        f"/pages/{kind}-policy",
        f"/pages/{kind}",
    ]
    # also search footer labels
    for label, url in links_map.items():
        if kind in label:
            candidates.append(url)

    for path in candidates:
        url = urljoin(base, path) if path.startswith("/") else path
        html, status = await fetch_text(client, url)
        if not html or (status and status >= 400):
            continue
        soup = make_soup(html)
        text = soup.get_text("\n", strip=True)
        if len(text) > 50:
            return Policy(url=url, content=text[:15000])  # cap size
    return None

async def fetch_about(client: httpx.AsyncClient, base: str, links_map: Dict[str, str]) -> About | None:
    candidates = ["/pages/about-us", "/pages/about", "/about", "/about-us"]
    for label, url in links_map.items():
        if "about" in label:
            candidates.append(url)
    for path in candidates:
        url = urljoin(base, path) if path.startswith("/") else path
        html, status = await fetch_text(client, url)
        if not html or (status and status >= 400):
            continue
        soup = make_soup(html)
        text = soup.get_text("\n", strip=True)
        if len(text) > 50:
            return About(url=url, content=text[:15000])
    return None

async def fetch_faqs(client: httpx.AsyncClient, base: str, links_map: Dict[str, str]) -> List[FAQ]:
    faqs: List[FAQ] = []
    candidates = ["/pages/faq", "/pages/faqs", "/pages/help", "/pages/support", "/apps/help-center", "/policies/faq"]
    for label, url in links_map.items():
        if "faq" in label or "help" in label or "support" in label:
            candidates.append(url)
    seen_pages = set()
    for path in candidates:
        url = urljoin(base, path) if path.startswith("/") else path
        if url in seen_pages:
            continue
        seen_pages.add(url)
        html, status = await fetch_text(client, url)
        if not html or (status and status >= 400):
            continue
        soup = make_soup(html)
        # Pattern 1: dl/dt/dd pairs
        for dt in soup.select("dt"):
            q = dt.get_text(" ", strip=True)
            dd = dt.find_next_sibling("dd")
            a = dd.get_text(" ", strip=True) if dd else ""
            if q and a:
                faqs.append(FAQ(question=q, answer=a, url=url))
        # Pattern 2: headings + next paragraph(s)
        for h in soup.select("h1, h2, h3, h4, h5, h6"):
            q = h.get_text(" ", strip=True)
            # Gather following siblings until next heading
            answer_parts = []
            for sib in h.next_siblings:
                if getattr(sib, "name", None) in ["h1","h2","h3","h4","h5","h6"]:
                    break
                text = getattr(sib, "get_text", lambda *a, **k: str(sib))(" ", strip=True)
                if text:
                    answer_parts.append(text)
            a = " ".join(answer_parts).strip()
            if q and len(a) > 0 and len(q) < 220:
                faqs.append(FAQ(question=q, answer=a[:1000], url=url))
        # Pattern 3: details/summary blocks
        for det in soup.select("details"):
            sum_el = det.find("summary")
            if not sum_el:
                continue
            q = sum_el.get_text(" ", strip=True)
            a = det.get_text(" ", strip=True).replace(q, "", 1).strip()
            if q and a:
                faqs.append(FAQ(question=q, answer=a[:1000], url=url))
    # Deduplicate by (q, a) pair
    uniq = []
    seen = set()
    for f in faqs:
        key = (f.question[:200].lower(), f.answer[:200].lower())
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq[:100]

async def extract_socials_contacts_and_links(client: httpx.AsyncClient, base: str):
    html, _ = await fetch_text(client, base + "/")
    footer_links = {}
    emails = []
    phones = []
    others = []

    if not html:
        return footer_links, emails, phones, others

    soup = make_soup(html)

    # Links in footer
    for a in soup.select("footer a[href]"):
        label = (a.text or "").strip()
        href = a.get("href")
        url = urljoin(base, href)
        footer_links[label.lower()] = url
        others.append(url)

    # Any link on homepage can also count for "others"
    for a in soup.select("a[href]"):
        href = a.get("href")
        url = urljoin(base, href)
        if url.startswith(base):
            others.append(url)

    # Emails and phones
    text = soup.get_text(" ", strip=True)
    from app.scraper.utils import EMAIL_RE, PHONE_RE, unique_preserve_order
    emails = unique_preserve_order(EMAIL_RE.findall(text))
    phones = unique_preserve_order(PHONE_RE.findall(text))

    return footer_links, emails, phones, unique_preserve_order(others)

async def build_brand_context(website_url: str) -> BrandContext:
    base = normalize_base(website_url)
    errors: List[str] = []
    async with httpx.AsyncClient() as client:
        # connectivity check
        home_html, status = await fetch_text(client, base + "/")
        if not home_html:
            raise ConnectionError(f"Website not reachable or returned status {status}")

        soup = make_soup(home_html)
        title = soup.find("title").get_text(strip=True) if soup.find("title") else None

        products = await fetch_products_catalog(client, base)
        hero_products = await fetch_hero_products(client, base)

        footer_links, emails, phones, other_links = await extract_socials_contacts_and_links(client, base)

        # Policies
        privacy = await fetch_policy_page(client, base, "privacy", footer_links)
        ret = await fetch_policy_page(client, base, "refund", footer_links)
        if not ret:
            ret = await fetch_policy_page(client, base, "return", footer_links)

        # About
        about = await fetch_about(client, base, footer_links)

        # FAQs
        faqs = await fetch_faqs(client, base, footer_links)

        # Socials from footer links
        social_map = {}
        from app.scraper.utils import categorize_social
        for label, url in footer_links.items():
            platform, link = categorize_social(url)
            if platform:
                social_map[platform] = link

        important = {}
        # Heuristics
        for label, url in footer_links.items():
            ll = label.lower()
            if "track" in ll or ("order" in ll and "track" in ll):
                important["order_tracking"] = url
            if "contact" in ll:
                important["contact_us"] = url
            if "blog" in ll:
                important["blogs"] = url

        return BrandContext(
            brand_name=title,
            website=base,
            product_catalog=products,
            hero_products=hero_products,
            policies=Policies(
                privacy_policy=privacy,
                return_policy=ret,
            ),
            faqs=faqs,
            social_handles=SocialHandles(**social_map),
            contact_details=ContactDetails(emails=emails, phones=phones),
            about_us=about,
            important_links=ImportantLinks(
                order_tracking=important.get("order_tracking"),
                contact_us=important.get("contact_us"),
                blogs=important.get("blogs"),
                others=other_links[:100],
            ),
            scrape_meta=ScrapeMeta(
                requested_at=datetime.datetime.utcnow().isoformat() + "Z",
                success=True,
                errors=errors,
            )
        )
