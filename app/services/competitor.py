# from typing import List
# from sqlalchemy.orm import Session
# from app.models.db import Competitor

# async def find_competitors(website_url: str, db: Session) -> List[str]:
#     competitors = (
#         db.query(Competitor.competitor_website)
#         .filter(Competitor.website_url == website_url)
#         .all()
#     )
#     # db.query returns list of tuples → extract values
#     return [c[0] for c in competitors]

from typing import List
from sqlalchemy.orm import Session
from app.models.models import Competitor  # Correct import
from app.models.schemas import BrandContext
from app.services.insights_service import fetch_and_optionally_persist
import httpx
from bs4 import BeautifulSoup
from app.scraper.utils import normalize_base, fetch_text

async def find_competitors(website_url: str, db: Session) -> List[BrandContext]:
    """
    Find competitors for a given Shopify store and fetch their insights.
    """
    competitors = []
    
    # Step 1: Query existing competitors from the database
    stored_competitors = (
        db.query(Competitor.competitor_website)
        .filter(Competitor.website_url == website_url)
        .all()
    )
    competitor_urls = [c[0] for c in stored_competitors]
    
    # Step 2: If no competitors in DB, discover new ones
    if not competitor_urls:
        competitor_urls = await discover_competitors(website_url)
        # Save discovered competitors to the database
        for comp_url in competitor_urls:
            db.add(Competitor(website_url=website_url, competitor_website=comp_url))
        db.commit()

    # Step 3: Fetch insights for each competitor
    for comp_url in competitor_urls[:3]:  # Limit to 3 competitors to avoid performance issues
        try:
            ctx = await fetch_and_optionally_persist(comp_url, db)
            competitors.append(ctx)
        except Exception as e:
            # Log error but continue with other competitors
            print(f"Error fetching insights for competitor {comp_url}: {str(e)}")
    
    return competitors

async def discover_competitors(website_url: str) -> List[str]:
    """
    Discover potential competitors by analyzing the website's content.
    This is a placeholder; in a real implementation, use web search or product similarity.
    """
    async with httpx.AsyncClient() as client:
        html, _ = await fetch_text(client, normalize_base(website_url) + "/")
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        title = soup.find("title").get_text(strip=True) if soup.find("title") else ""
        keywords = title.lower().split()  # Simple keyword extraction
        
        # Simulate competitor discovery based on keywords
        competitor_urls = []
        if "hair" in keywords:
            competitor_urls = ["https://hairoriginals.com", "https://examplehair.com"]
        elif "fashion" in keywords:
            competitor_urls = ["https://memy.co.in", "https://examplefashion.com"]
        else:
            competitor_urls = ["https://colourpop.com", "https://examplegeneric.com"]
        
        return [normalize_base(url) for url in competitor_urls[:3]]