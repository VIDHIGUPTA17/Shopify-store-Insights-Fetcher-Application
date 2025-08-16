# Shopify Store Insights-Fetcher

A FastAPI service that takes a Shopify store URL and returns a structured JSON of brand insights
(without using the official Shopify API). It scrapes common Shopify routes and the website HTML
for product catalog, hero products, policies, FAQs, socials, contact details, about text, and important links.

---

## Features
- **Whole product catalog** via `/products.json` (if available)
- **Hero products** parsed from homepage
- **Policies** (privacy, refund/returns) via footer/policy routes
- **FAQs** from typical pages (`/pages/faq`, `/pages/faqs`, etc.) and Q/A extraction
- **Social handles** (Instagram, Facebook, TikTok, YouTube, X/Twitter, LinkedIn, Pinterest)
- **Contact details** (emails, phone numbers) via regex
- **About/Brand text** from common about pages
- **Important links** (order tracking, contact us, blogs)
- **Optional persistence** to SQLite using SQLAlchemy

---

## Project Structure
```text
shopify-insights-fetcher/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ scraper/
│  │  ├─ __init__.py
│  │  ├─ utils.py
│  │  └─ shopify_scraper.py
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ schemas.py
│  │  ├─ db.py
│  │  └─ models.py
│  └─ services/
│     ├─ __init__.py
│     ├─ insights_service.py
│     └─ competitor.py  (optional stub)
├─ requirements.txt
└─ README.md
```

---

## Quickstart (Local)

1) **Create & activate a virtual environment**
```bash
cd shopify-insights-fetcher
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

2) **Install dependencies**
```bash
pip install -r requirements.txt
```

3) **Run the API**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) **Test with curl**
```bash
curl -X POST "http://localhost:8000/fetch_insights" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://memy.co.in", "persist": false, "with_competitors": false}'
```

5) **Interactive Docs**
Open your browser at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Notes
- This app **does not** use the official Shopify API. It relies on public pages and JSON endpoints (like `/products.json`).
- Some stores disable or rate-limit `/products.json`. In those cases, the scraper falls back to HTML parsing and `/collections/all` if available.
- The scraper uses heuristics (CSS selectors, regex) that work for many Shopify themes but not **all**.
- To persist results to SQLite, pass `"persist": true` in the request body (a local `brand_insights.db` file will be created).

---

## Example Request Body
```json
{
  "website_url": "https://memy.co.in",
  "persist": false,
  "with_competitors": false
}
```

## Example Minimal Response (shape)
```json
{
  "brand_name": "Example Store",
  "website": "https://example.myshopify.com",
  "product_catalog": [ ... ],
  "hero_products": [ ... ],
  "policies": {
    "privacy_policy": { "url": "...", "content": "..." },
    "return_policy": { "url": "...", "content": "..." }
  },
  "faqs": [ { "question": "...", "answer": "..." } ],
  "social_handles": { "instagram": "...", "facebook": "...", ... },
  "contact_details": { "emails": ["..."], "phones": ["..."] },
  "about_us": { "url": "...", "content": "..." },
  "important_links": {
    "order_tracking": "...",
    "contact_us": "...",
    "blogs": "...",
    "others": [ "..." ]
  },
  "scrape_meta": {
    "requested_at": "ISO8601",
    "success": true,
    "errors": [ "..." ]
  }
}
```
