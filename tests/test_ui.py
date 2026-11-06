from core.ui import badge, bar, empty_html, kv_html, lead, meta_line, page_head, row_title, section, stats_html, step_html, tip


def test_html_kacis():
    assert "&lt;b&gt;" in page_head("<b>x</b>", "y")
    assert "&lt;script&gt;" in badge("<script>")
    assert "&amp;" in empty_html("A & B", "ipucu")
    assert "&lt;" in lead("<i>") and "&lt;" in tip("<i>")
    assert "&lt;" in row_title("<x>") and "&lt;" in meta_line(["<x>"])
    assert "&lt;" in section("<x>") and "&lt;" in step_html(1, 2, "<x>")


def test_stats_ve_kv():
    html = stats_html([(3, "malzeme"), (741, "tarif")])
    assert html.count('class="stat"') == 2 and "741" in html
    assert kv_html([("Kalori", "212 kcal")]).count("kv") == 1


def test_bar_sinirlari():
    assert 'width:100%' in bar(1.4) and 'width:0%' in bar(-1)
    assert 'class="full"' in bar(1.0) and 'class="full"' not in bar(0.5)
