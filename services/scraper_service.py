from typing import List
from models.offer import Offer
from repositories.offer_repository import OfferRepository

class ScraperService:
    """Lógica de negocio: Recoge ofertas y las guarda"""
    def __init__(self, repo: OfferRepository | None = None):
        self.repo = repo or OfferRepository()

    def scrape(self)->List[Offer]:
        #TODO: scraping real, de momento son datos de ejemplo
        sample = [
            Offer(
                id=self.repo.next_id(),
                title="Python Developer Junior (FastAPI)",
                company="ACME Tech",
                location="Remoto",
                url="https://example.com/oferta/1",
                description="Buscamos junior con Python, FastAPI y ganas de IA.",
            ),
        ]
        offers = self.repo.list_all() + sample
        self.repo.save_all(offers)
        return sample
