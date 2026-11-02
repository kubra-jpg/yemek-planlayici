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


def sample(name="Menemen"):
    return {
        "name": name,
        "time_min": 15,
        "servings": 2,
        "ingredients": [
            {"name": "yumurta", "quantity": 4, "unit": "adet"},
            {"name": "Domates", "quantity": 3, "unit": "adet"},
        ],
        "steps": "Kavur.\n\nPişir.",
    }


def test_create_recipe(session):
    recipe_id = repo.save_recipe(session, sample())
    recipe = repo.get_recipe(session, recipe_id)
    assert recipe["name"] == "Menemen"
    assert {i["name"] for i in recipe["ingredients"]} == {"yumurta", "domates"}
    assert recipe["steps"] == ["Kavur.", "Pişir."]  # boş satır atlandı


def test_update_replaces_ingredients(session):
    recipe_id = repo.save_recipe(session, sample())
    data = sample("Menemen (az yumurtalı)")
    data["ingredients"] = [{"name": "yumurta", "quantity": 2, "unit": "adet"}]
    repo.save_recipe(session, data, recipe_id)

    recipe = repo.get_recipe(session, recipe_id)
    assert recipe["name"] == "Menemen (az yumurtalı)"
    assert len(recipe["ingredients"]) == 1
    assert recipe["ingredients"][0]["quantity"] == 2


def test_duplicate_name_rejected(session):
    repo.save_recipe(session, sample())
    with pytest.raises(ValueError):
        repo.save_recipe(session, sample())


def test_empty_name_rejected(session):
    with pytest.raises(ValueError):
        repo.save_recipe(session, sample("   "))


def test_recipe_needs_ingredients(session):
    data = sample()
    data["ingredients"] = [{"name": "", "quantity": None, "unit": None}]
    with pytest.raises(ValueError):
        repo.save_recipe(session, data)


def test_bad_quantities_become_none(session):
    data = sample()
    data["ingredients"] = [
        {"name": "tuz", "quantity": float("nan"), "unit": "çay kaşığı"},
        {"name": "yağ", "quantity": -1, "unit": ""},
        {"name": "tuz", "quantity": 5, "unit": "g"},  # tekrar eden, atlanır
    ]
    recipe_id = repo.save_recipe(session, data)
    ingredients = repo.get_recipe(session, recipe_id)["ingredients"]
    assert len(ingredients) == 2
    assert all(i["quantity"] is None for i in ingredients)


def test_delete_recipe(session):
    recipe_id = repo.save_recipe(session, sample())
    assert repo.delete_recipe(session, recipe_id) is True
    assert repo.get_recipe(session, recipe_id) is None
    assert repo.delete_recipe(session, recipe_id) is False