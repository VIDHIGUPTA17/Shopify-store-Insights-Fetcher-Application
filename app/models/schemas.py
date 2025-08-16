from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Product(BaseModel):
    id: Optional[int] = None
    handle: Optional[str] = None
    title: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: Optional[List[str]] = None
    price_range: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    url: Optional[str] = None

class Policy(BaseModel):
    url: Optional[str] = None
    content: Optional[str] = None

class FAQ(BaseModel):
    question: str
    answer: str
    url: Optional[str] = None

class SocialHandles(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    youtube: Optional[str] = None
    twitter: Optional[str] = None
    x: Optional[str] = None
    linkedin: Optional[str] = None
    pinterest: Optional[str] = None

class ContactDetails(BaseModel):
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    address_texts: List[str] = Field(default_factory=list)

class About(BaseModel):
    url: Optional[str] = None
    content: Optional[str] = None

class ImportantLinks(BaseModel):
    order_tracking: Optional[str] = None
    contact_us: Optional[str] = None
    blogs: Optional[str] = None
    others: List[str] = Field(default_factory=list)

class Policies(BaseModel):
    privacy_policy: Optional[Policy] = None
    return_policy: Optional[Policy] = None

class ScrapeMeta(BaseModel):
    requested_at: str
    success: bool
    errors: List[str] = Field(default_factory=list)

class BrandContext(BaseModel):
    brand_name: Optional[str] = None
    website: Optional[str] = None
    product_catalog: List[Product] = Field(default_factory=list)
    hero_products: List[Product] = Field(default_factory=list)
    policies: Policies = Policies()
    faqs: List[FAQ] = Field(default_factory=list)
    social_handles: SocialHandles = SocialHandles()
    contact_details: ContactDetails = ContactDetails()
    about_us: Optional[About] = None
    important_links: ImportantLinks = ImportantLinks()
    scrape_meta: Optional[ScrapeMeta] = None

class FetchRequest(BaseModel):
    website_url: str
    persist: bool = True
    with_competitors: bool = False


