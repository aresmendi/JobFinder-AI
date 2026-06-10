from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from core.deps import get_repo
from repositories.offer_repository import OfferRepository
from schemas.offer import OfferResponse, OfferStatusUpdate
from services.scraper_service import ScraperService

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("", response_model=List[OfferResponse])
def list_offers(
    status: Optional[str] = Query(default=None, description="nueva | aplicada | descartada"),
    source: Optional[str] = Query(default=None, description="tecnoempleo | infojobs | indeed | linkedin"),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    repo: OfferRepository = Depends(get_repo),
):
    """Lista ofertas, ordenadas por score (las sin puntuar al final). Admite filtros."""
    offers = repo.list_all()
    if status:
        offers = [o for o in offers if o.status == status]
    if source:
        offers = [o for o in offers if o.source == source]
    if min_score is not None:
        offers = [o for o in offers if o.score is not None and o.score >= min_score]
    return sorted(offers, key=lambda o: (o.score is None, -(o.score or 0)))


@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: int, repo: OfferRepository = Depends(get_repo)):
    offer = repo.get(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    return offer


@router.patch("/{offer_id}/status", response_model=OfferResponse)
def update_status(
    offer_id: int,
    payload: OfferStatusUpdate,
    repo: OfferRepository = Depends(get_repo),
):
    """Marca una oferta como aplicada/descartada/nueva (sección Mis Aplicaciones)."""
    offer = repo.get(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")
    offer.status = payload.status
    return repo.update(offer)


@router.delete("/{offer_id}", status_code=204)
def delete_offer(offer_id: int, repo: OfferRepository = Depends(get_repo)):
    if not repo.delete(offer_id):
        raise HTTPException(status_code=404, detail="Oferta no encontrada")


@router.post("/scrape", response_model=List[OfferResponse])
def scrape_offers(
    q: str = "python",
    location: str = "",
    portal: str = "all",
    repo: OfferRepository = Depends(get_repo),
):
    """
    Scrapea ofertas de uno o todos los portales.
    - portal: all | tecnoempleo | infojobs | indeed | linkedin
    - location: ciudad o país (ej. "Valencia", "España")
    """
    return ScraperService(repo).scrape(query=q, location=location, portal=portal)
