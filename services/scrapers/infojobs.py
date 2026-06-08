from typing import List
from bs4 import BeautifulSoup
from models.offer import Offer
from .base import BasePortalScraper

# Infojobs carga los resultados con JS → Playwright obligatorio
BASE = "https://www.infojobs.net/ofertas-trabajo"


class InfojobsScraper(BasePortalScraper):
    portal_name = "infojobs"

    def scrape(self, query: str, location: str = "", start_id: int = 0) -> List[Offer]:
        slug = query.replace(" ", "-")
        url = f"{BASE}/{slug}"
        if location:
            url += f"?province={location.lower()}"
        html = self._playwright_html(url, "article, [data-testid='offer-card'], .offer-card", timeout=15000)
        return self._parse(html, start_id)

    def _parse(self, html: str, start_id: int) -> List[Offer]:
        soup = BeautifulSoup(html, "html.parser")
        # Infojobs usa articles con data-testid o clases que cambian, intentamos varios selectores
        cards = (
            soup.select("article[data-testid='offer-card']")
            or soup.select("article.offer-card")
            or soup.select("article")
        )
        offers: List[Offer] = []
        for card in cards:
            a = card.select_one("a[href*='/oferta/'], a[href*='/empleo/']")
            title_el = card.select_one("h2, h3, [data-testid='offer-title']")
            if not a or not title_el:
                continue
            comp = card.select_one("[data-testid='company-name'], .company-name")
            loc = card.select_one("[data-testid='location'], .location")
            desc = card.select_one("[data-testid='description'], .description, p")
            href = a.get("href", "").strip()
            url = href if href.startswith("http") else f"https://www.infojobs.net{href}"
            offers.append(Offer(
                id=start_id + len(offers),
                title=title_el.get_text(strip=True),
                url=url,
                company=comp.get_text(strip=True) if comp else None,
                location=loc.get_text(strip=True) if loc else None,
                description=desc.get_text(" ", strip=True)[:400] if desc else None,
                source=self.portal_name,
            ))
        return offers
