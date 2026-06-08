from typing import List
import requests
from bs4 import BeautifulSoup
from models.offer import Offer
from .base import BasePortalScraper, HEADERS

BASE = "https://www.infojobs.net/jobsearch/search-results/list.xhtml"


class InfojobsScraper(BasePortalScraper):
    portal_name = "infojobs"

    def scrape(self, query: str, location: str = "", start_id: int = 0) -> List[Offer]:
        html = self._get_html(query, location)
        offers = self._parse(html, start_id)
        if not offers:
            url = f"{BASE}?keyword={query}&normalizedLocation={location}"
            html = self._playwright_html(url, "li.ij-OfferList-item")
            offers = self._parse(html, start_id)
        return offers

    def _get_html(self, query: str, location: str) -> str:
        try:
            params = {"keyword": query}
            if location:
                params["normalizedLocation"] = location
            r = requests.get(BASE, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception:
            return ""

    def _parse(self, html: str, start_id: int) -> List[Offer]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("li.ij-OfferList-item")
        offers: List[Offer] = []
        for card in cards:
            a = card.select_one("a.ij-OfferList-item-title-link")
            if not a:
                continue
            comp = card.select_one("span.ij-OfferList-item-company")
            loc = card.select_one("li.ij-OfferCardContent-description-list-item--location")
            desc = card.select_one("div.ij-OfferList-item-description")
            href = a.get("href", "").strip()
            url = href if href.startswith("http") else f"https://www.infojobs.net{href}"
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
