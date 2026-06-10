def test_list_offers_sorted_by_score(client, sample_offers):
    r = client.get("/offers")
    assert r.status_code == 200
    data = r.json()
    assert [o["id"] for o in data] == [1, 2, 3]  # 85, 40, sin score al final


def test_list_offers_filter_status(client, sample_offers):
    r = client.get("/offers", params={"status": "descartada"})
    assert [o["id"] for o in r.json()] == [2]


def test_list_offers_filter_source(client, sample_offers):
    r = client.get("/offers", params={"source": "tecnoempleo"})
    assert [o["id"] for o in r.json()] == [1]


def test_list_offers_filter_min_score(client, sample_offers):
    r = client.get("/offers", params={"min_score": 50})
    assert [o["id"] for o in r.json()] == [1]


def test_get_offer(client, sample_offers):
    r = client.get("/offers/1")
    assert r.status_code == 200
    assert r.json()["title"] == "Backend Python"
    assert r.json()["status"] == "nueva"


def test_get_offer_404(client, sample_offers):
    assert client.get("/offers/999").status_code == 404


def test_patch_status(client, repo, sample_offers):
    r = client.patch("/offers/1/status", json={"status": "aplicada"})
    assert r.status_code == 200
    assert r.json()["status"] == "aplicada"
    assert repo.get(1).status == "aplicada"


def test_patch_status_invalid_value(client, sample_offers):
    r = client.patch("/offers/1/status", json={"status": "pendiente"})
    assert r.status_code == 422


def test_patch_status_404(client, sample_offers):
    r = client.patch("/offers/999/status", json={"status": "aplicada"})
    assert r.status_code == 404


def test_delete_offer(client, repo, sample_offers):
    assert client.delete("/offers/2").status_code == 204
    assert repo.get(2) is None
    assert client.delete("/offers/2").status_code == 404


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_frontend_served_at_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "html" in r.headers["content-type"]
