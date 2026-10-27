def normalize(text):
    """Malzeme adını karşılaştırmaya hazırlar: boşlukları siler, küçük harfe çevirir."""
    text = text.strip()
    # Türkçe harf tuzağı: Python "I".lower() işlemini "i" yapar, oysa Türkçede "ı" olmalı.
    text = text.replace("I", "ı").replace("İ", "i")
    return text.lower()


def match_recipe(my_ingredients, recipe):
    """Tek bir tarifi, evdeki malzemelerle karşılaştırır."""
    mine = {normalize(item) for item in my_ingredients}
    needed = [normalize(item) for item in recipe["ingredients"]]

    have = [item for item in needed if item in mine]
    missing = [item for item in needed if item not in mine]
    ratio = len(have) / len(needed) if needed else 0

    return {
        "recipe": recipe,
        "have": have,
        "missing": missing,
        "ratio": ratio,
    }


def match_recipes(my_ingredients, recipes):
    """Tüm tarifleri eşleştirir ve eşleşme oranı yüksek olandan düşüğe sıralar."""
    results = [match_recipe(my_ingredients, recipe) for recipe in recipes]
    return sorted(results, key=lambda result: result["ratio"], reverse=True)