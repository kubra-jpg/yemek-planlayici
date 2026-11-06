"""Pişirme sayacı için saf mantık: adım metninden süre ayıklama ve sayaç bip sesi."""

import io
import math
import re
import struct
import wave

_DUR = re.compile(
    r"(\d+(?:,\d+)?)(?:\s*-\s*(\d+(?:,\d+)?))?\s*(saat|dakika|saniye)"
)
_UNIT_SECONDS = {"saat": 3600, "dakika": 60, "saniye": 1}


def _num(text):
    return float(text.replace(",", "."))


def _fmt(value):
    return str(int(value)) if float(value).is_integer() else str(value).replace(".", ",")


def parse_durations(text):
    """Adım metnindeki süreleri sırayla döndürür.

    Her kayıt: {"label": "3-4 dk", "seconds": 180}. Aralıkta (3-4 dakika) sayaç
    alt sınıra kurulur; pişme işaretini sonra kullanıcı kontrol eder.
    Aynı süre iki kez geçiyorsa tek kayıt tutulur.
    """
    found, seen = [], set()
    for m in _DUR.finditer(text or ""):
        low = _num(m.group(1))
        high = _num(m.group(2)) if m.group(2) else None
        unit = m.group(3)
        seconds = int(round(low * _UNIT_SECONDS[unit]))
        if seconds <= 0:
            continue
        short = {"saat": "saat", "dakika": "dk", "saniye": "sn"}[unit]
        label = f"{_fmt(low)}-{_fmt(high)} {short}" if high else f"{_fmt(low)} {short}"
        if (label, seconds) in seen:
            continue
        seen.add((label, seconds))
        found.append({"label": label, "seconds": seconds})
    return found


def format_clock(seconds):
    """Kalan saniyeyi 'dd:ss' ya da 'sa:dd:ss' yapar."""
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def beep_wav(freq=880, beeps=3, beep_s=0.25, gap_s=0.15, rate=22050):
    """Sayaç bitince çalınacak kısa bip sesi (WAV baytları)."""
    frames = bytearray()
    for _ in range(beeps):
        for i in range(int(rate * beep_s)):
            v = int(12000 * math.sin(2 * math.pi * freq * i / rate))
            frames += struct.pack("<h", v)
        frames += b"\x00\x00" * int(rate * gap_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return buf.getvalue()
