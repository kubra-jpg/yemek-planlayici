from core.units import format_amount, is_comparable, to_base, unit_kind


def test_weight_conversion():
    assert to_base(2, "kg") == 2000
    assert to_base(500, "g") == 500


def test_volume_conversion():
    assert to_base(1, "l") == 1000
    assert to_base(2, "yemek kaşığı") == 30


def test_unknown_unit():
    assert to_base(1, "tutam") is None
    assert unit_kind("tutam") is None


def test_comparable_only_within_kind():
    assert is_comparable("g", "kg") is True
    assert is_comparable("g", "adet") is False
    assert is_comparable("ml", "") is False


def test_format_amount():
    assert format_amount(2.0, "adet") == "2 adet"
    assert format_amount(0.5, "kg") == "0.5 kg"
    assert format_amount(None, "g") == "g"