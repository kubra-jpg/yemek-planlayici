"""Yaklaşık kalori hesabı: malzeme miktarlarından tarif başına ve kişi başına kcal.

Değerler 100 g başına ortalama kcal'dir; birim dönüşümleri yaklaşık gramajlara dayanır.
Sonuç bir tahmindir (pişirme, marka ve boyut farkları dikkate alınmaz).
"""

from core.matcher import normalize

# ad: (100 g kcal, su bardağı g, adet g, demet g, dilim g, paket g) -- bilinmeyen None
_N = {
    "acı biber": (40, None, 15, None, None, None),
    "alabalık": (140, None, 250, None, None, None),
    "arpa şehriye": (360, 150, None, None, None, None),
    "asma yaprağı": (90, None, 3, None, None, None),
    "avokado": (160, None, 200, None, None, None),
    "ayva": (57, None, 250, None, None, None),
    "badem": (575, 140, None, None, None, None),
    "bakla": (70, 150, None, None, None, None),
    "bal": (304, 320, None, None, None, None),
    "balkabağı": (26, 130, None, None, None, None),
    "balık": (150, None, 250, None, None, None),
    "bamya": (33, 100, None, None, None, None),
    "barbekü sosu": (150, 270, None, None, None, None),
    "barbunya": (330, 180, None, None, None, None),
    "beyaz peynir": (260, 150, None, None, 25, None),
    "bezelye": (80, 150, None, None, None, None),
    "biber": (27, None, 40, None, None, None),
    "bisküvi": (450, 100, 8, None, None, None),
    "brokoli": (34, None, 300, None, None, None),
    "bulgur": (350, 160, None, None, None, None),
    "buğday": (340, 170, None, None, None, None),
    "börülce": (340, 180, None, None, None, None),
    "ceviz": (654, 100, 8, None, None, None),
    "ciğer": (135, None, None, None, None, None),
    "dereotu": (43, None, None, 40, None, None),
    "domates": (18, None, 120, None, None, None),
    "dondurma": (207, 130, 50, None, None, None),
    "ekmek": (265, None, 100, None, 30, None),
    "elma": (52, None, 180, None, None, None),
    "elma sirkesi": (21, 240, None, None, None, None),
    "enginar": (47, None, 150, None, None, None),
    "erişte": (360, 100, None, None, None, None),
    "fesleğen": (23, None, None, 30, None, None),
    "fıstık": (570, 140, None, None, None, None),
    "galeta unu": (395, 110, None, None, None, None),
    "gül suyu": (5, 240, None, None, None, None),
    "güllaç": (350, None, 5, None, None, None),
    "hamburger ekmeği": (270, None, 80, None, None, None),
    "hamsi": (130, None, 15, None, None, None),
    "havuç": (41, None, 80, None, None, None),
    "ihlamur": (1, 20, None, None, None, None),
    "ince bulgur": (350, 160, None, None, None, None),
    "irmik": (360, 170, None, None, None, None),
    "işkembe": (85, None, None, None, None, None),
    "kabak": (17, None, 200, None, None, None),
    "kabartma tozu": (53, None, None, None, None, 10),
    "kadayıf": (330, None, None, None, None, None),
    "kahve": (300, 100, None, None, None, None),
    "kakao": (230, 100, None, None, None, None),
    "kalamar": (92, None, None, None, None, None),
    "karabiber": (250, 100, None, None, None, None),
    "karides": (85, None, None, None, None, None),
    "karnabahar": (25, None, 600, None, None, None),
    "kaymak": (400, 230, None, None, None, None),
    "kaşar": (330, 100, None, None, 20, None),
    "kedi dili": (400, None, 5, None, None, None),
    "kekik": (276, 40, None, None, None, None),
    "kereviz": (42, None, 350, None, None, None),
    "kimyon": (375, 100, None, None, None, None),
    "krema": (340, 240, None, None, None, None),
    "kuru fasulye": (340, 190, None, None, None, None),
    "kuru kayısı": (240, 150, 10, None, None, None),
    "kuru nane": (280, 30, None, None, None, None),
    "kuru patlıcan": (280, None, 5, None, None, None),
    "kuru üzüm": (299, 150, None, None, None, None),
    "kuzu eti": (250, None, None, None, None, None),
    "kuş üzümü": (299, 150, None, None, None, None),
    "kuşbaşı et": (220, None, None, None, None, None),
    "kırmızı biber": (31, None, 100, None, None, None),
    "kırmızı mercimek": (350, 200, None, None, None, None),
    "kıyma": (250, None, None, None, None, None),
    "labne": (180, 240, None, None, None, None),
    "lahana": (25, None, 1000, None, None, None),
    "lavaş": (275, None, 60, None, None, None),
    "lazanya yaprağı": (350, None, 10, None, None, None),
    "levrek": (100, None, 350, None, None, None),
    "limon": (29, None, 100, None, None, None),
    "makarna": (360, 100, None, None, None, None),
    "mantar": (22, 70, None, None, None, None),
    "marul": (15, None, 300, None, None, None),
    "mascarpone": (430, 250, None, None, None, None),
    "maya": (325, None, None, None, None, 10),
    "maydanoz": (36, None, None, 60, None, None),
    "mayonez": (680, 220, None, None, None, None),
    "midye": (86, None, 15, None, None, None),
    "mor lahana": (31, None, 800, None, None, None),
    "mozzarella": (280, 110, None, None, None, None),
    "muz": (89, None, 120, None, None, None),
    "mısır": (86, 160, None, None, None, 200),
    "mısır unu": (360, 140, None, None, None, None),
    "nar ekşisi": (60, 300, None, None, None, None),
    "nişasta": (340, 130, None, None, None, None),
    "nohut": (360, 200, None, None, None, None),
    "noodle": (380, None, None, None, None, 85),
    "palamut": (150, None, None, None, 120, None),
    "parmesan": (430, 100, None, None, None, None),
    "pastırma": (200, None, None, None, None, None),
    "patates": (77, None, 150, None, None, None),
    "patlamalık mısır": (370, 200, None, None, None, None),
    "patlıcan": (25, None, 200, None, None, None),
    "paça": (150, None, None, None, None, None),
    "pekmez": (290, 340, None, None, None, None),
    "peynir": (300, 150, None, None, 25, None),
    "pirinç": (360, 185, None, None, None, None),
    "portakal": (47, None, 180, None, None, None),
    "pudra şekeri": (390, 120, None, None, None, None),
    "pul biber": (300, 80, None, None, None, None),
    "pırasa": (31, None, 150, None, None, None),
    "roka": (25, None, None, 100, None, None),
    "safran": (310, 60, None, None, None, None),
    "salatalık": (15, None, 120, None, None, None),
    "salep": (350, 100, None, None, None, None),
    "salça": (82, 280, None, None, None, None),
    "sardalya": (210, None, None, None, None, None),
    "sarımsak": (149, None, 4, None, None, None),
    "semizotu": (20, None, None, None, None, None),
    "simit": (300, None, 120, None, None, None),
    "sirke": (20, 240, None, None, None, None),
    "somon": (208, None, None, None, None, None),
    "soya sosu": (53, 270, None, None, None, None),
    "soğan": (40, None, 110, None, None, None),
    "spagetti": (360, 100, None, None, None, None),
    "sucuk": (450, None, None, None, None, None),
    "sumak": (240, 100, None, None, None, None),
    "susam": (573, 144, None, None, None, None),
    "süt": (61, 245, None, None, None, None),
    "tahin": (595, 250, None, None, None, None),
    "tarhana": (350, 120, None, None, None, None),
    "tarçın": (247, 125, None, None, None, None),
    "tavuk but": (200, None, None, None, None, None),
    "tavuk göğsü": (165, None, None, None, None, None),
    "tavuk kanat": (215, None, None, None, None, None),
    "taze fasulye": (31, 110, None, None, None, None),
    "tereyağı": (717, 227, None, None, None, None),
    "ton balığı": (150, None, None, None, None, 150),
    "turşu": (15, None, 40, None, None, None),
    "tutmaç": (350, 120, None, None, None, None),
    "tuz": (0, 290, None, None, None, None),
    "un": (364, 125, None, None, None, None),
    "uskumru": (205, None, 250, None, None, None),
    "vanilin": (0, None, None, None, None, 1),
    "yağ": (884, 220, None, None, None, None),
    "yeşil mercimek": (350, 200, None, None, None, None),
    "yoğurt": (65, 245, None, None, None, None),
    "yufka": (290, None, 35, None, None, None),
    "yulaf ezmesi": (370, 90, None, None, None, None),
    "yumurta": (143, None, 55, None, None, None),
    "zeytin": (145, None, 4, None, None, None),
    "zeytinyağı": (884, 216, None, None, None, None),
    "çam fıstığı": (673, 140, None, None, None, None),
    "çikolata": (540, 170, None, None, None, None),
    "çilek": (32, 150, None, None, None, None),
    "çupra": (120, None, 300, None, None, None),
    "ıspanak": (23, None, None, None, None, None),
    "şehriye": (360, 150, None, None, None, None),
    "şeker": (387, 200, None, None, None, None),
}
NUTRITION = {normalize(k): v for k, v in _N.items()}

