from models.offer import Offer
from services import scraper_service
from services.scraper_service import ScraperService


class FakeScraper:
    portal_name = "fake"
    results: list[Offer] = []

    def scrape(self, query, location="", start_id=0):
        return [
            Offer(id=start_id + i, title=o.title, url=o.url, source=self.portal_name)
            for i, o in enumerate(self.results)
        ]


class BrokenScraper:
    portal_name = "broken"

    def scrape(self, query, location="", start_id=0):
        raise RuntimeError("portal caído")


def test_scrape_persists_and_assigns_ids(repo, monkeypatch):
    FakeScraper.results = [
        Offer(id=0, title="A", url="https://a.com"),
        Offer(id=0, title="B", url="https://b.com"),
    ]
    monkeypatch.setattr(scraper_service, "SCRAPERS", {"fake": FakeScraper})
    new = ScraperService(repo).scrape(portal="fake")
    assert len(new) == 2
    assert len(repo.list_all()) == 2
    assert repo.next_id() == 3


def test_scrape_dedupes_by_url(repo, sample_offers, monkeypatch):
    FakeScraper.results = [
        Offer(id=0, title="Duplicada", url="https://example.com/1"),  # ya existe
        Offer(id=0, title="Nueva", url="https://nueva.com"),
    ]
    monkeypatch.setattr(scraper_service, "SCRAPERS", {"fake": FakeScraper})
    new = ScraperService(repo).scrape(portal="fake")
    assert [o.title for o in new] == ["Nueva"]
    assert len(repo.list_all()) == 4


def test_broken_scraper_does_not_break_others(repo, monkeypatch):
    FakeScraper.results = [Offer(id=0, title="OK", url="https://ok.com")]
    monkeypatch.setattr(
        scraper_service, "SCRAPERS", {"broken": BrokenScraper, "fake": FakeScraper}
    )
    new = ScraperService(repo).scrape(portal="all")
    assert [o.title for o in new] == ["OK"]


def test_unknown_portal_returns_empty(repo, monkeypatch):
    monkeypatch.setattr(scraper_service, "SCRAPERS", {"fake": FakeScraper})
    assert ScraperService(repo).scrape(portal="noexiste") == []
