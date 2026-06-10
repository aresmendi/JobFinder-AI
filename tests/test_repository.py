import json

from models.offer import Offer
from repositories.offer_repository import OfferRepository


def test_init_creates_empty_file(tmp_path):
    path = tmp_path / "sub" / "offers.json"
    repo = OfferRepository(path=str(path))
    assert path.exists()
    assert repo.list_all() == []


def test_empty_file_returns_empty_list(tmp_path):
    path = tmp_path / "offers.json"
    path.write_text("")
    repo = OfferRepository(path=str(path))
    assert repo.list_all() == []


def test_save_and_list_roundtrip(repo, sample_offers):
    offers = repo.list_all()
    assert len(offers) == 3
    assert offers[0].title == "Backend Python"
    assert offers[0].score == 85


def test_old_rows_without_status_get_default(tmp_path):
    # Compatibilidad: JSON antiguo sin el campo status
    path = tmp_path / "offers.json"
    path.write_text(json.dumps([{"id": 1, "title": "X", "url": "https://x.com"}]))
    repo = OfferRepository(path=str(path))
    assert repo.list_all()[0].status == "nueva"


def test_get_existing_and_missing(repo, sample_offers):
    assert repo.get(2).company == "Globex"
    assert repo.get(999) is None


def test_update_replaces_offer(repo, sample_offers):
    offer = repo.get(1)
    offer.status = "aplicada"
    repo.update(offer)
    assert repo.get(1).status == "aplicada"
    assert len(repo.list_all()) == 3


def test_delete(repo, sample_offers):
    assert repo.delete(2) is True
    assert repo.get(2) is None
    assert len(repo.list_all()) == 2
    assert repo.delete(999) is False


def test_next_id(repo, sample_offers):
    assert repo.next_id() == 4
    repo.save_all([])
    assert repo.next_id() == 1


def test_write_is_valid_json_after_save(repo, sample_offers):
    raw = json.loads(repo.path.read_text(encoding="utf-8"))
    assert isinstance(raw, list) and len(raw) == 3
    # No deben quedar temporales de la escritura atómica
    assert list(repo.path.parent.glob("*.tmp")) == []