# ad: (protein g, karbonhidrat g, yağ g) -- 100 g başına
_M = {
    "acı biber": (2, 9, 0.4),
    "alabalık": (20, 0, 6),
    "arpa şehriye": (11, 75, 1.5),
    "asma yaprağı": (5, 17, 2),
    "avokado": (2, 9, 15),
    "ayva": (0.4, 15, 0.1),
    "badem": (21, 22, 50),
    "bakla": (5, 11, 0.5),
    "bal": (0.3, 82, 0),
    "balkabağı": (1, 6.5, 0.1),
    "balık": (20, 0, 6),
    "bamya": (2, 7, 0.2),
    "barbekü sosu": (1, 34, 0.5),
    "barbunya": (22, 60, 1.2),
    "beyaz peynir": (17, 2, 21),
    "bezelye": (5, 14, 0.4),
    "biber": (1, 5, 0.2),
    "bisküvi": (7, 70, 13),
    "brokoli": (2.5, 5, 0.4),
    "bulgur": (12, 75, 1.3),
    "buğday": (12, 71, 2),
    "börülce": (23, 60, 1.3),
    "ceviz": (15, 14, 61),
    "ciğer": (20, 4, 4),
    "dereotu": (3, 6, 1),
    "domates": (0.9, 3, 0.2),
    "dondurma": (3.5, 24, 11),
    "ekmek": (9, 49, 3.2),
    "elma": (0.3, 12, 0.2),
    "elma sirkesi": (0, 5, 0),
    "enginar": (3, 9, 0.1),
    "erişte": (12, 74, 2),
    "fesleğen": (3, 1.5, 0.6),
    "fıstık": (25, 16, 45),
    "galeta unu": (13, 72, 5),
    "gül suyu": (0, 1, 0),
    "güllaç": (8, 78, 0.8),
    "hamburger ekmeği": (9, 50, 4),
    "hamsi": (20, 0, 5),
    "havuç": (0.9, 9.6, 0.2),
    "ihlamur": (0, 0, 0),
    "ince bulgur": (12, 75, 1.3),
    "irmik": (12.7, 73, 1),
    "işkembe": (12, 0, 3.5),
    "kabak": (1, 2.5, 0.2),
    "kabartma tozu": (0, 13, 0),
    "kadayıf": (10, 70, 1),
    "kahve": (13, 50, 5),
    "kakao": (20, 10, 11),
    "kalamar": (16, 3, 1.4),
    "karabiber": (10, 45, 3.3),
    "karides": (18, 0.2, 1.1),
    "karnabahar": (1.9, 3.5, 0.3),
    "kaymak": (2, 3, 40),
    "kaşar": (25, 1.5, 26),
    "kedi dili": (8, 75, 7),
    "kekik": (9, 45, 4),
    "kereviz": (1.5, 9, 0.3),
    "kimyon": (18, 34, 20),
    "krema": (2, 3, 35),
    "kuru fasulye": (22, 61, 1.2),
    "kuru kayısı": (3.4, 55, 0.5),
    "kuru nane": (19, 40, 4),
    "kuru patlıcan": (10, 60, 1),
    "kuru üzüm": (3, 70, 0.5),
    "kuzu eti": (17, 0, 20),
    "kuş üzümü": (3, 70, 0.5),
    "kuşbaşı et": (20, 0, 15),
    "kırmızı biber": (1, 6, 0.3),
    "kırmızı mercimek": (25, 60, 1.1),
    "kıyma": (18, 0, 20),
    "labne": (6, 4, 15),
    "lahana": (1.3, 4.5, 0.1),
    "lavaş": (9, 55, 1.5),
    "lazanya yaprağı": (12, 72, 1.5),
    "levrek": (19, 0, 2.5),
    "limon": (1, 5, 0.3),
    "makarna": (12, 72, 1.5),
    "mantar": (2.5, 2.5, 0.3),
    "marul": (1.4, 2.2, 0.2),
    "mascarpone": (4.5, 4, 44),
    "maya": (40, 30, 5),
    "maydanoz": (3, 4, 0.5),
    "mayonez": (1, 3, 75),
    "midye": (11, 6, 2),
    "mor lahana": (1.4, 6, 0.2),
    "mozzarella": (22, 2, 22),
    "muz": (1, 20, 0.3),
    "mısır": (3, 16, 1.2),
    "mısır unu": (7, 77, 3.9),
    "nar ekşisi": (0.5, 15, 0),
    "nişasta": (0.3, 84, 0.1),
    "nohut": (19, 58, 5.5),
    "noodle": (10, 68, 8),
    "palamut": (22, 0, 6),
    "parmesan": (36, 3, 29),
    "pastırma": (28, 1, 9),
    "patates": (2, 17, 0.1),
    "patlamalık mısır": (12, 74, 4.5),
    "patlıcan": (1, 4.5, 0.2),
    "paça": (20, 0, 8),
    "pekmez": (1, 72, 0),
    "peynir": (21, 2, 23),
    "pirinç": (7, 79, 0.6),
    "portakal": (0.9, 10, 0.1),
    "pudra şekeri": (0, 97, 0),
    "pul biber": (12, 40, 8),
    "pırasa": (1.5, 5.5, 0.3),
    "roka": (2.6, 2.5, 0.5),
    "safran": (11, 55, 6),
    "salatalık": (0.7, 3, 0.1),
    "salep": (2, 85, 0.5),
    "salça": (4, 16, 0.5),
    "sardalya": (24, 0, 12),
    "sarımsak": (6, 30, 0.5),
    "semizotu": (2, 2, 0.4),
    "simit": (10, 55, 6),
    "sirke": (0, 5, 0),
    "somon": (20, 0, 14),
    "soya sosu": (8, 5, 0.1),
    "soğan": (1.1, 9, 0.1),
    "spagetti": (12, 72, 1.5),
    "sucuk": (22, 2, 40),
    "sumak": (5, 40, 6),
    "susam": (18, 23, 45),
    "süt": (3.2, 4.8, 3.3),
    "tahin": (17, 20, 50),
    "tarhana": (14, 60, 5),
    "tarçın": (4, 55, 1.2),
    "tavuk but": (17, 0, 14),
    "tavuk göğsü": (31, 0, 4.5),
    "tavuk kanat": (18, 0, 16),
    "taze fasulye": (1.8, 5.5, 0.2),
    "tereyağı": (0.9, 0.1, 79.5),
    "ton balığı": (25, 0, 6),
    "turşu": (0.5, 3, 0.1),
    "tutmaç": (12, 72, 2),
    "tuz": (0, 0, 0),
    "un": (10, 76, 1.5),
    "uskumru": (19, 0, 14),
    "vanilin": (0, 0, 0),
    "yağ": (0, 0, 98),
    "yeşil mercimek": (25, 60, 1.1),
    "yoğurt": (3.5, 4.5, 3.5),
    "yufka": (9, 60, 1.5),
    "yulaf ezmesi": (13, 66, 7),
    "yumurta": (12.5, 1, 10),
    "zeytin": (1, 3, 14),
    "zeytinyağı": (0, 0, 98),
    "çam fıstığı": (14, 13, 63),
    "çikolata": (6, 55, 32),
    "çilek": (0.7, 6.5, 0.3),
    "çupra": (20, 0, 4.5),
    "ıspanak": (2.9, 1.8, 0.4),
    "şehriye": (12, 73, 1.5),
    "şeker": (0, 97, 0),
}
MACROS = {normalize(k): v for k, v in _M.items()}

