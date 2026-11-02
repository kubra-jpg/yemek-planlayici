from core.matcher import normalize
from core.staples import STAPLE_CANDIDATES


def test_candidates_are_normalized_and_unique():
    assert all(normalize(name) == name for name in STAPLE_CANDIDATES)
    assert len(STAPLE_CANDIDATES) == len(set(STAPLE_CANDIDATES))


def test_perishables_are_not_candidates():
    for name in ["yumurta", "domates", "kırmızı mercimek", "dereotu", "süt"]:
        assert name not in STAPLE_CANDIDATES