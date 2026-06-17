from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from bs4.element import Tag
from models.offer import Offer
from services.date_utils import find_posted_phrase, parse_posted_date

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


class BasePortalScraper(ABC):
    """Interfaz común para todos los scrapers de portales de empleo."""

    @property
    @abstractmethod
    def portal_name(self) -> str: ...

    @abstractmethod
    def scrape(self, query: str, location: str = "", start_id: int = 0) -> List[Offer]:
        """Devuelve las ofertas encontradas. start_id evita colisiones de id entre portales."""
        ...

    def _launch_chromium(self, p):
        """Usa el Chromium propio de Playwright si está instalado; si no (p. ej.
        en sistemas donde `playwright install chromium` no está soportado),
        cae al Google Chrome ya instalado en el sistema."""
        try:
            return p.chromium.launch(headless=True)
        except Exception:
            return p.chromium.launch(headless=True, channel="chrome")

    def _playwright_html(self, url: str, wait_selector: str, timeout: int = 20000) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = self._launch_chromium(p)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, timeout=30000)
            try:
                page.wait_for_selector(wait_selector, timeout=timeout)
            except Exception:
                pass
            html = page.content()
            browser.close()
            return html

    def _extract_posted(self, card: Tag) -> Tuple[Optional[str], Optional[int]]:
        """Busca una fecha de publicación dentro de la card: primero en elementos
        candidatos típicos (time, datetime, clases con "date"), si no la encuentra
        cae a buscar el patrón en todo el texto de la card."""
        candidate = card.select_one("time, [datetime], [class*='date'], [class*='Date']")
        if candidate is not None:
            text = candidate.get("datetime") or candidate.get_text(" ", strip=True)
            raw, days_ago = parse_posted_date(text)
            if days_ago is not None:
                return raw, days_ago
        phrase = find_posted_phrase(card.get_text(" ", strip=True))
        if phrase is None:
            return None, None
        return parse_posted_date(phrase)
