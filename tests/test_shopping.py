from core.shopping import OTHER, aisle_for, group_by_aisle, to_text

ITEMS = [
    {"name": "süt", "label": "süt 1 l", "quantity": 1, "unit": "l"},
    {"name": "domates", "label": "domates 3 adet", "quantity": 3, "unit": "adet"},
    {"name": "kıyma", "label": "kıyma 300 g", "quantity": 300, "unit": "g"},
    {"name": "elma", "label": "elma 2 adet", "quantity": 2, "unit": "adet"},
    {"name": "uzaylı tozu", "label": "uzaylı tozu", "quantity": None, "unit": None},
]


def test_reyon_bulma():
    assert aisle_for("domates").endswith("Manav")
    assert aisle_for("kıyma").endswith("Kasap ve balık")
    assert aisle_for("uzaylı tozu") == OTHER


def test_gruplama_sirasi_ve_alfabe():
    groups = group_by_aisle(ITEMS)
    names = [g[0] for g in groups]
    assert names[0].endswith("Manav") and names[-1] == OTHER
    assert [i["name"] for i in groups[0][1]] == ["domates", "elma"]


def test_metin():
    text = to_text(ITEMS)
    assert "- domates 3 adet" in text and "- süt 1 l" in text
    assert text.index("Manav") < text.index("Kasap")
    assert to_text([]) == ""
