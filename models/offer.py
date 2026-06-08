from dataclasses import dataclass, field
from typing import Optional

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