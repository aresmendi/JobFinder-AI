import json
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
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, rows: List[dict]) -> None:
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def list_all(self) -> List[Offer]:
        return [Offer(**row) for row in self._read()]

    def get(self, offer_id: int) -> Optional[Offer]:
        return next((o for o in self.list_all() if o.id == offer_id), None)

    def save_all(self, offers: List[Offer]) -> None:
        self._write([o.__dict__ for o in offers])

    def next_id(self) -> int:
        offers = self.list_all()
        return (max((o.id for o in offers), default=0)) + 1
