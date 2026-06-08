from fastapi import APIRouter, HTTPException
from typing import List
from repositories.offer_repository import OfferRepository
from schemas.offer import OfferResponse
from services.scraper_service import ScraperService

router = APIRouter(prefix="/offers", tags=["offers"])
repo = OfferRepository()

@router.get("", response_model=List[OfferResponse])
def list_offers():
    return repo.list_all()

@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: int):
    offer = repo.get(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return offer

@router.post("/scrape", response_model=List[OfferResponse])
def scrape_offers(
    q: str = "python",
    location: str = "",
    portal: str = "all",
):
    """
    Scrapea ofertas de uno o todos los portales.
    - portal: all | tecnoempleo | infojobs | indeed | linkedin
    - location: ciudad o país (ej. "Valencia", "España")
    """
    return ScraperService(repo).scrape(query=q, location=location, portal=portal)
