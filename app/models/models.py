from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from app.models.db import Base

class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True, unique=True)

    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="brand", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="brand", cascade="all, delete-orphan")
    socials = relationship("Social", back_populates="brand", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="brand", cascade="all, delete-orphan")
    links = relationship("Link", back_populates="brand", cascade="all, delete-orphan")
    about = relationship("About", back_populates="brand", uselist=False, cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_range: Mapped[str | None] = mapped_column(Text, nullable=True)
    images_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    brand = relationship("Brand", back_populates="products")

class FAQ(Base):
    __tablename__ = "faqs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    brand = relationship("Brand", back_populates="faqs")

class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    kind: Mapped[str | None] = mapped_column(String(64), nullable=True) 
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand = relationship("Brand", back_populates="policies")

class Social(Base):
    __tablename__ = "socials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    platform: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(1024))

    brand = relationship("Brand", back_populates="socials")

class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    kind: Mapped[str] = mapped_column(String(32)) # email/phone/address
    value: Mapped[str] = mapped_column(String(1024))

    brand = relationship("Brand", back_populates="contacts")

class Link(Base):
    __tablename__ = "links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(1024))

    brand = relationship("Brand", back_populates="links")

class About(Base):
    __tablename__ = "about"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand = relationship("Brand", back_populates="about")


# app/models/model.py
# from sqlalchemy.orm import relationship, Mapped, mapped_column
# from sqlalchemy import Integer, String, Text, ForeignKey
# from app.models.db import Base

# ... (existing model definitions: Brand, Product, FAQ, Policy, Social, Contact, Link, About)

class Competitor(Base):
    __tablename__ = "competitors"
    __table_args__ = {'extend_existing': True}  # Allow redefinition of the table
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_url: Mapped[str] = mapped_column(String(512), nullable=False)  # The brand's website
    competitor_website: Mapped[str] = mapped_column(String(512), nullable=False)  # Competitor's website

    brand = relationship("Brand", primaryjoin="Brand.website==Competitor.website_url", foreign_keys=[website_url])