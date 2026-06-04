from idlelib import browser
from pydoc import html
from typing import List
import requests
from bs4 import BeautifulSoup
from models.offer import Offer
from repositories.offer_repository import OfferRepository

BASE = "https://www.tecnoempleo.com/ofertas-trabajo/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "}


class ScraperService:
    """Recoge ofertas de Tecnoempleao (request+BS4, con fallback a PlayWright)"""

    def __init__(self, repo: OfferRepository | None = None):
        self.repo = repo or OfferRepository()

    def scrape(self, query: str = "python") -> List[Offer]:
        html = self._html_requests(query)
        ofertas = self._parse(html)
        if not ofertas:  # fallback infalible
            html = self._html_playwright(query)
            ofertas = self._parse(html)
        return self._guardar(ofertas)

    # --- obtención del HTML ---
    def _html_requests(self, query: str) -> str:
        try:
            r = requests.get(BASE, params={"te": query}, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception:
            return ""

    def _html_playwright(self, query: str) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(f"{BASE}?te={query}", timeout=30000)
            page.wait_for_selector("div.p-3.border.rounded.mb-3.bg-white", timeout=15000)
            html = page.content()
            browser.close()
            return html

    # --- parseo ---
    def _parse(self, html: str) -> List[Offer]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.p-3.border.rounded.mb-3.bg-white")
        ofertas: List[Offer] = []
        base_id = self.repo.next_id()
        for card in cards:
            a = card.select_one("h3 a")
            if not a:
                continue
            comp = card.select_one("a.link-muted")
            loc = card.select_one("span.d-block.d-lg-none b")
            desc = card.select_one("span.hidden-md-down")
            skills = [b.get_text(strip=True)
                      for b in card.select("span.badge.bg-danger, span.badge.bg-gray-500")]
            descripcion = desc.get_text(" ", strip=True)[:400] if desc else ""
            if skills:
                descripcion += " | Skills: " + ", ".join(skills)
            ofertas.append(Offer(
                id=base_id + len(ofertas),
                title=a.get_text(strip=True),
                url=a.get("href", "").strip(),
                company=comp.get_text(strip=True) if comp else None,
                location=loc.get_text(strip=True) if loc else None,
                description=descripcion or None,
            ))
        return ofertas

    # --- guardado con dedupe por URL ---
    def _guardar(self, ofertas: List[Offer]) -> List[Offer]:
        existentes = self.repo.list_all()
        urls = {o.url for o in existentes}
        nuevas = [o for o in ofertas if o.url not in urls]
        if nuevas:
            self.repo.save_all(existentes + nuevas)
        return nuevas
