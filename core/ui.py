"""Arayüz görünümü: koyu/açık tema CSS'i ve küçük HTML bileşenleri (Streamlit'ten bağımsız)."""

from html import escape

THEMES = {
    "Koyu": {
        "bg": "#0F1317", "panel": "#161B21", "panel2": "#1C222A", "line": "#2A323C",
        "text": "#E6EAEF", "muted": "#96A0AC", "accent": "#E08C4A", "accent_ink": "#1A1206",
        "accent_hover": "#EC9A58", "ok": "#5FB87E", "warn": "#E0B341", "danger": "#E07A6E",
        "shadow": "rgba(0,0,0,.35)", "code": "#D7C3A8",
    },
    "Açık": {
        "bg": "#F6F6F3", "panel": "#FFFFFF", "panel2": "#EFF1EC", "line": "#DCE0D8",
        "text": "#1C2225", "muted": "#5E6B6E", "accent": "#B4642F", "accent_ink": "#FFFFFF",
        "accent_hover": "#9E5524", "ok": "#2E7D4F", "warn": "#8A6100", "danger": "#B3382C",
        "shadow": "rgba(20,25,30,.08)", "code": "#7A4A1E",
    },
}
DEFAULT_THEME = "Koyu"
PALETTE = THEMES[DEFAULT_THEME]


def _variables(theme):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return f"""
:root {{
  color-scheme: {'light' if theme == 'Açık' else 'dark'};
  --bg: {t['bg']}; --panel: {t['panel']}; --panel2: {t['panel2']}; --line: {t['line']};
  --text: {t['text']}; --muted: {t['muted']}; --accent: {t['accent']};
  --accent-ink: {t['accent_ink']}; --accent-hover: {t['accent_hover']};
  --ok: {t['ok']}; --warn: {t['warn']}; --danger: {t['danger']};
  --shadow: {t['shadow']}; --code: {t['code']};
}}
"""


BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, [class*="css"] {
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
  font-feature-settings: 'tnum' 1;
}
.stApp { background: var(--bg); color: var(--text); }
#MainMenu, footer, [data-testid="stStatusWidget"] { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { max-width: 940px; padding: 2.1rem 1.2rem 5rem; }

/* ---------- Kenar çubuğu ---------- */
section[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
.brand { font-size: 1.04rem; font-weight: 700; letter-spacing: -.01em; }
.brand-sub { color: var(--muted); font-size: .78rem; margin-top: 2px; }
.nav-label { color: var(--muted); font-size: .7rem; letter-spacing: .09em;
  text-transform: uppercase; margin: 22px 0 6px; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  display: flex; align-items: center; width: 100%; padding: 9px 11px;
  border-radius: 8px; border: 1px solid transparent; cursor: pointer;
  color: var(--muted); font-size: .93rem; font-weight: 500; transition: background .12s, color .12s; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: var(--panel2); color: var(--text); }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: var(--panel2); color: var(--text); border-color: var(--line);
  box-shadow: inset 2px 0 0 var(--accent); }
section[data-testid="stSidebar"] div[role="radiogroup"] label p { font-size: .93rem; margin: 0; }

/* ---------- Sayfa başlığı ---------- */
.page-head { border-bottom: 1px solid var(--line); padding-bottom: 14px; margin-bottom: 20px; }
.page-head h1 { font-size: 1.42rem; font-weight: 700; margin: 0; letter-spacing: -.015em; color: var(--text); }
.page-head p { color: var(--muted); font-size: .9rem; margin: 5px 0 0; max-width: 62ch; }

/* ---------- Özet kutuları ---------- */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 22px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 11px 13px; }
.stat b { display: block; font-size: 1.3rem; font-weight: 600; line-height: 1.25; color: var(--text); }
.stat span { display: block; color: var(--muted); font-size: .72rem; letter-spacing: .06em;
  text-transform: uppercase; margin-top: 3px; }
@media (max-width: 680px) { .stats { grid-template-columns: repeat(2, 1fr); } }

/* ---------- Tarif kartı ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] { gap: .55rem; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stVerticalBlock"]) { border-radius: 12px; }
.row-title { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.row-title .name { font-size: 1.04rem; font-weight: 600; color: var(--text); }
.row-title .pct { font-size: .8rem; font-weight: 600; color: var(--muted); white-space: nowrap; }
.row-title .pct.full { color: var(--ok); }
.meta { color: var(--muted); font-size: .82rem; }
.meta b { color: var(--text); font-weight: 600; }
.bar { height: 3px; border-radius: 2px; background: var(--line); overflow: hidden; margin: 2px 0 0; }
.bar > i { display: block; height: 100%; background: var(--accent); }
.bar > i.full { background: var(--ok); }
.lead { color: var(--text); opacity: .86; font-size: .92rem; line-height: 1.55; margin: 2px 0 0; }
.tip { border-left: 2px solid var(--accent); padding: 2px 0 2px 11px; color: var(--text); opacity: .9;
  font-size: .88rem; line-height: 1.5; }

/* Rozetler */
.badge { display: inline-block; padding: 2px 9px; border-radius: 6px; font-size: .74rem;
  font-weight: 600; letter-spacing: .02em; margin: 0 6px 4px 0; border: 1px solid transparent; }
