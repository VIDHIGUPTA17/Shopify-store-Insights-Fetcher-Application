from __future__ import annotations
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.schemas import FetchRequest, BrandContext
from app.models.db import get_db, Base, engine
from sqlalchemy.orm import Session
from app.services.insights_service import fetch_and_optionally_persist
from app.services.competitor import find_competitors

app = FastAPI(title="Shopify Store Insights-Fetcher", version="1.0.0")

# Create tables
Base.metadata.create_all(bind=engine)

@app.post("/fetch_insights", response_model=BrandContext)
async def fetch_insights(body: FetchRequest, db: Session = Depends(get_db)):
    try:
        # Connectivity error -> 401
        try:
            ctx = await fetch_and_optionally_persist(
                body.website_url,
                db if body.persist else None
            )
        except ConnectionError as e:
            raise HTTPException(status_code=401, detail=str(e))

        # (Optional) competitors
        if body.with_competitors:
            competitors = await find_competitors(body.website_url)
            if ctx.scrape_meta:
                ctx.scrape_meta.errors.append(f"Competitors not implemented. Found candidates: {competitors}")

        return JSONResponse(content=ctx.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