# su bardağı = 200 ml kabul edilir; diğer hacim birimlerinin su bardağına oranı
_CUP_FRACTION = {
    "su bardağı": 1.0,
    "yemek kaşığı": 0.075,
    "tatlı kaşığı": 0.05,
    "çay kaşığı": 0.025,
    "ml": 1 / 200,
    "l": 5.0,
}
_PIECE_COL = {"adet": 2, "demet": 3, "dilim": 4, "paket": 5}


def _find_key(name):
    """Malzeme adından tablo anahtarını bulur; tam ad yoksa en uzun kelime-altkümesi eşleşmesi."""
    key = normalize(name)
    if key in NUTRITION:
        return key
    words = set(key.split())
    best = None
    for k in NUTRITION:
        kw = set(k.split())
        if kw <= words and (best is None or len(k) > len(best)):
            best = k
    return best


def lookup(name):
    """Malzemenin besin kaydını (kcal, bardak g, adet g, ...) döndürür; yoksa None."""
    key = _find_key(name)
    return NUTRITION[key] if key else None


def grams(name, quantity, unit):
    """Miktarı grama çevirir; çevrilemiyorsa None."""
    if not quantity:
        return None
    if unit == "g":
        return float(quantity)
    if unit == "kg":
        return float(quantity) * 1000
    entry = lookup(name)
    if entry is None:
        return None
    if unit in _CUP_FRACTION:
        cup = entry[1]
        return None if cup is None else cup * _CUP_FRACTION[unit] * float(quantity)
    col = _PIECE_COL.get(unit)
    if col is None or entry[col] is None:
        return None
    return entry[col] * float(quantity)


