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
        "taze soğan", "turp", "pancar", "tatlı patates", "kuşkonmaz", "pazı", "tere", "zencefil", "bal kabağı", "yeşil biber", "kapya biber", "dolmalık biber", "çarliston biber", "sivri biber", "nane", "kuru domates", "kapari", "mısır konservesi", "fasulye konservesi", "domates konservesi",
    ],
    "Meyve": [
        "elma", "armut", "muz", "portakal", "mandalina", "limon", "çilek", "üzüm", "kiraz",
        "şeftali", "kayısı", "karpuz", "kavun", "nar", "incir", "ayva", "ananas", "kivi",
        "hindistan cevizi", "kuru kayısı", "kuru üzüm", "kuş üzümü", "hurma", "kuru incir",
        "dut", "böğürtlen", "ahududu", "yaban mersini", "erik", "vişne", "greyfurt", "mango",
        "papaya", "limon suyu", "portakal suyu", "kuru erik", "kuru elma", "elma suyu",
        "armut", "mandalina", "şeftali", "kayısı", "kiraz", "üzüm", "karpuz", "kavun", "nar", "incir", "ananas", "kivi", "hindistan cevizi", "hurma", "kuru incir", "yaban mersini", "erik", "vişne", "greyfurt", "mango", "kuru erik", "limon suyu", "portakal suyu",
    ],
    "Et ve tavuk": [
        "kıyma", "kuşbaşı et", "kuzu eti", "dana eti", "biftek", "pirzola", "tavuk göğsü",
        "tavuk but", "tavuk kanat", "bütün tavuk", "hindi", "ciğer", "işkembe", "paça",
        "sucuk", "pastırma", "sosis", "salam", "jambon", "kemik", "kaburga", "bonfile", "antrikot",
        "tavuk baget", "tavuk kıyma", "dana kıyma", "kuzu kıyma",
        "dil", "böbrek", "kokoreç", "köfte", "döner", "kavurma",
        "dana eti", "biftek", "pirzola", "kaburga", "bonfile", "hindi", "jambon", "sosis", "salam", "bütün tavuk", "yaprak sarma",
    ],
    "Balık ve deniz ürünleri": [
        "balık", "levrek", "çupra", "somon", "hamsi", "sardalya", "uskumru", "palamut",
        "alabalık", "ton balığı", "karides", "kalamar", "midye", "istavrit", "mezgit",
        "lüfer", "barbunya balığı", "kefal", "mercan", "ahtapot", "yengeç", "kılıç balığı",
        "dil balığı", "tekir", "ançüez", "balık konservesi",
        "istavrit", "mezgit", "lüfer", "kefal", "kılıç balığı", "ahtapot", "ton balığı konservesi",
    ],
    "Süt ürünleri ve yumurta": [
        "süt", "yoğurt", "ayran", "tereyağı", "krema", "kaymak", "labne", "yumurta",
        "beyaz peynir", "kaşar", "peynir", "lor peyniri", "tulum peyniri", "mozzarella",
        "parmesan", "mascarpone", "çökelek", "dil peyniri", "cheddar",
        "krem peynir", "süzme yoğurt", "kefir", "süt tozu", "yağsız süt",
        "tam yağlı süt", "yumurta sarısı", "yumurta akı",
        "lor peyniri", "tulum peyniri", "çökelek", "krem peynir", "kefir", "süt tozu", "yumurta sarısı", "yumurta akı", "süzme yoğurt", "ayran", "krem şanti",
    ],
    "Bakliyat ve tahıl": [
        "pirinç", "bulgur", "ince bulgur", "makarna", "spagetti", "şehriye", "arpa şehriye",
        "erişte", "kırmızı mercimek", "yeşil mercimek", "nohut", "kuru fasulye", "barbunya",
        "yulaf ezmesi", "irmik", "mısır unu", "buğday", "tarhana", "noodle", "lazanya yaprağı",
        "karabuğday", "kinoa", "kuskus", "tutmaç", "mantı", "yarma", "pirinç unu",
        "tam buğday unu", "çavdar unu", "mısır gevreği", "müsli", "granola", "kepek",
        "fasulye", "kuru bakla", "soya",
        "karabuğday", "kinoa", "kuskus", "pirinç unu", "tam buğday unu", "çavdar unu", "mısır gevreği", "müsli", "kuru bakla",
    ],
    "Fırın ve hamur": [
        "ekmek", "lavaş", "yufka", "simit", "un", "maya", "kabartma tozu", "galeta unu",
        "kadayıf", "güllaç", "bisküvi", "kedi dili", "hamburger ekmeği", "tortilla",
        "tortilla",
    ],
    "Kuruyemiş": [
        "ceviz", "fındık", "badem", "fıstık", "çam fıstığı", "antep fıstığı", "susam",
        "ay çekirdeği", "kabak çekirdeği", "leblebi", "kestane", "yer fıstığı",
        "kaju", "fıstık ezmesi",
        "fındık", "antep fıstığı", "ay çekirdeği", "kabak çekirdeği", "leblebi", "kestane", "yer fıstığı", "kaju", "fıstık ezmesi",
    ],
    "Temel gıda ve baharat": list(STAPLE_CANDIDATES) + [
        "vanilin", "pudra şekeri", "tarçın", "zencefil toz", "zerdeçal", "köri", "sumak",
        "defne yaprağı", "kırmızı toz biber", "kuru kekik", "limon tuzu",
        "ayçiçek yağı", "mısır yağı", "hardal", "kuru soğan",
        "zencefil toz", "yenibahar", "kakule", "karanfil", "kişniş", "biberiye", "rezene", "çörek otu", "mahlep", "kuru fesleğen", "adaçayı", "sarımsak tozu", "soğan tozu", "bulyon", "jelatin", "karbonat", "tavuk suyu", "sebze suyu",
    ],
    "Sos ve konserve": [
        "ketçap", "mayonez", "soya sosu", "nar ekşisi", "elma sirkesi", "barbekü sosu",
        "tahin", "pekmez", "bal", "reçel", "zeytin ezmesi", "domates sosu", "salça",
        "biber salçası", "hazır çorba", "ton balığı konservesi",
        "hardal", "ketçap", "reçel", "zeytin ezmesi", "domates sosu", "ton balığı konservesi", "kakaolu fındık kreması", "tahin helvası", "fasulye konservesi",
    ],
    "Tatlı ve içecek": [
        "çikolata", "kakao", "kahve", "çay", "ihlamur", "salep", "gül suyu", "safran",
        "dondurma", "tatlı sos", "jelatin", "karamel",
        "yeşil çay",
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


def catalog_groups():
    """Kategori -> malzeme listesi; her malzeme yalnızca ilk geçtiği kategoride, tekrarsız."""
    seen, groups = set(), {}
    for cat, items in CATALOG.items():
        kept = []
        for n in items:
            if n not in seen:
                seen.add(n)
                kept.append(n)
        groups[cat] = kept
    return groups


# Tek tuşla eklenebilen hazır paketler (hepsi katalogda bulunmalı)
PRESETS = {
    "🍳 Kahvaltılık": [
        "yumurta", "süt", "beyaz peynir", "kaşar", "zeytin", "domates", "salatalık", "bal",
        "reçel", "tereyağı", "ekmek", "yoğurt", "sucuk", "yulaf ezmesi",
    ],
    "🥦 Temel sebzeler": [
        "domates", "biber", "soğan", "sarımsak", "patates", "havuç", "salatalık", "limon",
        "maydanoz", "patlıcan", "kabak", "marul",
    ],
    "🫘 Bakliyat ve tahıl": [
        "pirinç", "bulgur", "makarna", "kırmızı mercimek", "yeşil mercimek", "nohut",
        "kuru fasulye", "şehriye", "irmik", "yulaf ezmesi",
    ],
    "🥩 Et ve tavuk": ["kıyma", "kuşbaşı et", "tavuk göğsü", "tavuk but", "sucuk"],
    "🍰 Pasta malzemeleri": [
        "un", "şeker", "yumurta", "süt", "tereyağı", "kabartma tozu", "vanilin", "kakao",
        "pudra şekeri", "çikolata", "nişasta", "krema",
    ],
}
