from typing import List
from bs4 import BeautifulSoup
from models.offer import Offer
from .base import BasePortalScraper

# LinkedIn public job search (no login required, pero agresivo en anti-bot).
# Playwright con user-agent real suele funcionar. Si falla → lista vacía, no error.
BASE = "https://www.linkedin.com/jobs/search"


class LinkedInScraper(BasePortalScraper):
    portal_name = "linkedin"

    def scrape(self, query: str, location: str = "", start_id: int = 0) -> List[Offer]:
        loc = location or "Spain"
        url = f"{BASE}/?keywords={query}&location={loc}&f_TPR=r86400"  # últimas 24h
        try:
            html = self._playwright_html(url, ".base-card, .job-search-card", timeout=15000)
            return self._parse(html, start_id)
        except Exception:
            return []

    def _parse(self, html: str, start_id: int) -> List[Offer]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".base-card, .job-search-card")
        offers: List[Offer] = []
        for card in cards:
            a = card.select_one("a.base-card__full-link, a.job-search-card__title-link")
            title_el = card.select_one(".base-search-card__title, h3.base-search-card__title")
            if not a or not title_el:
                continue
            comp = card.select_one(".base-search-card__subtitle a, h4.base-search-card__subtitle")
            loc = card.select_one(".job-search-card__location, span.job-search-card__location")
            href = a.get("href", "").split("?")[0]  # quita tracking params
            offers.append(Offer(
                id=start_id + len(offers),
                title=title_el.get_text(strip=True),
                url=href,
                company=comp.get_text(strip=True) if comp else None,
                location=loc.get_text(strip=True) if loc else None,
                description=None,
                source=self.portal_name,
            ))
        return offers
