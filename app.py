"""Yemek Planlayıcı + Alışveriş Listesi — Streamlit arayüzü."""

import re
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import streamlit as st

from core import repository as repo
from core.catalog import PRESETS, catalog_groups, catalog_names
from core.category import CATEGORIES, category_of
from core.cooking import scale_recipe, used_pantry_names
from core.db import get_session, init_db
from core.deduct import plan_deductions
from core.diet import ALLERGIES, DIETS, contains_text, filter_by_diet, load_settings, save_settings
from core.equipment import PROFILES, TOOLS, load_overrides, tools_for
from core.filters import SORT_LABELS, filter_recipes, sort_results, turkish_key
from core.goals import sort_by_nutrition
from core.history import (
    add_entry, format_date, load_history, recent, save_history, set_rating,
    sort_by_history, stats, top_rated,
)
from core.matcher import match_recipe, match_recipes, normalize
from core.nutrition import recipe_nutrition
from core.planner import DAYS, load_plan, merged_shopping_recipe, planned_recipes, save_plan
from core.shopping import group_by_aisle, to_text as shopping_to_text
from core.staples import STAPLE_CANDIDATES
from core.suggest import suggest
from core.texts import describe, load_texts, tip_for
from core.timers import beep_wav, format_clock, parse_durations
from core.ui import (
    DEFAULT_THEME, THEMES, bar, badges, css, empty_html, kv_html, lead, meta_line,
    page_head, row_title, section, stats_html, step_html, tip,
)
from core.units import UNIT_CHOICES, format_amount

DATA_DIR = Path(__file__).parent / "data"
PLAN_FILE = DATA_DIR / "plan.json"
DIET_FILE = DATA_DIR / "diet.json"
HISTORY_FILE = DATA_DIR / "history.json"
PAGE_SIZE = 12  # tarif listesinde bir seferde gösterilen tarif sayısı
NO_UNIT = "birim yok"  # miktar birimi seçilmediğinde listede görünen seçenek
PLAIN = re.compile(r"[^\w\sçğıöşüÇĞİÖŞÜ]", re.UNICODE)  # etiketlerdeki simgeleri temizler

st.set_page_config(
    page_title="Yemek Planlayıcı",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)
if "theme" not in st.session_state:
    st.session_state["theme"] = DEFAULT_THEME
st.markdown(css(st.session_state["theme"]), unsafe_allow_html=True)


# ======================================================================
# Veri katmanı — her tıklamada veritabanını yeniden okumamak için önbellek
# ======================================================================
@st.cache_resource
def setup_database():
    """Tabloları oluşturur; tarifler boşsa JSON'dan yükler (açılışta bir kez)."""
    init_db()
    with get_session() as session:
        repo.seed_recipes_if_empty(session, DATA_DIR / "recipes.json")
    return True


setup_database()

if "data_version" not in st.session_state:
    st.session_state["data_version"] = 0


@contextmanager
def writing():
    """Veritabanına yazmak için: iş bitince önbellek sürümünü ilerletir."""
    with get_session() as session:
        yield session
    st.session_state["data_version"] += 1


@st.cache_resource(max_entries=2, show_spinner=False)
def load_data(version):
    """Ekranın ihtiyaç duyduğu her şeyi tek seferde okur (sürüm değişince yenilenir)."""
    with get_session() as session:
        return {
            "pantry": repo.pantry_as_dict(session),
            "pantry_items": repo.list_pantry_items(session),
            "recipes": repo.list_recipes(session),
            "shopping": repo.list_shopping_items(session),
            "staples": repo.list_staples(session),
            "all_ingredients": repo.list_all_ingredient_names(session),
        }


@st.cache_resource(show_spinner=False)
def static_files():
    """Dosyadan okunan sabit veriler: ekipman ve tarif yazıları."""
    return {"equipment": load_overrides(), "texts": load_texts()}


@st.cache_resource(max_entries=2, show_spinner=False)
def recipe_index(version):
    """Tarif başına ağır hesaplar (besin, kategori, alet, uyarı) — bir kez hesaplanır."""
    files = static_files()
    index = {}
    for r in load_data(version)["recipes"]:
        index[r["id"]] = {
            "nut": recipe_nutrition(r),
            "category": category_of(r["name"]),
            "tools": tools_for(r, files["equipment"]),
            "contains": contains_text(r),
            "desc": describe(r["name"], files["texts"]),
            "tip": tip_for(r["name"], files["texts"]),
        }
    return index


@st.cache_resource(max_entries=8, show_spinner=False)
def matched(version, pantry_key, staples_key):
    """Tüm tariflerin dolapla eşleşmesi; dolap değişmedikçe yeniden hesaplanmaz."""
    data = load_data(version)
    return match_recipes(data["pantry"], data["recipes"], data["staples"])


@st.cache_resource(max_entries=8, show_spinner=False)
def diet_allowed(version, diet, allergies_key):
    """Diyet/alerji filtresinden geçen tarif kimlikleri."""
    recipes = load_data(version)["recipes"]
    return {r["id"] for r in filter_by_diet(recipes, diet, list(allergies_key))}


@st.cache_resource(max_entries=8, show_spinner=False)
def equipment_allowed(version, tools_key):
    """Evdeki aletlerle yapılabilen tarif kimlikleri."""
    index = recipe_index(version)
    have = set(tools_key)
    return {rid for rid, info in index.items() if set(info["tools"]) <= have}