def _factor(name, quantity, unit):
    """(gram, besin anahtarı) ya da hesaplanamıyorsa None."""
    key = _find_key(name)
    g = grams(name, quantity, unit)
    if key is None or g is None:
        return None
    return g, key


def ingredient_kcal(name, quantity, unit):
    """Bir malzemenin kcal değeri; hesaplanamıyorsa None."""
    f = _factor(name, quantity, unit)
    return None if f is None else NUTRITION[f[1]][0] * f[0] / 100


def recipe_nutrition(recipe):
    """Tarifin toplam ve kişi başı değerleri.

    Dönüş: {'total': kcal, 'per_serving': kcal, 'protein': g, 'carbs': g, 'fat': g,
    'unknown': [hesaba katılmayan malzemeler]} -- protein/carbs/fat kişi başıdır.
    """
    kcal = protein = carbs = fat = 0.0
    unknown = []
    for ing in recipe["ingredients"]:
        f = _factor(ing["name"], ing.get("quantity"), ing.get("unit"))
        if f is None:
            unknown.append(ing["name"])
            continue
        g, key = f
        # Kızartma yağının büyük kısmı kapta kalır: bol yağı (>= 100 g) %15 say
        share = 0.15 if key in ("yağ", "zeytinyağı") and g >= 100 else 1.0
        p, c, y = MACROS[key]
        kcal += NUTRITION[key][0] * g / 100 * share
        protein += p * g / 100 * share
        carbs += c * g / 100 * share
        fat += y * g / 100 * share
    servings = max(int(recipe.get("servings") or 1), 1)
    return {
        "total": round(kcal),
        "per_serving": round(kcal / servings),
        "protein": round(protein / servings),
        "carbs": round(carbs / servings),
        "fat": round(fat / servings),
        "unknown": unknown,
    }


def recipe_calories(recipe):
    """{'total', 'per_serving', 'unknown'} -- eski arayüz, recipe_nutrition'ın kısa hali."""
    n = recipe_nutrition(recipe)
    return {"total": n["total"], "per_serving": n["per_serving"], "unknown": n["unknown"]}