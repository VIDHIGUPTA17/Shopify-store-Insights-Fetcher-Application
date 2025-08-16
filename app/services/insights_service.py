from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.scraper.shopify_scraper import build_brand_context
from app.models.schemas import BrandContext
from app.models import models

async def fetch_and_optionally_persist(website_url: str, db: Optional[Session] = None) -> BrandContext:
    ctx = await build_brand_context(website_url)

    if db is not None:
        # Upsert brand by website
        brand = db.query(models.Brand).filter(models.Brand.website == ctx.website).one_or_none()
        if brand is None:
            brand = models.Brand(name=ctx.brand_name, website=ctx.website)
            db.add(brand)
            db.flush()
        else:
            brand.name = ctx.brand_name

        # Clear existing children for simplicity (idempotent persistence)
        db.query(models.Product).filter(models.Product.brand_id == brand.id).delete()
        db.query(models.FAQ).filter(models.FAQ.brand_id == brand.id).delete()
        db.query(models.Policy).filter(models.Policy.brand_id == brand.id).delete()
        db.query(models.Social).filter(models.Social.brand_id == brand.id).delete()
        db.query(models.Contact).filter(models.Contact.brand_id == brand.id).delete()
        db.query(models.Link).filter(models.Link.brand_id == brand.id).delete()
        db.query(models.About).filter(models.About.brand_id == brand.id).delete()

        # Persist products
        for p in ctx.product_catalog:
            db.add(models.Product(
                brand_id=brand.id,
                handle=p.handle,
                title=p.title,
                vendor=p.vendor,
                product_type=p.product_type,
                tags=",".join(p.tags) if p.tags else None,
                price_range=str(p.price_range) if p.price_range else None,
                images_json=str(p.images) if p.images else None,
                url=p.url,
            ))

        # Persist FAQs
        for f in ctx.faqs:
            db.add(models.FAQ(
                brand_id=brand.id,
                question=f.question,
                answer=f.answer,
                url=f.url
            ))

        # Policies
        if ctx.policies.privacy_policy:
            db.add(models.Policy(
                brand_id=brand.id,
                kind="privacy",
                url=ctx.policies.privacy_policy.url,
                content=ctx.policies.privacy_policy.content
            ))
        if ctx.policies.return_policy:
            db.add(models.Policy(
                brand_id=brand.id,
                kind="return",
                url=ctx.policies.return_policy.url,
                content=ctx.policies.return_policy.content
            ))

        # Socials
        socials = ctx.social_handles.model_dump(exclude_none=True)
        for platform, url in socials.items():
            db.add(models.Social(brand_id=brand.id, platform=platform, url=url))

        # Contacts
        for e in ctx.contact_details.emails:
            db.add(models.Contact(brand_id=brand.id, kind="email", value=e))
        for p in ctx.contact_details.phones:
            db.add(models.Contact(brand_id=brand.id, kind="phone", value=p))

        # Links (others)
        if ctx.important_links:
            if ctx.important_links.order_tracking:
                db.add(models.Link(brand_id=brand.id, label="order_tracking", url=ctx.important_links.order_tracking))
            if ctx.important_links.contact_us:
                db.add(models.Link(brand_id=brand.id, label="contact_us", url=ctx.important_links.contact_us))
            if ctx.important_links.blogs:
                db.add(models.Link(brand_id=brand.id, label="blogs", url=ctx.important_links.blogs))
            for url in (ctx.important_links.others or [])[:50]:
                db.add(models.Link(brand_id=brand.id, label=None, url=url))

        # About
        if ctx.about_us:
            db.add(models.About(brand_id=brand.id, url=ctx.about_us.url, content=ctx.about_us.content))

        db.commit()

    return ctx