.badge.ok { background: rgba(95,184,126,.12); color: var(--ok); border-color: rgba(95,184,126,.3); }
.badge.miss { background: rgba(224,122,110,.12); color: var(--danger); border-color: rgba(224,122,110,.3); }
.badge.neutral { background: var(--panel2); color: var(--muted); border-color: var(--line); }
.badge.warn { background: rgba(224,179,65,.12); color: var(--warn); border-color: rgba(224,179,65,.3); }

/* ---------- Düğmeler ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 8px; font-weight: 500; font-size: .9rem; padding: .42rem .9rem;
  background: var(--panel2); color: var(--text); border: 1px solid var(--line); transition: all .12s; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  border-color: var(--accent); background: var(--panel2); color: var(--text); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: var(--accent); border-color: var(--accent); color: var(--accent-ink); font-weight: 600; }
.stButton > button[kind="primary"]:hover { background: var(--accent-hover); border-color: var(--accent-hover); color: var(--accent-ink); }
.stButton > button:focus:not(:active) { border-color: var(--accent); color: var(--text); }

/* ---------- Girdiler ---------- */
div[data-baseweb="select"] > div, div[data-baseweb="input"], div[data-baseweb="textarea"] {
  background: var(--panel) !important; border-color: var(--line) !important; border-radius: 8px !important; }
div[data-baseweb="select"] > div:hover, div[data-baseweb="input"]:hover { border-color: var(--accent) !important; }
span[data-baseweb="tag"] { background: var(--panel2) !important; border: 1px solid var(--line);
  color: var(--text) !important; border-radius: 6px; }
span[data-baseweb="tag"] svg { fill: var(--muted); }
label p, .stCheckbox p, .stRadio p { color: var(--text); }
div[data-testid="stWidgetLabel"] p { color: var(--muted); font-size: .82rem; }

/* Öğün seçimi: yatay radyo düğmeleri sekme şeridi gibi */
.meal div[role="radiogroup"] { gap: 6px; }
.meal div[role="radiogroup"] label { padding: 6px 15px; border: 1px solid var(--line);
  border-radius: 999px; background: var(--panel); color: var(--muted); font-size: .88rem; }
.meal div[role="radiogroup"] label > div:first-child { display: none; }
.meal div[role="radiogroup"] label:has(input:checked) { background: var(--panel2);
  color: var(--text); border-color: var(--accent); }

/* ---------- Diğer bileşenler ---------- */
div[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 10px; background: var(--panel); }
div[data-testid="stExpander"] summary { font-weight: 500; font-size: .9rem; color: var(--text); }
div[data-testid="stExpander"] summary:hover { color: var(--accent); }
div[data-testid="stAlert"] { border-radius: 10px; border: 1px solid var(--line); background: var(--panel); }
hr { border-color: var(--line); margin: 1.6rem 0; }
h2, h3, h4 { color: var(--text); font-weight: 600; letter-spacing: -.01em; }
h3 { font-size: 1.12rem; }
h4 { font-size: .98rem; margin: 1.1rem 0 .3rem; }
div[data-testid="stCaptionContainer"] p { color: var(--muted); font-size: .82rem; }
code { background: var(--panel2) !important; color: var(--code) !important; }
.stProgress > div > div > div { background: var(--accent); }

/* Bölüm başlığı (küçük, büyük harf) */
.section { color: var(--muted); font-size: .72rem; letter-spacing: .09em;
  text-transform: uppercase; margin: 22px 0 8px; font-weight: 600; }

/* Boş durum */
.empty { border: 1px dashed var(--line); border-radius: 12px; padding: 28px 22px;
  background: var(--panel); }
.empty b { display: block; color: var(--text); font-size: 1rem; margin-bottom: 4px; }
.empty span { color: var(--muted); font-size: .88rem; }

/* Adım adım pişirme */
.step-no { color: var(--accent); font-size: .74rem; letter-spacing: .09em;
  text-transform: uppercase; font-weight: 600; }
.step-text { font-size: 1.12rem; line-height: 1.62; color: var(--text); margin-top: 6px; }
.kv { display: flex; justify-content: space-between; border-bottom: 1px solid var(--line);
  padding: 7px 0; font-size: .9rem; }
.kv span { color: var(--muted); }

/* Açılır listeler ve girdi metinleri temayı izlesin */
div[data-baseweb="select"] div, div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea, div[data-baseweb="popover"] li,
ul[role="listbox"], ul[role="listbox"] li { color: var(--text) !important; }
div[data-baseweb="popover"] div[data-baseweb="menu"], ul[role="listbox"],
div[data-baseweb="popover"] ul { background: var(--panel) !important; }
div[data-baseweb="popover"] li:hover, ul[role="listbox"] li:hover { background: var(--panel2) !important; }
div[data-testid="stNumberInputContainer"] { background: var(--panel) !important; border-color: var(--line) !important; }
div[data-testid="stNumberInput"] button { background: var(--panel2) !important; color: var(--text) !important; }
.stApp [data-testid="stMarkdownContainer"] p, .stApp label span { color: var(--text); }

