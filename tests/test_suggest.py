import random
from datetime import date

from core.suggest import score, suggest

TODAY = date(2026, 11, 5)


def R(name, ratio, missing=(), time=20):
    return {"recipe": {"name": name, "time_min": time}, "ratio": ratio, "missing": list(missing)}


def test_uyumlu_tarif_daha_yuksek_puan():
    assert score(R("A", 1.0), [], TODAY) > score(R("B", 0.5), [], TODAY)


def test_yeni_yapilan_tarif_geride():
    h = [{"name": "A", "date": "2026-11-04", "rating": None}]
    assert score(R("B", 1.0), h, TODAY) > score(R("A", 1.0), h, TODAY)


def test_puan_etkisi():
    h = [{"name": "A", "date": "2026-09-01", "rating": 5}, {"name": "B", "date": "2026-09-01", "rating": 1}]
    assert score(R("A", 1.0), h, TODAY) > score(R("B", 1.0), h, TODAY)


def test_bos_aday_none():
    assert suggest([], []) is None


def test_haric_tutma_ve_sure_ve_eksiksiz():
    c = [R("A", 1.0, time=60), R("B", 0.8, missing=["x"], time=10), R("C", 0.9, time=10)]
    assert suggest(c, [], exclude=["A", "B"], today=TODAY)["recipe"]["name"] == "C"
    assert suggest(c, [], max_time=30, only_complete=True, today=TODAY)["recipe"]["name"] == "C"
    assert suggest(c, [], max_time=5) is None


def test_hepsi_haric_none():
    assert suggest([R("A", 1.0)], [], exclude=["A"]) is None


def test_agirlikli_secim_cesitli_ama_gecerli():
    c = [R(n, 1.0) for n in "ABCDEFG"]
    rng = random.Random(1)
    got = {suggest(c, [], rng=rng, today=TODAY)["recipe"]["name"] for _ in range(60)}
    assert len(got) > 1 and got <= set("ABCDEFG")
