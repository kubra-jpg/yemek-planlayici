import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core import repository as repo
from core.matcher import match_recipe
from core.models import Base

BOILED_EGG = {
    "id": 1,
    "name": "Haşlanmış yumurta",
    "ingredients": [
        {"name": "yumurta", "quantity": 2, "unit": "adet"},
        {"name": "tuz", "quantity": 1, "unit": "çay kaşığı"},
    ],
}


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as s:
        yield s


# --- Eşleştirme ---
def test_without_staples_salt_is_missing():
    result = match_recipe({"yumurta": (6, "adet")}, BOILED_EGG)
    assert result["ratio"] == 0.5
    assert [m["name"] for m in result["missing"]] == ["tuz"]


def test_staple_is_not_counted():
    result = match_recipe({"yumurta": (6, "adet")}, BOILED_EGG, staples=["tuz"])
    assert result["ratio"] == 1
    assert result["missing"] == []
    assert result["staples"] == ["tuz"]


def test_staples_alone_do_not_create_a_match():
    result = match_recipe({}, BOILED_EGG, staples=["tuz"])
    assert result["ratio"] == 0
    assert [m["name"] for m in result["missing"]] == ["yumurta"]


# --- Veritabanı ---
def test_set_and_list_staples(session):
    repo.set_staples(session, ["Tuz", "yağ", "tuz", "  "])
    assert repo.list_staples(session) == ["tuz", "yağ"]


def test_set_staples_replaces_previous(session):
    repo.set_staples(session, ["tuz", "yağ"])
    repo.set_staples(session, ["karabiber"])
    assert repo.list_staples(session) == ["karabiber"]