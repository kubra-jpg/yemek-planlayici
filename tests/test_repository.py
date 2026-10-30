import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core import repository as repo
from core.models import Base


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as s:
        yield s


def test_add_and_list_pantry(session):
    assert repo.add_pantry(session, " Domates ") is True
    assert repo.list_pantry(session) == ["domates"]


def test_pantry_has_no_duplicates(session):
    repo.add_pantry(session, "domates")
    assert repo.add_pantry(session, "DOMATES") is False
    assert repo.list_pantry(session) == ["domates"]


def test_empty_name_is_ignored(session):
    assert repo.add_pantry(session, "   ") is False
    assert repo.list_pantry(session) == []


def test_remove_pantry(session):
    repo.add_pantry(session, "yumurta")
    assert repo.remove_pantry(session, "yumurta") is True
    assert repo.list_pantry(session) == []


def test_remove_missing_item_returns_false(session):
    assert repo.remove_pantry(session, "yok") is False


def test_shopping_is_separate_from_pantry(session):
    repo.add_shopping(session, "süt")
    assert repo.list_shopping(session) == ["süt"]
    assert repo.list_pantry(session) == []


def test_seed_recipes_loads_once(session, tmp_path):
    data = [
        {
            "id": 1,
            "name": "Menemen",
            "time_min": 15,
            "servings": 2,
            "ingredients": ["yumurta", "domates"],
            "steps": ["Pişir.", "Ye."],
        }
    ]
    path = tmp_path / "recipes.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    assert repo.seed_recipes_if_empty(session, path) == 1
    assert repo.seed_recipes_if_empty(session, path) == 0  # ikinci çağrıda yüklemez

    recipes = repo.list_recipes(session)
    assert len(recipes) == 1
    assert recipes[0]["name"] == "Menemen"
    assert set(recipes[0]["ingredients"]) == {"yumurta", "domates"}
    assert recipes[0]["steps"] == ["Pişir.", "Ye."]

def test_adding_to_pantry_removes_from_shopping(session):
    repo.add_shopping(session, "süt")
    assert repo.list_shopping(session) == ["süt"]
    repo.add_pantry(session, "süt")
    assert repo.list_shopping(session) == []
    assert repo.list_pantry(session) == ["süt"]


def test_item_in_pantry_is_not_added_to_shopping(session):
    repo.add_pantry(session, "domates")
    assert repo.add_shopping(session, "DOMATES") is False
    assert repo.list_shopping(session) == []