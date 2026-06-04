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
    score: Optional[int] = None #Match de 0 a 100 (Lo rellena el LLM)
    score_reason: Optional[str] = None #Por que del match (LLM)
    matched_keywords: Optional[list] = None
    missing_keywords: Optional[list] = None