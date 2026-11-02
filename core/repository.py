import json
from pathlib import Path

from sqlalchemy import select

from core.matcher import normalize
from core.models import Ingredient, PantryItem, Recipe, RecipeIngredient, ShoppingItem
from core.units import format_amount


# --- Malzeme ---
def get_or_create_ingredient(session, name):
    name = normalize(name)
    ingredient = session.scalar(select(Ingredient).where(Ingredient.name == name))
    if ingredient is None:
        ingredient = Ingredient(name=name)
        session.add(ingredient)
        session.flush()
    return ingredient


def split_names(text):
    """Virgül, noktalı virgül veya satır sonuyla ayrılmış metni malzeme adlarına böler."""
    if not text:
        return []
    for separator in (";", "\n"):
        text = text.replace(separator, ",")
    names = [normalize(part) for part in text.split(",")]
    return [name for name in names if name]


# --- Stok ve alışveriş listesi için ortak yardımcılar ---
def _list_names(session, model):
    stmt = (
        select(Ingredient.name)
        .join(model, model.ingredient_id == Ingredient.id)
        .order_by(Ingredient.name)
    )
    return list(session.scalars(stmt))


def _list_items(session, model):
    """Miktar ve birimle birlikte liste döndürür."""
    stmt = (
        select(Ingredient.name, model.quantity, model.unit)
        .join(model, model.ingredient_id == Ingredient.id)
        .order_by(Ingredient.name)
    )
    return [
        {
            "name": name,
            "quantity": quantity,
            "unit": unit,
            "label": f"{name} ({format_amount(quantity, unit)})" if quantity else name,
        }
        for name, quantity, unit in session.execute(stmt)
    ]


def _set_amount(session, model, name, quantity, unit):
    """Var olan kaydın miktarını günceller."""
    ingredient = session.scalar(
        select(Ingredient).where(Ingredient.name == normalize(name))
    )
    if ingredient is None:
        return False
    item = session.scalar(select(model).where(model.ingredient_id == ingredient.id))
    if item is None:
        return False
    item.quantity = quantity
    item.unit = unit
    return True


def _add(session, model, name):
    name = normalize(name)
    if not name:
        return False
    ingredient = get_or_create_ingredient(session, name)
    exists = session.scalar(select(model).where(model.ingredient_id == ingredient.id))
    if exists:
        return False
    session.add(model(ingredient_id=ingredient.id))
    session.flush()
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


def list_pantry_items(session):
    return _list_items(session, PantryItem)


def pantry_as_dict(session):
    """matcher için: {ad: (miktar, birim)}"""
    return {
        item["name"]: (item["quantity"], item["unit"])
        for item in _list_items(session, PantryItem)
    }


def add_pantry(session, name, quantity=None, unit=None):
    """Stoğa ekler; malzeme alışveriş listesindeyse oradan çıkarır."""
    added = _add(session, PantryItem, name)
    if quantity is not None:
        _set_amount(session, PantryItem, name, quantity, unit)
    remove_shopping(session, name)
    return added


def add_pantry_many(session, text):
    """Metindeki tüm malzemeleri stoğa ekler, eklenen adları döndürür."""
    added = []
    for name in split_names(text):
        if add_pantry(session, name):
            added.append(name)
    return added


def set_pantry_amount(session, name, quantity, unit):
    return _set_amount(session, PantryItem, name, quantity, unit)


def remove_pantry(session, name):
    return _remove(session, PantryItem, name)


# --- Alışveriş listesi ---
def list_shopping(session):
    return _list_names(session, ShoppingItem)


def list_shopping_items(session):
    return _list_items(session, ShoppingItem)


def add_shopping(session, name, quantity=None, unit=None):
    """Alışveriş listesine ekler; malzeme zaten evdeyse eklemez."""
    if normalize(name) in list_pantry(session):
        return False
    added = _add(session, ShoppingItem, name)
    if added and quantity is not None:
        _set_amount(session, ShoppingItem, name, quantity, unit)
    return added


