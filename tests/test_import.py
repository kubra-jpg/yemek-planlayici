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


def write_json(tmp_path, data):
    path = tmp_path / "recipes.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def recipe(name):
    return {
        "name": name,
        "time_min": 10,
        "servings": 1,
        "ingredients": [{"name": "balık", "quantity": 500, "unit": "g"}],
        "steps": ["Pişir."],
    }


def test_import_adds_only_new_recipes(session, tmp_path):
    repo.save_recipe(session, recipe("Fırında balık"))
    path = write_json(tmp_path, [recipe("Fırında balık"), recipe("Tavada balık")])

    assert repo.import_recipes(session, path) == 1
    assert repo.import_recipes(session, path) == 0  # ikinci kez eklemez
    assert len(repo.list_recipes(session)) == 2


def test_import_keeps_pantry(session, tmp_path):
    repo.add_pantry(session, "balık", 1, "kg")
    repo.import_recipes(session, write_json(tmp_path, [recipe("Tavada balık")]))
    assert repo.list_pantry(session) == ["balık"]


def test_project_recipe_file_is_valid(session):
    """Projedeki gerçek recipes.json sorunsuz yüklenebilmeli."""
    added = repo.import_recipes(session, "data/recipes.json")
    assert added >= 50