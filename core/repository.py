import json
from pathlib import Path

from sqlalchemy import select

from core.matcher import normalize
from core.models import Ingredient, PantryItem, Recipe, RecipeIngredient, ShoppingItem


# --- Malzeme ---
def get_or_create_ingredient(session, name):
    name = normalize(name)
    ingredient = session.scalar(select(Ingredient).where(Ingredient.name == name))
    if ingredient is None:
        ingredient = Ingredient(name=name)
        session.add(ingredient)
        session.flush()
    return ingredient


# --- Stok ve alışveriş listesi için ortak yardımcılar ---
def _list_names(session, model):
    stmt = (
        select(Ingredient.name)
        .join(model, model.ingredient_id == Ingredient.id)
        .order_by(Ingredient.name)
    )
    return list(session.scalars(stmt))


def _add(session, model, name):
    name = normalize(name)
    if not name:
        return False
    ingredient = get_or_create_ingredient(session, name)
    exists = session.scalar(select(model).where(model.ingredient_id == ingredient.id))
    if exists:
        return False
    session.add(model(ingredient_id=ingredient.id))
    return True


def _remove(session, model, name):
    ingredient = session.scalar(
        select(Ingredient).where(Ingredient.name == normalize(name))
    )
    if ingredient is None:
        return False
    item = session.scalar(select(model).where(model.ingredient_id == ingredient.id))
    if item is None:
        return False
    session.delete(item)
    return True


# --- Stok ---
def list_pantry(session):
    return _list_names(session, PantryItem)


def add_pantry(session, name):
    """Stoğa ekler; malzeme alışveriş listesindeyse oradan çıkarır."""
    added = _add(session, PantryItem, name)
    remove_shopping(session, name)
    return added


def remove_pantry(session, name):
    return _remove(session, PantryItem, name)


# --- Alışveriş listesi ---
def list_shopping(session):
    return _list_names(session, ShoppingItem)


def add_shopping(session, name):
    """Alışveriş listesine ekler; malzeme zaten evdeyse eklemez."""
    if normalize(name) in list_pantry(session):
        return False
    return _add(session, ShoppingItem, name)


def remove_shopping(session, name):
    return _remove(session, ShoppingItem, name)


# --- Tarifler ---
def recipe_to_dict(recipe):
    """Veritabanı kaydını, matcher'ın beklediği sözlük biçimine çevirir."""
    return {
        "id": recipe.id,
        "name": recipe.name,
        "time_min": recipe.time_min,
        "servings": recipe.servings,
        "ingredients": [ri.ingredient.name for ri in recipe.ingredients],
        "steps": recipe.steps.split("\n") if recipe.steps else [],
        "is_favorite": recipe.is_favorite,
    }


def list_recipes(session):
    recipes = session.scalars(select(Recipe).order_by(Recipe.id))
    return [recipe_to_dict(r) for r in recipes]


def seed_recipes_if_empty(session, json_path):
    """Tarif tablosu boşsa JSON dosyasındaki tarifleri yükler. Yüklenen sayıyı döndürür."""
    if session.scalar(select(Recipe.id).limit(1)) is not None:
        return 0

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    for item in data:
        recipe = Recipe(
            name=item["name"],
            time_min=item["time_min"],
            servings=item["servings"],
            steps="\n".join(item["steps"]),
        )
        for ingredient_name in item["ingredients"]:
            ingredient = get_or_create_ingredient(session, ingredient_name)
            recipe.ingredients.append(RecipeIngredient(ingredient=ingredient))
        session.add(recipe)
    return len(data)