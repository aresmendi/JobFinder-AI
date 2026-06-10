from pydantic import BaseModel
from typing import Optional, Literal

#Equivalente a los DTO
class OfferBase(BaseModel):
    title: str
    url: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

class OfferCreate(OfferBase):
    pass

class OfferResponse(OfferBase):
    id: int
    score: Optional[int] = None
    score_reason: Optional[str] = None
    source: Optional[str] = None
    status: str = "nueva"
    matched_keywords: Optional[list[str]] = None
    missing_keywords: Optional[list[str]] = None

class OfferStatusUpdate(BaseModel):
    status: Literal["nueva", "aplicada", "descartada"]