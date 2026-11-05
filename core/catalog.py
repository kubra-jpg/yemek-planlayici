"""Evdeki malzemeler için hazır seçim kataloğu (kategori -> malzeme adları)."""

from core.staples import STAPLE_CANDIDATES

CATALOG = {
    "Sebze": [
        "domates", "biber", "kırmızı biber", "acı biber", "salatalık", "soğan", "sarımsak",
        "patates", "havuç", "patlıcan", "kabak", "balkabağı", "ıspanak", "marul", "roka",
        "maydanoz", "dereotu", "nane", "fesleğen", "semizotu", "pırasa", "karnabahar", "brokoli",
        "lahana", "mor lahana", "kereviz", "enginar", "bamya", "taze fasulye", "bezelye", "bakla",
        "mantar", "mısır", "turp", "pancar", "kuşkonmaz", "taze soğan", "zencefil", "tatlı patates",
        "asma yaprağı", "börülce", "avokado", "turşu", "zeytin", "patlamalık mısır", "kuru patlıcan", "kuru biber",
        "yeşil mercimek", "domates konservesi", "dolmalık biber", "çarliston biber",
        "sivri biber", "kapya biber", "salata", "göbek marul", "tere", "ısırgan",
        "pazı", "kıvırcık", "lahana turşusu", "hıyar turşusu", "mantar konservesi", "yeşil soğan",
        "kabak çiçeği", "su kabağı", "bal kabağı", "kuru soğan", "şalgam",
    ],
    "Meyve": [
        "elma", "armut", "muz", "portakal", "mandalina", "limon", "çilek", "üzüm", "kiraz",
        "şeftali", "kayısı", "karpuz", "kavun", "nar", "incir", "ayva", "ananas", "kivi",
        "hindistan cevizi", "kuru kayısı", "kuru üzüm", "kuş üzümü", "hurma", "kuru incir",
        "dut", "böğürtlen", "ahududu", "yaban mersini", "erik", "vişne", "greyfurt", "mango",
        "papaya", "limon suyu", "portakal suyu", "kuru erik", "kuru elma", "elma suyu",
    ],
    "Et ve tavuk": [
        "kıyma", "kuşbaşı et", "kuzu eti", "dana eti", "biftek", "pirzola", "tavuk göğsü",
        "tavuk but", "tavuk kanat", "bütün tavuk", "hindi", "ciğer", "işkembe", "paça",
        "sucuk", "pastırma", "sosis", "salam", "jambon", "kemik", "kaburga", "bonfile", "antrikot",
        "tavuk baget", "tavuk kıyma", "dana kıyma", "kuzu kıyma",
        "dil", "böbrek", "kokoreç", "köfte", "döner", "kavurma",
    ],
    "Balık ve deniz ürünleri": [
        "balık", "levrek", "çupra", "somon", "hamsi", "sardalya", "uskumru", "palamut",
        "alabalık", "ton balığı", "karides", "kalamar", "midye", "istavrit", "mezgit",
        "lüfer", "barbunya balığı", "kefal", "mercan", "ahtapot", "yengeç", "kılıç balığı",
        "dil balığı", "tekir", "ançüez", "balık konservesi",
    ],
    "Süt ürünleri ve yumurta": [
        "süt", "yoğurt", "ayran", "tereyağı", "krema", "kaymak", "labne", "yumurta",
        "beyaz peynir", "kaşar", "peynir", "lor peyniri", "tulum peyniri", "mozzarella",
        "parmesan", "mascarpone", "çökelek", "dil peyniri", "cheddar",
        "krem peynir", "süzme yoğurt", "kefir", "süt tozu", "yağsız süt",
        "tam yağlı süt", "yumurta sarısı", "yumurta akı",
    ],
    "Bakliyat ve tahıl": [
        "pirinç", "bulgur", "ince bulgur", "makarna", "spagetti", "şehriye", "arpa şehriye",
        "erişte", "kırmızı mercimek", "yeşil mercimek", "nohut", "kuru fasulye", "barbunya",
        "yulaf ezmesi", "irmik", "mısır unu", "buğday", "tarhana", "noodle", "lazanya yaprağı",
        "karabuğday", "kinoa", "kuskus", "tutmaç", "mantı", "yarma", "pirinç unu",
        "tam buğday unu", "çavdar unu", "mısır gevreği", "müsli", "granola", "kepek",
        "fasulye", "kuru bakla", "soya",
    ],
    "Fırın ve hamur": [
        "ekmek", "lavaş", "yufka", "simit", "un", "maya", "kabartma tozu", "galeta unu",
        "kadayıf", "güllaç", "bisküvi", "kedi dili", "hamburger ekmeği", "tortilla",
    ],
    "Kuruyemiş": [
        "ceviz", "fındık", "badem", "fıstık", "çam fıstığı", "antep fıstığı", "susam",
        "ay çekirdeği", "kabak çekirdeği", "leblebi", "kestane", "yer fıstığı",
        "kaju", "fıstık ezmesi",
    ],
    "Temel gıda ve baharat": list(STAPLE_CANDIDATES) + [
        "vanilin", "pudra şekeri", "tarçın", "zencefil toz", "zerdeçal", "köri", "sumak",
        "defne yaprağı", "kırmızı toz biber", "kuru kekik", "limon tuzu",
        "ayçiçek yağı", "mısır yağı", "hardal", "kuru soğan",
    ],
    "Sos ve konserve": [
        "ketçap", "mayonez", "soya sosu", "nar ekşisi", "elma sirkesi", "barbekü sosu",
        "tahin", "pekmez", "bal", "reçel", "zeytin ezmesi", "domates sosu", "salça",
        "biber salçası", "hazır çorba", "ton balığı konservesi",
    ],
    "Tatlı ve içecek": [
        "çikolata", "kakao", "kahve", "çay", "ihlamur", "salep", "gül suyu", "safran",
        "dondurma", "tatlı sos", "jelatin", "karamel",
    ],
}


def catalog_names():
    """Tüm katalog malzemeleri, tekrarsız ve sıralı."""
    seen, names = set(), []
    for items in CATALOG.values():
        for n in items:
            if n not in seen:
                seen.add(n)
                names.append(n)
    return names