VERSION = st.session_state["data_version"]
DATA = load_data(VERSION)
INDEX = recipe_index(VERSION)
pantry = DATA["pantry"]
pantry_items = DATA["pantry_items"]
recipes = DATA["recipes"]
shopping = DATA["shopping"]
staples = DATA["staples"]
all_ingredients = DATA["all_ingredients"]
RECIPES_BY_ID = {r["id"]: r for r in recipes}
PANTRY_KEY = tuple(sorted((n, q, u) for n, (q, u) in pantry.items()))
STAPLES_KEY = tuple(sorted(staples))

# Diyet/alerji ayarları ve pişirme geçmişi (dosyadan)
if "diet_cfg" not in st.session_state:
    st.session_state["diet_cfg"] = load_settings(DIET_FILE)
if "history" not in st.session_state:
    st.session_state["history"] = load_history(HISTORY_FILE)
history = st.session_state["history"]
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0


def persist_history():
    try:
        save_history(HISTORY_FILE, history)
    except OSError:
        st.warning("Geçmiş dosyaya kaydedilemedi.")


def info_of(recipe):
    return INDEX.get(recipe["id"], {})


# ======================================================================
# Kenar çubuğu: bölümler ve genel ayarlar
# ======================================================================
with st.sidebar:
    st.markdown(
        '<div class="brand">Yemek Planlayıcı</div>'
        '<div class="brand-sub">Evdeki malzemelerle yemek planı</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="nav-label">Görünüm</div><div class="theme">', unsafe_allow_html=True)
    st.radio(
        "Görünüm", list(THEMES), key="theme", horizontal=True, label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="nav-label">Bölümler</div>', unsafe_allow_html=True)
    PAGES = ["Tarifler", "Dolabım", "Haftalık plan", "Alışveriş listesi", "Tariflerim"]
    page = st.radio("Bölüm", PAGES, key="nav", label_visibility="collapsed")

    st.markdown('<div class="nav-label">Durum</div>', unsafe_allow_html=True)
    st.caption(
        f"Dolapta {len(pantry_items)} malzeme\n\n"
        f"Alışveriş listesinde {len(shopping)} ürün\n\n"
        f"Pişirdiğin {len(history)} yemek"
    )

    st.markdown('<div class="nav-label">Tercihlerim</div>', unsafe_allow_html=True)
    saved = st.session_state["diet_cfg"]
    diet = st.selectbox(
        "Beslenme tarzı", list(DIETS), index=list(DIETS).index(saved["diet"])
    )
    allergies = st.multiselect(
        "Alerjilerim", list(ALLERGIES), default=saved["allergies"],
        placeholder="Yoksa boş bırak",
    )
    new_cfg = {"diet": diet, "allergies": allergies}
    if new_cfg != saved:
        st.session_state["diet_cfg"] = new_cfg
        try:
            save_settings(DIET_FILE, new_cfg)
        except OSError:
            pass
    profile = st.selectbox("Mutfağımdaki aletler", list(PROFILES))
    if PROFILES[profile] is None:
        available_tools = st.multiselect("Evimde olanlar", TOOLS, default=TOOLS)
    else:
        available_tools = PROFILES[profile]

DIET_OK = diet_allowed(VERSION, diet, tuple(sorted(allergies)))
TOOLS_OK = equipment_allowed(VERSION, tuple(sorted(available_tools)))


# ======================================================================
# Pişirme modu
# ======================================================================
def start_cooking(recipe):
    st.session_state["cooking_id"] = recipe["id"]
    st.session_state["cook_stage"] = "prep"
    st.session_state["cook_step"] = 0
    st.session_state.pop(f"cook_servings_{recipe['id']}", None)
    for key in [k for k in st.session_state if str(k).startswith("cook_check_")]:
        del st.session_state[key]
    st.rerun()


def stop_cooking():
    for k in ("timer_end", "timer_label", "timer_alerted"):
        st.session_state.pop(k, None)
    st.session_state.pop("cooking_id", None)
    st.rerun()


def _timer_panel():
    """Çalışan sayacı gösterir; bitince bip çalar. Her saniye yenilenir."""
    end = st.session_state.get("timer_end")
    if not end:
        return
    label = st.session_state.get("timer_label", "")
    left = end - time.time()
    if left > 0:
        c1, c2 = st.columns([4, 1])
        c1.info(f"{label} · kalan {format_clock(left)}")
        if c2.button("İptal", key="timer_cancel"):
            st.session_state.pop("timer_end", None)
            st.rerun()
    else:
        st.warning(f"Süre doldu: {label}. Yemeğin pişme işaretini kontrol et.")
        if not st.session_state.get("timer_alerted"):
            st.session_state["timer_alerted"] = True
            try:
                st.audio(beep_wav(), format="audio/wav", autoplay=True)
            except TypeError:
                pass
        if st.button("Tamam", key="timer_ok"):
            st.session_state.pop("timer_end", None)
            st.rerun()


def show_timer():
    if st.session_state.get("timer_end"):
        # Sayaç varken panel saniyede bir kendini yeniler; yokken boşuna çalışmaz.
        st.fragment(run_every=1)(_timer_panel)()


def render_cooking(base):
    """Pişirme modu: hazırlık -> adım adım -> bitti (dolap güncelleme)."""
    stage = st.session_state.get("cook_stage", "prep")
    info = info_of(base)
    nut = info.get("nut", recipe_nutrition(base))

    if st.button("← Tariflere dön"):
        stop_cooking()

    st.markdown(page_head(base["name"], info.get("desc", "")), unsafe_allow_html=True)

    servings = st.number_input(
        "Kaç kişilik yapacaksın?",
        min_value=1, max_value=20, value=int(base["servings"]), step=1,
        key=f"cook_servings_{base['id']}",
        disabled=stage != "prep",
        help="Malzeme miktarları kişi sayısına göre otomatik ayarlanır.",
    )
    scaled = scale_recipe(base, servings)
    result = match_recipe(pantry, scaled, staples)
    missing_names = {m["name"] for m in result["missing"]}

    # ---------- Aşama 1: Hazırlık ----------
    if stage == "prep":
        st.markdown(section("Malzemeleri hazırla"), unsafe_allow_html=True)
        st.caption("Hazırladığın malzemeyi işaretle. Parantez içindekiler evde yok sayılanlar.")
        for ing in scaled["ingredients"]:
            name = normalize(ing["name"])
            if name in missing_names:
                note = "  (evde yok)"
            elif name in result["staples"]:
                note = "  (temel malzeme)"
            else:
                note = ""
            st.checkbox(ing["label"] + note, key=f"cook_check_{base['id']}_{name}")

        if result["insufficient"]:
            st.warning(
                "Miktarı yetersiz olabilir: "
                + ", ".join(
                    f"{i['name']} ({format_amount(i['quantity'], i['unit'])} gerekiyor)"
                    for i in result["insufficient"]
                )
            )
        if result["missing"]:
            st.error(
                f"{len(result['missing'])} malzeme evde yok: "
                + ", ".join(m["name"] for m in result["missing"])
            )
            if st.button("Eksikleri alışveriş listesine ekle", use_container_width=True):
                with writing() as session:
                    added = repo.add_shopping_many(session, result["missing"])
                st.toast(f"{len(added)} malzeme alışveriş listesine eklendi.")
                st.rerun()

        if st.button("Pişirmeye başla", type="primary", use_container_width=True):
            st.session_state["cook_stage"] = "steps"
            st.session_state["cook_step"] = 0
            st.rerun()

    # ---------- Aşama 2: Adım adım ----------
    elif stage == "steps":
        steps = scaled["steps"]
        total = len(steps)
        index = min(st.session_state.get("cook_step", 0), total - 1)
        st.progress((index + 1) / total)
        with st.container(border=True):
            st.markdown(step_html(index + 1, total, steps[index]), unsafe_allow_html=True)

            show_timer()
            durations = parse_durations(steps[index])[:3]
            if durations:
                cols = st.columns(len(durations) + 1)
                for k, d in enumerate(durations):
                    if cols[k].button(
                        f"{d['label']} sayacı",
                        key=f"timer_{base['id']}_{index}_{k}",
                        use_container_width=True,
                    ):
                        st.session_state["timer_end"] = time.time() + d["seconds"]
                        st.session_state["timer_label"] = f"Adım {index + 1} · {d['label']}"
                        st.session_state.pop("timer_alerted", None)
                        st.rerun()

        if index == total - 1 and info.get("tip"):
            st.markdown(tip("Püf noktası: " + info["tip"]), unsafe_allow_html=True)

        b1, b2 = st.columns(2)
        if b1.button("← Önceki adım", disabled=index == 0, use_container_width=True):
            st.session_state["cook_step"] = index - 1
            st.rerun()
        if index < total - 1:
            if b2.button("Sonraki adım →", type="primary", use_container_width=True):
                st.session_state["cook_step"] = index + 1
                st.rerun()
        else:
            if b2.button("Bitirdim", type="primary", use_container_width=True):
                st.session_state["cook_entry"] = add_entry(history, base["name"])
                persist_history()
                st.session_state["cook_stage"] = "done"
                st.rerun()

        with st.expander("Malzemeler"):
            for ing in scaled["ingredients"]:
                st.write(ing["label"])

    # ---------- Aşama 3: Bitti ----------
    else:
        st.success("Afiyet olsun.")
        entry = st.session_state.get("cook_entry")
        if entry is not None and entry < len(history):
            options = [None, 1, 2, 3, 4, 5]
            current = history[entry]["rating"]
            rating = st.radio(
                "Nasıl oldu?",
                options,
                index=options.index(current),
                format_func=lambda v: "Puan verme" if v is None else f"{v} puan",
                horizontal=True,
                key=f"rate_{entry}",
            )
            if rating != current:
                set_rating(history, entry, rating)
                persist_history()

        plan_items = plan_deductions(scaled, pantry, staples)
        auto = [p for p in plan_items if p["action"] in ("reduce", "remove")]
        known_names = {p["name"] for p in plan_items}
        manual = [p["name"] for p in plan_items if p["action"] == "unknown"]
        for name in used_pantry_names(result, pantry, staples):
            if name not in known_names:
                manual.append(name)

        if auto or manual:
            st.markdown(section("Dolabını güncelle"), unsafe_allow_html=True)
        apply_auto = []
        if auto:
            st.caption("Kullandığın miktar dolaptan düşülecek; istemediğinin işaretini kaldır.")
            for p in auto:
                have = format_amount(*p["have"])
                if p["action"] == "remove":
                    text = f"{p['name']}: {have} → bitti, dolaptan çıkar"
                else:
                    text = (f"{p['name']}: {have} → {format_amount(*p['left'])} kalır "
                            f"(−{format_amount(*p['used'])})")
                if st.checkbox(text, value=True, key=f"deduct_{entry}_{p['name']}"):
                    apply_auto.append(p)
        finished = []
        if manual:
            finished = st.multiselect(
                "Miktarı bilinmeyenlerden bitenleri seç",
                manual,
                placeholder="Bitenleri seç (boş bırakabilirsin)",
                key=f"finished_{entry}",
            )
        c1, c2 = st.columns(2)
        if (auto or manual) and c1.button(
            "Dolabımı güncelle ve çık", type="primary", use_container_width=True,
            key="deduct_apply",
        ):
            with writing() as session:
                for p in apply_auto:
                    if p["action"] == "remove":
                        repo.remove_pantry(session, p["name"])
                    else:
                        repo.set_pantry_amount(session, p["name"], *p["left"])
                for name in finished:
                    repo.remove_pantry(session, name)
            count = len(apply_auto) + len(finished)
            if count:
                st.toast(f"{count} malzeme güncellendi.")
            stop_cooking()
        if c2.button("Güncellemeden çık", use_container_width=True, key="deduct_skip"):
            stop_cooking()


# ======================================================================
# Bölüm: Tarifler
# ======================================================================
def page_recipes():
    cooking_recipe = RECIPES_BY_ID.get(st.session_state.get("cooking_id"))
    if cooking_recipe is not None:
        render_cooking(cooking_recipe)
        return

    st.markdown(
        page_head(
            "Tarifler",
            "Dolabındakilere en çok uyan tarifler önce gelir. "
            "Eksik malzemeyi tek dokunuşla alışveriş listesine ekleyebilirsin.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        stats_html([
            (len(pantry_items), "dolaptaki malzeme"),
            (len(recipes), "tarif"),
            (len(shopping), "alışveriş listesi"),
            (len(history), "pişirdiğin yemek"),
        ]),
        unsafe_allow_html=True,
    )

    if not pantry:
        st.info(
            "Önce Dolabım bölümünde evdeki malzemeleri seç. "
            "Dilersen 'Yalnızca evdekilerle' anahtarını kapatıp tüm tariflere de bakabilirsin."
        )

    # --- Öğün ---
    st.markdown('<div class="meal">', unsafe_allow_html=True)
    meal = st.radio(
        "Öğün", ["Tümü"] + CATEGORIES, horizontal=True, key="meal_cat",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Arama, sıralama, filtreler ---
    sort_labels = {
        **SORT_LABELS,
        "kcal": "Kalori (az → çok)",
        "protein": "Protein (çok → az)",
        "rating": "Puanım (yüksek → düşük)",
        "last": "Uzun süredir yapmadıklarım",
    }
    c1, c2 = st.columns([3, 2])
    query = c1.text_input(
        "Tarif ara", placeholder="Tarif ya da malzeme ara", label_visibility="collapsed"
    )
    sort_by = c2.selectbox(
        "Sırala", list(sort_labels), format_func=lambda k: f"Sırala: {sort_labels[k]}",
        label_visibility="collapsed",
    )
    c3, c4, c5 = st.columns([2.2, 1.5, 1.5])
    only_matching = c3.toggle("Yalnızca evdekilerle", value=True)
    favorites_only = c4.toggle("Favorilerim")
    with c5.popover("Filtreler", use_container_width=True):
        max_time = st.selectbox(
            "En fazla süre", [None, 15, 30, 45, 60],
            format_func=lambda m: "Fark etmez" if m is None else f"{m} dakika",
        )
        max_kcal = st.selectbox(
            "En fazla kalori (kişi başı)", [None, 300, 400, 500, 600, 800],
            format_func=lambda v: "Fark etmez" if v is None else f"{v} kcal",
        )
        min_protein = st.selectbox(
            "En az protein (kişi başı)", [None, 10, 20, 30, 40],
            format_func=lambda v: "Fark etmez" if v is None else f"{v} g",
        )

    # --- Süzme (önbellekli eşleşme üzerinden) ---
    allowed = {r["id"] for r in filter_recipes(recipes, query, max_time, favorites_only)}
    allowed &= DIET_OK
    allowed &= TOOLS_OK
    if meal != "Tümü":
        allowed &= {rid for rid, info in INDEX.items() if info["category"] == meal}
    if max_kcal:
        allowed &= {rid for rid, i in INDEX.items() if i["nut"]["per_serving"] <= max_kcal}
    if min_protein:
        allowed &= {rid for rid, i in INDEX.items() if i["nut"]["protein"] >= min_protein}

    all_results = [r for r in matched(VERSION, PANTRY_KEY, STAPLES_KEY)
                   if r["recipe"]["id"] in allowed]
    if only_matching:
        results = [r for r in all_results if r["ratio"] > 0 and r["have"]]
    else:
        results = all_results
    hidden_by_pantry = len(all_results) - len(results)

    if sort_by in ("kcal", "protein"):
        results = sort_by_nutrition(results, sort_by)
    elif sort_by in ("rating", "last"):
        results = sort_by_history(results, history, sort_by)
    else:
        results = sort_results(results, sort_by)

    signature = (query, meal, max_time, only_matching, favorites_only, sort_by,
                 max_kcal, min_protein, profile, tuple(available_tools), diet, tuple(allergies))
    if st.session_state.get("recipe_signature") != signature:
        st.session_state["recipe_signature"] = signature
        st.session_state["recipe_limit"] = PAGE_SIZE
    limit = st.session_state.get("recipe_limit", PAGE_SIZE)

    # --- Bugün ne pişireyim? ---
    if pantry:
        with st.container(border=True):
            st.markdown(section("Bugün ne pişireyim?"), unsafe_allow_html=True)
            o1, o2, o3 = st.columns([1.5, 1.5, 1.2])
            sug_quick = o1.toggle("En fazla 30 dakika", key="sug_quick")
            sug_complete = o2.toggle("Eksiksiz olanlar", key="sug_complete", value=True)
            label = "Başka öner" if st.session_state.get("sug_name") else "Öner"
            if o3.button(label, type="primary", use_container_width=True, key="sug_go"):
                cand = [r for r in all_results if r["ratio"] > 0 and r["have"]]
                seen = st.session_state.setdefault("sug_seen", [])
                pick = suggest(cand, history, exclude=seen,
                               max_time=30 if sug_quick else None, only_complete=sug_complete)
                if pick is None and seen:
                    st.session_state["sug_seen"] = []
                    pick = suggest(cand, history, max_time=30 if sug_quick else None,
                                   only_complete=sug_complete)
                if pick is None:
                    st.session_state.pop("sug_name", None)
                    st.session_state["sug_empty"] = True
                else:
                    st.session_state["sug_empty"] = False
                    st.session_state["sug_name"] = pick["recipe"]["name"]
                    st.session_state["sug_seen"].append(pick["recipe"]["name"])
            if st.session_state.get("sug_empty"):
                st.caption(
                    "Bu seçeneklerle uygun tarif bulamadım. 'Eksiksiz olanlar'ı kapatmayı "
                    "ya da dolabına malzeme eklemeyi dene."
                )
            chosen = next(
                (r for r in recipes if r["name"] == st.session_state.get("sug_name")), None
            )
            if chosen is not None:
                res = match_recipe(pantry, chosen, staples)
                info = info_of(chosen)
                st.markdown(
                    row_title(chosen["name"], "tamamı evde" if not res["missing"] else "",
                              full=not res["missing"]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    meta_line([
                        f"{chosen['time_min']} dk",
                        f"{chosen['servings']} kişilik",
                        f"{info['nut']['per_serving']} kcal / kişi",
                    ]),
                    unsafe_allow_html=True,
                )
                if info.get("desc"):
                    st.markdown(lead(info["desc"]), unsafe_allow_html=True)
                if res["missing"]:
                    st.markdown(
                        badges([(f"eksik: {', '.join(m['name'] for m in res['missing'])}", "miss")]),
                        unsafe_allow_html=True,
                    )
                if st.button("Bunu pişirelim", key="sug_cook", type="primary"):
                    start_cooking(chosen)

    # --- Sonuç özeti ---
    note = f"{len(results)} tarif"
    extras = []
    if meal != "Tümü":
        extras.append(meal.lower())
    if only_matching and hidden_by_pantry:
        extras.append(f"{hidden_by_pantry} tarif eksik malzeme yüzünden gizli")
    if extras:
        note += " · " + " · ".join(extras)
    st.markdown(section(note), unsafe_allow_html=True)

    if not results:
        st.markdown(
            empty_html(
                "Bu seçimlere uyan tarif yok",
                "Aramayı değiştir, filtreleri gevşet ya da 'Yalnızca evdekilerle' anahtarını kapat.",
            ),
            unsafe_allow_html=True,
        )

    # --- Tarif kartları ---
    for r in results[:limit]:
        recipe = r["recipe"]
        info = info_of(recipe)
        nut = info["nut"]
        pct = int(r["ratio"] * 100)
        complete = not r["missing"]
        is_open = st.session_state.get("open_recipe") == recipe["id"]

        with st.container(border=True):
            st.markdown(
                row_title(
                    recipe["name"],
                    "tamamı evde" if complete and pantry else f"%{pct} uyum",
                    full=complete and bool(pantry),
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                meta_line([
                    f"{recipe['time_min']} dk",
                    f"{recipe['servings']} kişilik",
                    f"{nut['per_serving']} kcal / kişi",
                    f"{nut['protein']} g protein",
                ]),
                unsafe_allow_html=True,
            )
            if pantry:
                st.markdown(bar(r["ratio"]), unsafe_allow_html=True)
            if info.get("desc"):
                st.markdown(lead(info["desc"]), unsafe_allow_html=True)

            marks = []
            if recipe["is_favorite"]:
                marks.append(("favori", "warn"))
            if pantry:
                if r["missing"]:
                    names = ", ".join(m["name"] for m in r["missing"][:4])
                    more = f" +{len(r['missing']) - 4}" if len(r["missing"]) > 4 else ""
                    marks.append((f"eksik: {names}{more}", "miss"))
                else:
                    marks.append(("gereken her şey evde", "ok"))
            hs = stats(history, recipe["name"])
            if hs["count"]:
                avg = f" · {str(hs['avg']).replace('.', ',')} puan" if hs["avg"] else ""
                marks.append((f"{hs['count']} kez yaptın{avg}", "neutral"))
            if info.get("contains"):
                marks.append((f"içerir: {info['contains']}", "warn"))
            if marks:
                st.markdown(badges(marks), unsafe_allow_html=True)

            b1, b2 = st.columns([1, 1])
            if b1.button("Pişirmeye başla", key=f"cook_{recipe['id']}",
                         type="primary", use_container_width=True):
                start_cooking(recipe)
            if r["missing"]:
                if b2.button("Eksikleri listeye ekle", key=f"add_{recipe['id']}",
                             use_container_width=True):
                    with writing() as session:
                        added = repo.add_shopping_many(session, r["missing"])
                    st.session_state["open_recipe"] = recipe["id"]
                    st.toast(f"{len(added)} malzeme alışveriş listesine eklendi.")
                    st.rerun()
            elif b2.button("Tarifi gör", key=f"open_{recipe['id']}", use_container_width=True):
                st.session_state["open_recipe"] = (
                    None if is_open else recipe["id"]
                )
                st.rerun()

            with st.expander("Tarifi gör", expanded=is_open):
                render_recipe_detail(r, recipe, info)

    if len(results) > limit:
        remaining = len(results) - limit
        if st.button(f"Daha fazla göster ({remaining} tarif daha)", use_container_width=True):
            st.session_state["recipe_limit"] = limit + PAGE_SIZE
            st.rerun()


def render_recipe_detail(r, recipe, info):
    """Kart içindeki ayrıntı: malzemeler, yapılışı, besin değerleri."""
    nut = info["nut"]
    st.markdown(section("Malzemeler"), unsafe_allow_html=True)
    for ing in recipe["ingredients"]:
        if ing["name"] in r["staples"]:
            note = "  (temel malzeme)"
        elif ing["name"] in r["have"]:
            note = ""
        else:
            note = "  (evde yok)"
        st.write(ing["label"] + note)

    if r["insufficient"]:
        st.warning(
            "Miktarı yetersiz olabilir: "
            + ", ".join(
                f"{i['name']} ({format_amount(i['quantity'], i['unit'])} gerekiyor)"
                for i in r["insufficient"]
            )
        )

    st.markdown(section("Yapılışı"), unsafe_allow_html=True)
    for n, step in enumerate(recipe["steps"], start=1):
        st.markdown(f"**{n}.** {step}")
    if info.get("tip"):
        st.markdown(tip("Püf noktası: " + info["tip"]), unsafe_allow_html=True)

    st.markdown(section("Kişi başı yaklaşık değerler"), unsafe_allow_html=True)
    st.markdown(
        kv_html([
            ("Kalori", f"{nut['per_serving']} kcal"),
            ("Protein", f"{nut['protein']} g"),
            ("Karbonhidrat", f"{nut['carbs']} g"),
            ("Yağ", f"{nut['fat']} g"),
            ("Gereken aletler", ", ".join(info["tools"]) if info["tools"] else "pişirme gerekmez"),
        ]),
        unsafe_allow_html=True,
    )
    if nut["unknown"]:
        st.caption("Besin hesabına katılmayanlar: " + ", ".join(nut["unknown"]))

    fav = "Favorilerden çıkar" if recipe["is_favorite"] else "Favorilere ekle"
    if st.button(fav, key=f"fav2_{recipe['id']}", use_container_width=True):
        with writing() as session:
            repo.toggle_favorite(session, recipe["id"])
        st.session_state["open_recipe"] = recipe["id"]
        st.rerun()


# ======================================================================
# Bölüm: Dolabım
# ======================================================================
def page_pantry():
    st.markdown(
        page_head(
            "Dolabım",
            "Evde olanları işaretle. Tarifler bu listeye göre sıralanır; "
            "temel malzemeler eksik sayılmaz.",
        ),
        unsafe_allow_html=True,
    )
    pantry_names = [item["name"] for item in pantry_items]
    pantry_set = set(pantry_names)
    groups = catalog_groups()
    known = {n for items in groups.values() for n in items}

    def quick_add():
        picked = st.session_state.get("quick_add", [])
        if picked:
            with writing() as session:
                for name in picked:
                    repo.add_pantry(session, name)
        st.session_state["quick_add"] = []

    options = sorted((set(catalog_names()) | set(all_ingredients)) - pantry_set, key=turkish_key)
    st.multiselect(
        "Hızlı ekle", options, key="quick_add", on_change=quick_add,
        placeholder="Yazarak ara ve ekle: domates, tavuk, süt…",
        label_visibility="collapsed",
    )

    st.markdown(section("Hazır paketler"), unsafe_allow_html=True)
    preset_cols = st.columns(3)
    for i, (label, items) in enumerate(PRESETS.items()):
        clean = PLAIN.sub("", label).strip()
        if preset_cols[i % 3].button(clean, key=f"preset_{i}", use_container_width=True):
            with writing() as session:
                for name in items:
                    if name not in pantry_set:
                        repo.add_pantry(session, name)
            st.rerun()

    st.markdown(section("Kategoriler"), unsafe_allow_html=True)
    chosen = set()
    for cat, items in groups.items():
        have = sorted((n for n in items if n in pantry_set), key=turkish_key)
        title = f"{cat} ({len(have)})" if have else cat
        with st.expander(title):
            picked = st.multiselect(
                cat, sorted(items, key=turkish_key), default=have,
                placeholder="Evde olanları seç", label_visibility="collapsed",
            )
            chosen |= set(picked)

    other = sorted((n for n in pantry_names if n not in known), key=turkish_key)
    if other:
        with st.expander(f"Kendi eklediklerim ({len(other)})"):
            picked_other = st.multiselect(
                "Diğer", other, default=other, label_visibility="collapsed"
            )
            chosen |= set(picked_other)

    if chosen != pantry_set:
        with writing() as session:
            for name in chosen - pantry_set:
                repo.add_pantry(session, name)
            for name in pantry_set - chosen:
                repo.remove_pantry(session, name)
        st.rerun()

    with st.form("add_pantry_form", clear_on_submit=True):
        f1, f2 = st.columns([4, 1])
        new_item = f1.text_input(
            "Listede yoksa yaz", placeholder="Listede yok mu? Buraya yaz (virgülle birden fazla)",
            label_visibility="collapsed",
        )
        submitted = f2.form_submit_button("Ekle", use_container_width=True)
    if submitted and new_item.strip():
        with writing() as session:
            repo.add_pantry_many(session, new_item)
        st.rerun()

    if not pantry_names:
        st.markdown(
            empty_html(
                "Dolabın boş",
                "Yukarıdan yazarak ekle, bir kategoriyi aç ya da hazır paketlerden birini kullan.",
            ),
            unsafe_allow_html=True,
        )
        return

    st.markdown(section(f"Seçili malzemeler ({len(pantry_names)})"), unsafe_allow_html=True)
    st.write(", ".join(sorted(pantry_names, key=turkish_key)))

    with st.expander(f"Temel malzemeler ({len(staples)})"):
        st.caption(
            "Tuz, yağ, baharat gibi hep evde bulunanlar. Eksik sayılmaz, "
            "alışveriş listesine eklenmez."
        )
        staple_options = sorted(set(STAPLE_CANDIDATES) | set(staples), key=turkish_key)
        chosen_staples = st.multiselect(
            "Temel malzemeler", staple_options, default=staples,
            placeholder="ör. tuz, yağ, şeker", label_visibility="collapsed",
        )
        if sorted(chosen_staples) != sorted(staples):
            with writing() as session:
                repo.set_staples(session, chosen_staples)
            st.rerun()

    with st.expander("Miktarları gir (isteğe bağlı)"):
        st.caption(
            "Miktar girersen yetersiz malzeme uyarısı alırsın ve pişirince "
            "kullandığın kadarı dolaptan düşülür."
        )
        for item in pantry_items:
            col1, col2, col3 = st.columns([3, 1.5, 2])
            col1.write(item["name"])
            quantity = col2.number_input(
                "miktar", min_value=0.0, step=1.0, value=float(item["quantity"] or 0),
                key=f"q_{item['name']}", label_visibility="collapsed",
            )
            unit_options = [NO_UNIT] + UNIT_CHOICES
            unit = col3.selectbox(
                "birim", unit_options,
                index=unit_options.index(item["unit"]) if item["unit"] in UNIT_CHOICES else 0,
                key=f"u_{item['name']}", label_visibility="collapsed",
                placeholder="Birim seç",
            )
            chosen_unit = None if unit == NO_UNIT else unit
            if (quantity or None) != item["quantity"] or chosen_unit != item["unit"]:
                with writing() as session:
                    repo.set_pantry_amount(session, item["name"], quantity or None, chosen_unit)
                st.rerun()

    if st.button("Dolabı tamamen boşalt"):
        with writing() as session:
            for name in pantry_names:
                repo.remove_pantry(session, name)
        st.rerun()


# ======================================================================
# Bölüm: Haftalık plan
# ======================================================================
def page_plan():
    st.markdown(
        page_head(
            "Haftalık plan",
            "Günlere tarif seç; haftanın tüm eksik malzemelerini tek seferde "
            "alışveriş listesine ekle.",
        ),
        unsafe_allow_html=True,
    )
    if "plan" not in st.session_state:
        st.session_state["plan"] = load_plan(PLAN_FILE)
    plan = st.session_state["plan"]
    by_id = RECIPES_BY_ID
    plan_before = repr(plan)

    plan["servings"] = int(st.number_input(
        "Kaç kişilik?", min_value=1, max_value=20, value=plan["servings"], step=1,
        key="plan_servings",
    ))

    option_ids = [rid for rid in by_id if rid in DIET_OK]
    for day in DAYS:
        key = f"plan_day_{day}"
        if key not in st.session_state:
            st.session_state[key] = [i for i in plan["days"][day] if i in by_id]
        picked = st.session_state[key]
        chosen = st.multiselect(
            day,
            option_ids + [i for i in picked if i not in DIET_OK],
            format_func=lambda rid: by_id[rid]["name"],
            key=key, placeholder="Tarif seç",
        )
        plan["days"][day] = chosen
        if chosen:
            kcal = sum(INDEX[i]["nut"]["per_serving"] for i in chosen if i in INDEX)
            st.caption(f"Kişi başı yaklaşık {round(kcal)} kcal")

    if repr(plan) != plan_before:
        try:
            save_plan(PLAN_FILE, plan)
        except OSError:
            st.warning("Plan dosyaya kaydedilemedi; sayfayı yenileyince kaybolabilir.")

    if planned_recipes(plan, by_id):
        st.markdown(section("Bu hafta için eksikler"), unsafe_allow_html=True)
        merged = merged_shopping_recipe(plan, by_id)
        week = match_recipe(pantry, merged, staples)
        if week["missing"] or week["insufficient"]:
            for m in week["missing"]:
                st.write(m.get("label", m["name"]))
            for i in week["insufficient"]:
                st.write(
                    f"{i['name']}: {format_amount(i['quantity'], i['unit'])} gerekiyor "
                    "(dolapta yetersiz)"
                )
            if week["missing"] and st.button(
                "Eksikleri alışveriş listesine ekle", type="primary", key="plan_add"
            ):
                with writing() as session:
                    added = repo.add_shopping_many(session, week["missing"])
                st.toast(f"{len(added)} malzeme alışveriş listesine eklendi.")
                st.rerun()
        else:
            st.success("Plandaki her şey dolabında var.")
        if st.button("Planı temizle", key="plan_clear"):
            for day in DAYS:
                st.session_state.pop(f"plan_day_{day}", None)
                plan["days"][day] = []
            save_plan(PLAN_FILE, plan)
            st.rerun()

    st.markdown(section("Yaptıkların"), unsafe_allow_html=True)
    if not history:
        st.caption("Henüz bir tarif bitirmedin. Pişirme ekranında 'Bitirdim'e bastıkça burada birikir.")
    else:
        best = top_rated(history)
        if best:
            st.markdown("**En çok puan alanlar**")
            for name, avg, count in best:
                st.write(f"{name} — {str(avg).replace('.', ',')} puan ({count} kez)")
        st.markdown("**Son yaptıkların**")
        for _, e in recent(history, 15):
            stars = f"{e['rating']} puan" if e["rating"] else "puan yok"
            st.write(f"{format_date(e['date'])} · {e['name']} · {stars}")


# ======================================================================
# Bölüm: Alışveriş listesi
# ======================================================================
def page_shopping():
    st.markdown(
        page_head(
            "Alışveriş listesi",
            "Reyonlara göre sıralı. Aldığın malzemeye 'Aldım' de; dolabına eklenir.",
        ),
        unsafe_allow_html=True,
    )
    if not shopping:
        st.markdown(
            empty_html(
                "Listen boş",
                "Bir tarifte 'Eksikleri listeye ekle' düğmesine basınca eksikler buraya gelir.",
            ),
            unsafe_allow_html=True,
        )
        return

    with st.expander("Listeyi kopyala veya indir"):
        text = shopping_to_text(shopping)
        st.caption("Sağ üstteki simgeyle kopyalayıp mesaj olarak gönderebilirsin.")
        st.code(text, language=None)
        st.download_button(
            "Metin dosyası olarak indir", text, file_name="alisveris-listesi.txt"
        )

    for aisle, group in group_by_aisle(shopping):
        st.markdown(section(aisle.split(" ", 1)[-1]), unsafe_allow_html=True)
        for item in group:
            col1, col2 = st.columns([4, 1.2])
            col1.write(item["label"])
            if col2.button("Aldım", key=f"buy_{item['name']}", use_container_width=True):
                with writing() as session:
                    repo.add_pantry(session, item["name"], item["quantity"], item["unit"])
                st.rerun()


# ======================================================================
# Bölüm: Tariflerim
# ======================================================================
def page_manage():
    st.markdown(
        page_head("Tariflerim", "Kendi tarifini ekle ya da var olan bir tarifi düzenle."),
        unsafe_allow_html=True,
    )
    if "manage_next" in st.session_state:
        st.session_state["manage_choice"] = st.session_state.pop("manage_next")

    recipe_names = {r["id"]: r["name"] for r in recipes}
    choice = st.selectbox(
        "Düzenlenecek tarif", [None] + list(recipe_names),
        format_func=lambda rid: "Yeni tarif" if rid is None else recipe_names[rid],
        key="manage_choice",
    )
    if choice is None:
        current = {"id": None, "name": "", "time_min": 15, "servings": 2,
                   "ingredients": [], "steps": []}
    else:
        current = RECIPES_BY_ID[choice]

    form_key = f"recipe_form_{current['id'] or 'new'}_{st.session_state['form_version']}"
    with st.form(form_key):
        name = st.text_input("Tarif adı", value=current["name"])
        c1, c2 = st.columns(2)
        time_min = c1.number_input(
            "Hazırlama süresi (dk)", min_value=0, step=5, value=int(current["time_min"])
        )
        servings = c2.number_input(
            "Kaç kişilik", min_value=1, step=1, value=int(current["servings"])
        )
        st.caption("Malzemeler — satır eklemek için tablonun altındaki artı işaretini kullan.")
        table = pd.DataFrame(
            [{"name": i["name"], "quantity": i["quantity"], "unit": i["unit"]}
             for i in current["ingredients"]],
            columns=["name", "quantity", "unit"],
        )
        edited = st.data_editor(
            table, num_rows="dynamic", use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Malzeme"),
                "quantity": st.column_config.NumberColumn("Miktar", min_value=0.0, step=0.5),
                "unit": st.column_config.SelectboxColumn("Birim", options=UNIT_CHOICES),
            },
            key=f"ingredients_{form_key}",
        )
        steps_text = st.text_area(
            "Yapılışı (her satıra bir adım)", value="\n".join(current["steps"]), height=180
        )
        save = st.form_submit_button("Kaydet", type="primary")

    if save:
        data = {"name": name, "time_min": time_min, "servings": servings,
                "ingredients": edited.to_dict("records"), "steps": steps_text}
        try:
            with writing() as session:
                saved_id = repo.save_recipe(session, data, current["id"])
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["form_version"] += 1
            st.session_state["manage_next"] = saved_id
            st.toast("Tarif kaydedildi.")
            st.rerun()

    if current["id"] is not None:
        with st.expander("Tarifi sil"):
            st.warning("Bu işlem geri alınamaz.")
            confirm = st.checkbox(
                f"Evet, '{current['name']}' tarifini silmek istiyorum",
                key=f"confirm_{current['id']}",
            )
            if st.button("Tarifi sil", disabled=not confirm, key=f"delete_{current['id']}"):
                with writing() as session:
                    repo.delete_recipe(session, current["id"])
                st.session_state["form_version"] += 1
                st.session_state["manage_next"] = None
                st.toast("Tarif silindi.")
                st.rerun()


PAGE_FUNCS = {
    "Tarifler": page_recipes,
    "Dolabım": page_pantry,
    "Haftalık plan": page_plan,
    "Alışveriş listesi": page_shopping,
    "Tariflerim": page_manage,
}
PAGE_FUNCS[page]()
