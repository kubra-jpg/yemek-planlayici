from core.planner import DAYS, empty_plan, load_plan, merged_shopping_recipe, planned_recipes, save_plan

R1 = {"id": 1, "name": "A", "servings": 2, "steps": [], "ingredients": [
    {"name": "yumurta", "quantity": 4, "unit": "adet"}, {"name": "un", "quantity": 200, "unit": "g"}]}
R2 = {"id": 2, "name": "B", "servings": 4, "steps": [], "ingredients": [
    {"name": "yumurta", "quantity": 2, "unit": "adet"}, {"name": "süt", "quantity": 1, "unit": "su bardağı"}]}
BY = {1: R1, 2: R2}


def test_bos_plan():
    p = empty_plan()
    assert list(p["days"]) == DAYS and all(v == [] for v in p["days"].values())


def test_kaydet_oku(tmp_path):
    p = empty_plan(3)
    p["days"]["Salı"] = [1, 2]
    f = tmp_path / "plan.json"
    save_plan(f, p)
    assert load_plan(f) == p


def test_dosya_yok_ya_da_bozuk(tmp_path):
    assert load_plan(tmp_path / "yok.json") == empty_plan()
    bad = tmp_path / "b.json"
    bad.write_text("{bozuk", encoding="utf-8")
    assert load_plan(bad) == empty_plan()


def test_silinmis_tarif_atlanir():
    p = empty_plan()
    p["days"]["Cuma"] = [1, 99]
    assert [r["id"] for r in planned_recipes(p, BY)] == [1]


def test_malzemeler_toplanir_ve_olceklenir():
    p = empty_plan(4)  # R1 x2, R2 x1
    p["days"]["Pazartesi"] = [1]
    p["days"]["Çarşamba"] = [2]
    m = merged_shopping_recipe(p, BY)
    by = {i["name"]: i for i in m["ingredients"]}
    assert by["yumurta"]["quantity"] == 10  # 8 + 2
    assert by["un"]["quantity"] == 400
    assert by["süt"]["quantity"] == 1
