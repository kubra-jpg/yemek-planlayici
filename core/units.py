"""Birim tanımları ve dönüşümler."""

# Her birim: (tür, temel birim cinsinden karşılığı)
UNITS = {
    "g": ("weight", 1.0),
    "gram": ("weight", 1.0),
    "kg": ("weight", 1000.0),
    "ml": ("volume", 1.0),
    "l": ("volume", 1000.0),
    "litre": ("volume", 1000.0),
    "çay kaşığı": ("volume", 5.0),
    "tatlı kaşığı": ("volume", 10.0),
    "yemek kaşığı": ("volume", 15.0),
    "su bardağı": ("volume", 200.0),
    "adet": ("count", 1.0),
    "dilim": ("count", 1.0),
    "demet": ("count", 1.0),
    "paket": ("count", 1.0),
}

# Arayüzdeki açılır listede gösterilecek sıralama
UNIT_CHOICES = ["adet", "g", "kg", "ml", "l", "yemek kaşığı", "çay kaşığı",
                "su bardağı", "dilim", "demet", "paket"]


def unit_kind(unit):
    """Birimin türünü döndürür: weight, volume, count ya da None."""
    if not unit:
        return None
    entry = UNITS.get(unit.strip().lower())
    return entry[0] if entry else None


def to_base(quantity, unit):
    """Miktarı temel birime çevirir. Çevrilemezse None döndürür."""
    if quantity is None or not unit:
        return None
    entry = UNITS.get(unit.strip().lower())
    if entry is None:
        return None
    return quantity * entry[1]


def is_comparable(unit_a, unit_b):
    """İki birim aynı türdense karşılaştırılabilir."""
    kind_a = unit_kind(unit_a)
    return kind_a is not None and kind_a == unit_kind(unit_b)


def format_amount(quantity, unit):
    """Ekranda gösterim: 2.0 adet yerine '2 adet'."""
    if quantity is None:
        return unit or ""
    if quantity == int(quantity):
        quantity = int(quantity)
    return f"{quantity} {unit}".strip() if unit else str(quantity)