/* Görünüm (tema) seçici: küçük haplar */
section[data-testid="stSidebar"] .theme div[role="radiogroup"],
.theme div[role="radiogroup"] { gap: 6px; flex-direction: row; }
section[data-testid="stSidebar"] .theme div[role="radiogroup"] label,
.theme div[role="radiogroup"] label { flex: 1; justify-content: center; padding: 5px 10px;
  border: 1px solid var(--line); border-radius: 999px; background: var(--panel2);
  color: var(--muted); font-size: .82rem; box-shadow: none; }
section[data-testid="stSidebar"] .theme div[role="radiogroup"] label > div:first-child,
.theme div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] .theme div[role="radiogroup"] label:has(input:checked),
.theme div[role="radiogroup"] label:has(input:checked) { background: var(--accent);
  color: var(--accent-ink); border-color: var(--accent); box-shadow: none; }
section[data-testid="stSidebar"] .theme div[role="radiogroup"] label:has(input:checked) p,
.theme div[role="radiogroup"] label:has(input:checked) p { color: var(--accent-ink); }
section[data-testid="stSidebar"] .theme div[role="radiogroup"] label p,
.theme div[role="radiogroup"] label p { font-size: .82rem; margin: 0; }

/* Açılır paneller (Filtreler vb.) ve seçim kutuları: her iki temada okunur kalsın */
[data-testid="stPopover"] > button, [data-testid="stPopoverButton"] {
  background: var(--panel2) !important; border: 1px solid var(--line) !important; }
[data-testid="stPopover"] > button *, [data-testid="stPopoverButton"] * {
  color: var(--text) !important; }
[data-testid="stPopoverBody"], div[data-baseweb="popover"] > div {
  background: var(--panel) !important; border: 1px solid var(--line) !important; }
[data-testid="stPopoverBody"] label *, [data-testid="stPopoverBody"] p,
[data-testid="stPopoverBody"] span { color: var(--text) !important; }
div[data-baseweb="select"], div[data-baseweb="select"] > div,
div[data-baseweb="select"] > div > div { background: var(--panel) !important; }
div[data-baseweb="select"] * { color: var(--text) !important; }
div[data-baseweb="select"] svg { fill: var(--text) !important; }
div[data-baseweb="select"] input, div[data-baseweb="input"] input {
  -webkit-text-fill-color: var(--text) !important; }
</style>
"""


def css(theme=DEFAULT_THEME):
    """Seçilen temaya göre tam CSS bloğu."""
    return BASE.replace("<style>", "<style>" + _variables(theme), 1)


def page_head(title, subtitle=""):
    sub = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    return f'<div class="page-head"><h1>{escape(title)}</h1>{sub}</div>'


def stats_html(stats):
    """stats: [(değer, etiket), ...] -> özet kutuları."""
    cells = "".join(
        f'<div class="stat"><b>{escape(str(v))}</b><span>{escape(label)}</span></div>'
        for v, label in stats
    )
    return f'<div class="stats">{cells}</div>'


def section(title):
    return f'<div class="section">{escape(title)}</div>'


def badge(text, kind="neutral"):
    return f'<span class="badge {kind}">{escape(text)}</span>'


def badges(items):
    """items: [(metin, tür), ...]"""
    return "".join(badge(t, k) for t, k in items)


def row_title(name, right="", full=False):
    cls = "pct full" if full else "pct"
    right_html = f'<span class="{cls}">{escape(right)}</span>' if right else ""
    return f'<div class="row-title"><span class="name">{escape(name)}</span>{right_html}</div>'


def meta_line(parts):
    """parts: ['18 dk', '4 kişilik', ...] -> tek satır gri bilgi."""
    return '<div class="meta">' + " · ".join(escape(p) for p in parts) + "</div>"


def bar(ratio):
    pct = max(0.0, min(1.0, ratio)) * 100
    cls = ' class="full"' if pct >= 99.5 else ""
    return f'<div class="bar"><i{cls} style="width:{pct:.0f}%"></i></div>'


def lead(text):
    return f'<p class="lead">{escape(text)}</p>'


def tip(text):
    return f'<div class="tip">{escape(text)}</div>'


def empty_html(title, hint):
    return f'<div class="empty"><b>{escape(title)}</b><span>{escape(hint)}</span></div>'


def step_html(index, total, text):
    return (f'<div class="step-no">Adım {index} / {total}</div>'
            f'<div class="step-text">{escape(text)}</div>')


def kv_html(rows):
    return "".join(
        f'<div class="kv"><span>{escape(k)}</span><b>{escape(str(v))}</b></div>' for k, v in rows
    )