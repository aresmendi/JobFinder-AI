import re
from typing import List
import requests
from bs4 import BeautifulSoup
from models.offer import Offer
from services.date_utils import parse_posted_date
from .base import BasePortalScraper, HEADERS

_DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")

BASE = "https://www.tecnoempleo.com/ofertas-trabajo/"


class TecnoempleoScraper(BasePortalScraper):
    portal_name = "tecnoempleo"

    def scrape(self, query: str, location: str = "", start_id: int = 0) -> List[Offer]:
        html = self._get_html(query, location)
        offers = self._parse(html, start_id)
        if not offers:
            html = self._playwright_html(
                f"{BASE}?te={query}&tp={location}",
                "div.p-3.border.rounded.mb-3.bg-white",
            )
            offers = self._parse(html, start_id)
        return offers

    def _get_html(self, query: str, location: str) -> str:
        try:
            params = {"te": query}
            if location:
                params["tp"] = location
            r = requests.get(BASE, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception:
            return ""

    def _parse(self, html: str, start_id: int) -> List[Offer]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.p-3.border.rounded.mb-3.bg-white")
        offers: List[Offer] = []
        for card in cards:
            a = card.select_one("h3 a")
            if not a:
                continue
            comp = card.select_one("a.link-muted")
            loc = card.select_one("span.d-block.d-lg-none b")
            desc = card.select_one("span.hidden-md-down")
            skills = [b.get_text(strip=True)
                      for b in card.select("span.badge.bg-danger, span.badge.bg-gray-500")]
            description = desc.get_text(" ", strip=True)[:400] if desc else ""
            if skills:
                description += " | Skills: " + ", ".join(skills)
            href = a.get("href", "").strip()
            url = href if href.startswith("http") else f"https://www.tecnoempleo.com{href}"
            date_match = _DATE_RE.search(card.get_text(" ", strip=True))
            posted_raw, posted_days_ago = parse_posted_date(date_match.group(0) if date_match else None)
            offers.append(Offer(
                id=start_id + len(offers),
                title=a.get_text(strip=True),
                url=url,
                company=comp.get_text(strip=True) if comp else None,
                location=loc.get_text(strip=True) if loc else None,
                description=description or None,
                source=self.portal_name,
                posted_raw=posted_raw,
                posted_days_ago=posted_days_ago,
            ))
        return offers
