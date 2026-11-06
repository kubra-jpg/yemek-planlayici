"""Alışveriş listesini market reyonlarına göre gruplar ve kopyalanabilir metne çevirir."""

from core.catalog import catalog_groups
from core.matcher import find_in_pantry, normalize
from core.units import format_amount

# Katalog kategorisi -> market reyonu (sıralama = markette dolaşma sırası)
AISLES = [
    ("🥬 Manav", ["Sebze", "Meyve"]),
    ("🥩 Kasap ve balık", ["Et ve tavuk", "Balık ve deniz ürünleri"]),
    ("🧀 Süt ve kahvaltılık", ["Süt ürünleri ve yumurta"]),
    ("🍞 Fırın", ["Fırın ve hamur"]),
    ("🫘 Bakliyat ve kuru gıda", ["Bakliyat ve tahıl"]),
    ("🧂 Baharat ve temel gıda", ["Temel gıda ve baharat"]),
    ("🥫 Konserve ve soslar", ["Sos ve konserve"]),
    ("🥜 Kuruyemiş", ["Kuruyemiş"]),
    ("🍫 Tatlı ve içecek", ["Tatlı ve içecek"]),
]
OTHER = "🛍 Diğer"


def _lookup():
    cat_to_aisle = {c: a for a, cats in AISLES for c in cats}
    return {normalize(n): cat_to_aisle[c] for c, items in catalog_groups().items()
            if c in cat_to_aisle for n in items}


def aisle_for(name, lookup=None):
    """Malzemenin reyonu: önce tam, sonra kelime eşleşmesi; bulunamazsa 'Diğer'."""
    lookup = lookup if lookup is not None else _lookup()
    key = normalize(name)
    if key in lookup:
        return lookup[key]
    found = find_in_pantry(key, {k: None for k in lookup})
    return lookup[found] if found is not None else OTHER


def group_by_aisle(items):
    """items: [{'name','label',...}] -> [(reyon, [item,...])]; reyonlar market sırasında,
    her reyonda malzemeler alfabetik; boş reyonlar atlanır."""
    lookup = _lookup()
    groups = {}
    for item in items:
        groups.setdefault(aisle_for(item["name"], lookup), []).append(item)
    order = [a for a, _ in AISLES] + [OTHER]
    return [(a, sorted(groups[a], key=lambda i: normalize(i["name"]))) for a in order if a in groups]


def _label(item):
    return item.get("label") or f"{item['name']} {format_amount(item.get('quantity'), item.get('unit'))}".strip()


def to_text(items):
    """Panoya kopyalanacak düz metin (mesajlaşma uygulamalarına yapıştırılabilir)."""
    lines = []
    for aisle, group in group_by_aisle(items):
        lines.append(aisle)
        lines.extend(f"- {_label(i)}" for i in group)
        lines.append("")
    return "\n".join(lines).strip()
