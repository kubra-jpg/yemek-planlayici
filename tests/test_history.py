from datetime import date

from core.history import (
    add_entry, format_date, load_history, recent, save_history, set_rating,
    sort_by_history, stats, top_rated,
)


def H():
    h = []
    add_entry(h, "Menemen", 5, date(2026, 11, 1))
    add_entry(h, "Menemen", 4, date(2026, 11, 3))
    add_entry(h, "Mantı", None, date(2026, 10, 20))
    add_entry(h, "Kısır", 3, date(2026, 11, 2))
    return h


def test_stats():
    s = stats(H(), "Menemen")
    assert s == {"count": 2, "last": "2026-11-03", "avg": 4.5}
    assert stats(H(), "Mantı") == {"count": 1, "last": "2026-10-20", "avg": None}
    assert stats(H(), "Yok") == {"count": 0, "last": None, "avg": None}


def test_set_rating():
    h = H()
    set_rating(h, 2, 5)
    assert stats(h, "Mantı")["avg"] == 5.0
    set_rating(h, 99, 1)  # geçersiz sıra: hata vermez


def test_kaydet_oku_ve_bozuk(tmp_path):
    f = tmp_path / "h.json"
    save_history(f, H())
    assert load_history(f) == H()
    assert load_history(tmp_path / "yok.json") == []
    f.write_text("[{\"name\": \"A\", \"date\": \"2026-01-01\", \"rating\": 9}]", encoding="utf-8")
    assert load_history(f)[0]["rating"] == 5  # 1-5 aralığına çekilir
    f.write_text("bozuk", encoding="utf-8")
    assert load_history(f) == []


def mk(*names):
    return [{"recipe": {"name": n}} for n in names]


def test_siralama():
    res = mk("Mantı", "Kısır", "Menemen", "Hiç")
    by_rating = [r["recipe"]["name"] for r in sort_by_history(res, H(), "rating")]
    assert by_rating[0] == "Menemen" and by_rating[1] == "Kısır"
    by_last = [r["recipe"]["name"] for r in sort_by_history(res, H(), "last")]
    assert by_last[0] == "Hiç" and by_last[1] == "Mantı" and by_last[-1] == "Menemen"


def test_recent_ve_top():
    h = H()
    assert recent(h, 2)[0][0] == 3
    assert top_rated(h)[0] == ("Menemen", 4.5, 2)
    assert "Mantı" not in [t[0] for t in top_rated(h)]


def test_tarih_bicimi():
    assert format_date("2026-11-05") == "05.11.2026"
    assert format_date("bozuk") == "bozuk"
