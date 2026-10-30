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


# --- Stok ---
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


def test_split_names_handles_separators():
    assert repo.split_names("domates, Soğan\nyumurta") == [
        "domates",
        "soğan",
        "yumurta",
    ]
    assert repo.split_names("  ,  ") == []
    assert repo.split_names("") == []


def test_add_pantry_many(session):
    added = repo.add_pantry_many(session, "domates, soğan, domates")
    assert added == ["domates", "soğan"]  # tekrar eden malzeme bir kez eklenir
    assert repo.list_pantry(session) == ["domates", "soğan"]


# --- Alışveriş listesi ---
def test_shopping_is_separate_from_pantry(session):
    repo.add_shopping(session, "süt")
    assert repo.list_shopping(session) == ["süt"]
    assert repo.list_pantry(session) == []


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


def test_shopping_keeps_quantity(session):
    repo.add_shopping(session, "yumurta", 4, "adet")
    item = repo.list_shopping_items(session)[0]
    assert item["quantity"] == 4
    assert item["unit"] == "adet"
    assert item["label"] == "yumurta (4 adet)"


def test_bought_item_moves_to_pantry_with_quantity(session):
    repo.add_shopping(session, "süt", 500, "ml")
    item = repo.list_shopping_items(session)[0]
    repo.add_pantry(session, item["name"], item["quantity"], item["unit"])

    assert repo.list_shopping(session) == []
    pantry_item = repo.list_pantry_items(session)[0]
    assert pantry_item["quantity"] == 500
    assert pantry_item["unit"] == "ml"


# --- Tarifler ---
def test_seed_recipes_loads_once(session, tmp_path):
    data = [
        {
            "id": 1,
            "name": "Menemen",
            "time_min": 15,
            "servings": 2,
            "ingredients": [
                {"name": "yumurta", "quantity": 4, "unit": "adet"},
                {"name": "domates", "quantity": 3, "unit": "adet"},
            ],
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
    assert {i["name"] for i in recipes[0]["ingredients"]} == {"yumurta", "domates"}
    assert recipes[0]["steps"] == ["Pişir.", "Ye."]


def test_seed_recipes_keeps_quantities(session, tmp_path):
    data = [
        {
            "id": 1,
            "name": "Omlet",
            "time_min": 10,
            "servings": 1,
            "ingredients": [{"name": "yumurta", "quantity": 2, "unit": "adet"}],
            "steps": ["Pişir."],
        }
    ]
    path = tmp_path / "recipes.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    repo.seed_recipes_if_empty(session, path)

    ingredient = repo.list_recipes(session)[0]["ingredients"][0]
    assert ingredient["quantity"] == 2
    assert ingredient["unit"] == "adet"
    assert ingredient["label"] == "yumurta (2 adet)"