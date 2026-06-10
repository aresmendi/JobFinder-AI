import pytest

from services import cv_service
from services.cv_service import cargar_cv, buscar_cv


def test_cargar_cv_txt(tmp_path):
    f = tmp_path / "cv.txt"
    f.write_text("Python, FastAPI, SQL", encoding="utf-8")
    assert cargar_cv(str(f)) == "Python, FastAPI, SQL"


def test_cargar_cv_missing_file(tmp_path):
    assert cargar_cv(str(tmp_path / "no-existe.txt")) == "CV no disponible"


def test_cargar_cv_unsupported_extension(tmp_path):
    f = tmp_path / "cv.odt"
    f.write_text("x")
    with pytest.raises(ValueError):
        cargar_cv(str(f))


@pytest.fixture
def fake_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(cv_service, "BASE_DIR", tmp_path)
    data = tmp_path / "data"
    data.mkdir()
    return data


def test_buscar_cv_exact_name_priority(fake_data_dir):
    (fake_data_dir / "cv.txt").write_text("txt")
    (fake_data_dir / "cv.pdf").write_text("pdf")
    assert buscar_cv().endswith("cv.txt")  # .txt va primero en la prioridad


def test_buscar_cv_wildcard(fake_data_dir):
    (fake_data_dir / "cv_ares.pdf").write_text("pdf")
    assert buscar_cv().endswith("cv_ares.pdf")


def test_buscar_cv_none(fake_data_dir):
    assert buscar_cv() is None
