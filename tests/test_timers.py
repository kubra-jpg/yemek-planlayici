import json
from pathlib import Path

from core.timers import beep_wav, format_clock, parse_durations


def test_tek_sure():
    assert parse_durations("Soğanı 4-5 dakika kavur.") == [{"label": "4-5 dk", "seconds": 240}]


def test_birden_cok_sure():
    d = parse_durations("3 dakika çevir; sonra 30 saniye karıştır, 1,5 dakika bekle.")
    assert [x["seconds"] for x in d] == [180, 30, 90]
    assert d[2]["label"] == "1,5 dk"


def test_saat():
    assert parse_durations("150°C fırında 3 saat pişir.")[0]["seconds"] == 10800


def test_sure_yok():
    assert parse_durations("Soğanı doğra.") == []
    assert parse_durations("") == []
    assert parse_durations(None) == []


def test_ayni_sure_tekrar_edilmez():
    assert len(parse_durations("5 dakika kavur, 5 dakika bekle")) == 1


def test_format_clock():
    assert format_clock(65) == "01:05"
    assert format_clock(3725) == "1:02:05"
    assert format_clock(-3) == "00:00"


def test_beep_wav_gecerli():
    assert beep_wav()[:4] == b"RIFF"


def test_pisirme_adimlarinin_cogunda_sure_var():
    data = json.loads((Path(__file__).parent.parent / "data" / "recipes.json").read_text("utf-8"))
    with_time = sum(1 for r in data for s in r["steps"] if parse_durations(s))
    assert with_time > 800
