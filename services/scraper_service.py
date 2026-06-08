from typing import List, Literal
from models.offer import Offer
from repositories.offer_repository import OfferRepository
from services.scrapers import SCRAPERS

PortalName = Literal["all", "tecnoempleo", "infojobs", "indeed", "linkedin"]


class ScraperService:
    """Orquesta uno o varios scrapers de portales y persiste las ofertas deduplicadas."""

    def __init__(self, repo: OfferRepository | None = None):
        self.repo = repo or OfferRepository()

    def scrape(
        self,
        query: str = "python",
        location: str = "",
        portal: PortalName = "all",
    ) -> List[Offer]:
        portals = list(SCRAPERS.keys()) if portal == "all" else [portal]
        existing = self.repo.list_all()
        seen_urls = {o.url for o in existing}
        next_id = self.repo.next_id()

        new_offers: List[Offer] = []
        for name in portals:
            scraper_cls = SCRAPERS.get(name)
            if not scraper_cls:
                continue
            try:
                found = scraper_cls().scrape(query, location, start_id=next_id + len(new_offers))
                for offer in found:
                    if offer.url not in seen_urls:
                        seen_urls.add(offer.url)
                        new_offers.append(offer)
            except Exception as exc:
                print(f"[scraper:{name}] error — {exc}")

        if new_offers:
            self.repo.save_all(existing + new_offers)
        return new_offers
