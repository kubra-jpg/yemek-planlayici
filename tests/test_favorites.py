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


def test_toggle_favorite(session):
    recipe_id = repo.save_recipe(
        session,
        {
            "name": "Omlet",
            "ingredients": [{"name": "yumurta", "quantity": 2, "unit": "adet"}],
            "steps": "Pişir.",
        },
    )
    assert repo.get_recipe(session, recipe_id)["is_favorite"] is False
    assert repo.toggle_favorite(session, recipe_id) is True
    assert repo.get_recipe(session, recipe_id)["is_favorite"] is True
    assert repo.toggle_favorite(session, recipe_id) is False


def test_toggle_missing_recipe(session):
    assert repo.toggle_favorite(session, 999) is None