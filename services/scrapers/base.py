from abc import ABC, abstractmethod
from typing import List
from models.offer import Offer

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

    def _playwright_html(self, url: str, wait_selector: str, timeout: int = 20000) -> str:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, timeout=30000)
            try:
                page.wait_for_selector(wait_selector, timeout=timeout)
            except Exception:
                pass
            html = page.content()
            browser.close()
            return html
