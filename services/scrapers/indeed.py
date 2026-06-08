from typing import List
from bs4 import BeautifulSoup
from models.offer import Offer
from .base import BasePortalScraper

# Indeed requiere JS rendering; requests solo falla → vamos directo a Playwright.
BASE = "https://es.indeed.com/jobs"


class IndeedScraper(BasePortalScraper):
    portal_name = "indeed"

    def scrape(self, query: str, location: str = "", start_id: int = 0) -> List[Offer]:
        loc = location or "España"
        url = f"{BASE}?q={query}&l={loc}"
        html = self._playwright_html(url, ".job_seen_beacon, .resultContent", timeout=15000)
        return self._parse(html, start_id)

    def _parse(self, html: str, start_id: int) -> List[Offer]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".job_seen_beacon")
        offers: List[Offer] = []
        for card in cards:
            a = card.select_one("h2.jobTitle a")
            if not a:
                continue
            comp = card.select_one("[data-testid='company-name']")
            loc = card.select_one("[data-testid='text-location']")
            desc = card.select_one(".job-snippet, [data-testid='job-snippet']")
            href = a.get("href", "").strip()
            url = href if href.startswith("http") else f"https://es.indeed.com{href}"
            offers.append(Offer(
                id=start_id + len(offers),
                title=a.get_text(strip=True),
                url=url,
                company=comp.get_text(strip=True) if comp else None,
                location=loc.get_text(strip=True) if loc else None,
                description=desc.get_text(" ", strip=True)[:400] if desc else None,
                source=self.portal_name,
            ))
        return offers
