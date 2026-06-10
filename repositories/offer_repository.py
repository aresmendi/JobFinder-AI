import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from core.config import settings
from models.offer import Offer


class OfferRepository:
    """Acceso a datos. Ahora sobre JSON, después BD."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or settings.data_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> List[dict]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, rows: List[dict]) -> None:
        # Escritura atómica: si el proceso muere a mitad, el JSON original queda intacto
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def list_all(self) -> List[Offer]:
        return [Offer(**row) for row in self._read()]

    def get(self, offer_id: int) -> Optional[Offer]:
        return next((o for o in self.list_all() if o.id == offer_id), None)

    def save_all(self, offers: List[Offer]) -> None:
        self._write([o.__dict__ for o in offers])

    def update(self, offer: Offer) -> Offer:
        """Reemplaza la oferta con el mismo id y persiste."""
        offers = self.list_all()
        for i, o in enumerate(offers):
            if o.id == offer.id:
                offers[i] = offer
                break
        else:
            offers.append(offer)
        self.save_all(offers)
        return offer

    def delete(self, offer_id: int) -> bool:
        offers = self.list_all()
        remaining = [o for o in offers if o.id != offer_id]
        if len(remaining) == len(offers):
            return False
        self.save_all(remaining)
        return True

    def next_id(self) -> int:
        offers = self.list_all()
        return (max((o.id for o in offers), default=0)) + 1
