"""'Bugün ne pişirsem?': dolaptaki malzemeye, geçmişe ve puanlara göre tek tarif önerir."""

import random
from datetime import date

from core.history import stats

_NEVER_COOKED_DAYS = 14  # hiç yapılmamış tarife "iki hafta önce yapılmış" kadar yenilik puanı


def score(result, history, today=None):
    """Bir eşleşme sonucunun öneri puanı (yüksek = daha iyi).

    - malzeme uyumu: 0-100 (ratio)
    - yenilik: uzun süredir yapılmayan/hiç yapılmayan tarife en çok 20 puan
    - puan: ortalama puanın 3'ten farkı kadar (en çok ±10)
    """
    today = today or date.today()
    s = stats(history, result["recipe"]["name"])
    if s["last"]:
        try:
            days = (today - date.fromisoformat(s["last"])).days
        except ValueError:
            days = _NEVER_COOKED_DAYS
    else:
        days = _NEVER_COOKED_DAYS
    novelty = min(max(days, 0), 30) / 30 * 20
    rating = (s["avg"] - 3) * 5 if s["avg"] else 0
    return result["ratio"] * 100 + novelty + rating


def suggest(candidates, history, exclude=(), max_time=None, only_complete=False,
            today=None, rng=None, top=5):
    """Adaylar arasından bir sonuç seçer; uygun aday yoksa None.

    candidates: match_recipes çıktısı (dolapla en az bir malzemesi eşleşenler).
    En yüksek puanlı `top` aday arasından puana göre ağırlıklı rastgele seçilir;
    böylece öneri hep aynı tarif olmaz ama iyi seçenekler öne çıkar.
    """
    rng = rng or random
    excluded = set(exclude)
    pool = []
    for r in candidates:
        recipe = r["recipe"]
        if recipe["name"] in excluded:
            continue
        if max_time and recipe["time_min"] > max_time:
            continue
        if only_complete and r["missing"]:
            continue
        pool.append(r)
    if not pool:
        return None
    ranked = sorted(pool, key=lambda r: score(r, history, today), reverse=True)[:top]
    weights = [max(score(r, history, today), 1) for r in ranked]
    return rng.choices(ranked, weights=weights, k=1)[0]
