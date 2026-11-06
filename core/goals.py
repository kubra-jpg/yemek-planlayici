"""Beslenme hedefleri: kalori / protein filtresi ve besin değerine göre sıralama."""

from core.nutrition import recipe_nutrition


def filter_by_goals(results, max_kcal=None, min_protein=None):
    """match_recipes sonuçlarını kişi başı değerlere göre süzer.

    max_kcal: kişi başı en fazla kcal; min_protein: kişi başı en az protein (g).
    """
    kept = []
    for r in results:
        n = recipe_nutrition(r["recipe"])
        if max_kcal is not None and n["per_serving"] > max_kcal:
            continue
        if min_protein is not None and n["protein"] < min_protein:
            continue
        kept.append(r)
    return kept


def sort_by_nutrition(results, by):
    """'kcal': az kalorili önce, 'protein': çok proteinli önce. Eşitlikte eşleşme oranı."""
    if by == "kcal":
        key = lambda r: (recipe_nutrition(r["recipe"])["per_serving"], -r["ratio"])
    elif by == "protein":
        key = lambda r: (-recipe_nutrition(r["recipe"])["protein"], -r["ratio"])
    else:
        raise ValueError(f"Bilinmeyen sıralama: {by}")
    return sorted(results, key=key)