def add_shopping_many(session, items):
    """Malzemeleri alışveriş listesine ekler.

    items: adlardan oluşan liste ya da {"name","quantity","unit"} sözlükleri.
    """
    added = []
    for item in items:
        if isinstance(item, dict):
            ok = add_shopping(
                session, item["name"], item.get("quantity"), item.get("unit")
            )
            name = item["name"]
        else:
            ok = add_shopping(session, item)
            name = item
        if ok:
            added.append(name)
    return added


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
        "ingredients": [
            {
                "name": ri.ingredient.name,
                "quantity": ri.quantity,
                "unit": ri.unit,
                "label": f"{ri.ingredient.name} ({format_amount(ri.quantity, ri.unit)})"
                if ri.quantity
                else ri.ingredient.name,
            }
            for ri in recipe.ingredients
        ],
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
        for raw in item["ingredients"]:
            if isinstance(raw, dict):
                name = raw["name"]
                quantity = raw.get("quantity")
                unit = raw.get("unit")
            else:
                name, quantity, unit = raw, None, None
            ingredient = get_or_create_ingredient(session, name)
            recipe.ingredients.append(
                RecipeIngredient(ingredient=ingredient, quantity=quantity, unit=unit)
            )
        session.add(recipe)

    session.flush()
    return len(data)

# --- Tarif yönetimi ---
def get_recipe(session, recipe_id):
    recipe = session.get(Recipe, recipe_id)
    return recipe_to_dict(recipe) if recipe else None


def _clean_ingredients(rows):
    """Tablodan gelen malzeme satırlarını temizler.

    Boş satırları ve tekrar eden malzemeleri atar, geçersiz miktarı None yapar.
    (ad, miktar, birim) üçlülerinden oluşan liste döndürür.
    """
    cleaned, seen = [], set()
    for row in rows:
        raw_name = row.get("name")
        if not isinstance(raw_name, str):
            continue
        ing_name = normalize(raw_name)
        if not ing_name or ing_name in seen:
            continue
        seen.add(ing_name)

        quantity = row.get("quantity")
        try:
            quantity = float(quantity) if quantity is not None else None
        except (TypeError, ValueError):
            quantity = None
        # Boş hücre NaN gelir; NaN kendisine eşit olmayan tek sayıdır
        if quantity is not None and (quantity != quantity or quantity <= 0):
            quantity = None

        unit = row.get("unit")
        unit = unit.strip() if isinstance(unit, str) and unit.strip() else None

        cleaned.append((ing_name, quantity, unit))
    return cleaned


def save_recipe(session, data, recipe_id=None):
    """Yeni tarif oluşturur (recipe_id=None) ya da var olanı günceller.

    Tarifin id'sini döndürür. Veri hatalıysa ValueError fırlatır.
    """
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("Tarif adı boş olamaz.")

    ingredients = _clean_ingredients(data.get("ingredients") or [])
    if not ingredients:
        raise ValueError("En az bir malzeme eklemelisin.")

    same_name = session.scalar(select(Recipe).where(Recipe.name == name))
    if same_name is not None and same_name.id != recipe_id:
        raise ValueError(f"'{name}' adında bir tarif zaten var.")

    if recipe_id is None:
        recipe = Recipe(name=name)
        session.add(recipe)
    else:
        recipe = session.get(Recipe, recipe_id)
        if recipe is None:
            raise ValueError("Tarif bulunamadı.")
        recipe.name = name

    recipe.time_min = int(data.get("time_min") or 0)
    recipe.servings = int(data.get("servings") or 1)

    steps = data.get("steps") or ""
    if isinstance(steps, list):
        steps = "\n".join(steps)
    recipe.steps = "\n".join(s.strip() for s in steps.split("\n") if s.strip())

    # Eski malzemeleri silip yenilerini ekle
    recipe.ingredients.clear()
    session.flush()
    for ing_name, quantity, unit in ingredients:
        ingredient = get_or_create_ingredient(session, ing_name)
        recipe.ingredients.append(
            RecipeIngredient(ingredient=ingredient, quantity=quantity, unit=unit)
        )
    session.flush()
    return recipe.id


def delete_recipe(session, recipe_id):
    recipe = session.get(Recipe, recipe_id)
    if recipe is None:
        return False
    session.delete(recipe)
    session.flush()
    return True

def import_recipes(session, json_path):
    """Dosyadaki tariflerden veritabanında olmayanları ekler; var olanlara dokunmaz.

    Eklenen tarif sayısını döndürür.
    """
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    existing = set(session.scalars(select(Recipe.name)))
    added = 0
    for item in data:
        if item["name"] in existing:
            continue
        save_recipe(session, item)
        existing.add(item["name"])
        added += 1
    return added
def toggle_favorite(session, recipe_id):
    """Tarifin favori durumunu tersine çevirir, yeni durumu döndürür."""
    recipe = session.get(Recipe, recipe_id)
    if recipe is None:
        return None
    recipe.is_favorite = not recipe.is_favorite
    session.flush()
    return recipe.is_favorite