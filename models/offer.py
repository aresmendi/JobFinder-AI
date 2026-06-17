from dataclasses import dataclass, field
from typing import Optional

# Estados del ciclo de vida de una oferta (sección "Mis Aplicaciones")
OFFER_STATUSES = ("nueva", "aplicada", "descartada")


@dataclass
class Offer:
    """Entidad de dominio"""
    id: int
    title: str
    url: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    score: Optional[int] = None
    score_reason: Optional[str] = None
    matched_keywords: Optional[list] = None
    missing_keywords: Optional[list] = None
    source: Optional[str] = None  # portal de origen: tecnoempleo, infojobs, indeed, linkedin
    status: str = "nueva"  # nueva | aplicada | descartada
    posted_raw: Optional[str] = None  # texto de fecha tal cual aparece en el portal
    posted_days_ago: Optional[int] = None  # días transcurridos desde la publicación, ya parseado