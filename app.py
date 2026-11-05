from pathlib import Path

import pandas as pd
import streamlit as st

from core import repository as repo
from core.catalog import catalog_names
from core.db import get_session, init_db
from core.filters import SORT_LABELS, filter_recipes, sort_results, turkish_key
from core.equipment import (
    PROFILES,
    TOOLS,
    filter_by_equipment,
    load_overrides,
    tools_for,
)
from core.goals import filter_by_goals, sort_by_nutrition
from core.matcher import match_recipes
from core.nutrition import recipe_nutrition
from core.staples import STAPLE_CANDIDATES
from core.units import UNIT_CHOICES, format_amount

DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(page_title="Yemek Planlayıcı", page_icon="🍳")


@st.cache_resource
def setup_database():
    """Tabloları oluşturur; tarifler boşsa JSON'dan yükler (açılışta bir kez)."""
    init_db()
    with get_session() as session:
        repo.seed_recipes_if_empty(session, DATA_DIR / "recipes.json")


setup_database()


@st.cache_data
def equipment_overrides():
    """data/equipment.json: tarif adına göre gereken aletler (açılışta bir kez okunur)."""
    return load_overrides()


# Tarif formunun her kayıttan sonra temiz açılması için sürüm sayacı
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# --- Veritabanından güncel verileri oku ---
with get_session() as session:
    pantry = repo.pantry_as_dict(session)
    pantry_items = repo.list_pantry_items(session)
    recipes = repo.list_recipes(session)
    shopping = repo.list_shopping_items(session)
    staples = repo.list_staples(session)
    all_ingredients = repo.list_all_ingredient_names(session)

st.title("🍳 Yemek Planlayıcı")

tab_pantry, tab_recipes, tab_shopping, tab_manage = st.tabs(
    ["Evdeki malzemeler", "Önerilen tarifler", "Alışveriş listesi", "Tarifleri yönet"]
)


# --- Sekme 1: Evdeki malzemeler ---
with tab_pantry:
    catalog_options = sorted(set(catalog_names()) | set(all_ingredients), key=turkish_key)
    with st.form("add_pantry_form", clear_on_submit=True):
        picked = st.multiselect(
            "Listeden seç",
            [n for n in catalog_options if n not in pantry],
            placeholder="Yazarak ara: ör. mercimek, tavuk, süt",
        )
        new_item = st.text_input(
            "Listede yoksa elle yaz",
            placeholder="domates, soğan, yumurta",
            help="Birden fazla malzemeyi virgülle ayırabilirsin.",
        )
        submitted = st.form_submit_button("Ekle")
    if submitted:
        text = ", ".join(picked + ([new_item] if new_item.strip() else []))
        with get_session() as session:
            repo.add_pantry_many(session, text)
        st.rerun()

    with st.expander(f"🧂 Temel malzemeler ({len(staples)})"):
        st.caption(
            "Bu malzemeler her zaman evde var sayılır: eşleşme oranına katılmaz, "
            "eksik görünmez ve alışveriş listesine eklenmez."
        )
        staple_options = sorted(set(STAPLE_CANDIDATES) | set(staples), key=turkish_key)
        chosen_staples = st.multiselect(
            "Temel malzemeler",
            staple_options,
            default=staples,
            placeholder="ör. tuz, yağ, şeker",
            label_visibility="collapsed",
        )
        if sorted(chosen_staples) != sorted(staples):
            with get_session() as session:
                repo.set_staples(session, chosen_staples)
            st.rerun()

    if not pantry_items:
        st.write("Henüz malzeme eklemedin.")

    for item in pantry_items:
        col1, col2, col3, col4 = st.columns([3, 1.2, 1.5, 1])
        col1.write(item["name"])
        quantity = col2.number_input(
            "miktar",
            min_value=0.0,
            step=1.0,
            value=float(item["quantity"] or 0),
            key=f"q_{item['name']}",
            label_visibility="collapsed",
        )
        unit = col3.selectbox(
            "birim",
            [""] + UNIT_CHOICES,
            index=([""] + UNIT_CHOICES).index(item["unit"])
            if item["unit"] in UNIT_CHOICES
            else 0,
            key=f"u_{item['name']}",
            label_visibility="collapsed",
        )
        if (quantity or None) != item["quantity"] or (unit or None) != item["unit"]:
            with get_session() as session:
                repo.set_pantry_amount(
                    session, item["name"], quantity or None, unit or None
                )
            st.rerun()
        if col4.button("Sil", key=f"del_{item['name']}"):
            with get_session() as session:
                repo.remove_pantry(session, item["name"])
            st.rerun()

# --- Sekme 2: Önerilen tarifler ---
with tab_recipes:
    # Arama ve filtre çubuğu
    f1, f2 = st.columns([2, 1])
    query = f1.text_input(
        "Ara", placeholder="Tarif ya da malzeme adı (ör. balık, çorba)"
    )
    max_time = f2.selectbox(
        "En fazla süre",
        [None, 15, 30, 45, 60],
        format_func=lambda m: "Fark etmez" if m is None else f"{m} dk",
    )
    f3, f4, f5 = st.columns(3)
    only_matching = f3.toggle("Sadece eşleşenler", value=True)
    favorites_only = f4.toggle("Sadece favoriler")
    sort_labels = {
        **SORT_LABELS,
        "kcal": "Kalori (az → çok)",
        "protein": "Protein (çok → az)",
    }
    sort_by = f5.selectbox("Sırala", list(sort_labels), format_func=sort_labels.get)

    with st.expander("🎯 Hedefler ve mutfak ekipmanı"):
        g1, g2 = st.columns(2)
        max_kcal = g1.selectbox(
            "En fazla kalori (kişi başı)",
            [None, 300, 400, 500, 600, 800],
            format_func=lambda v: "Fark etmez" if v is None else f"{v} kcal",
        )
        min_protein = g2.selectbox(
            "En az protein (kişi başı)",
            [None, 10, 20, 30, 40],
            format_func=lambda v: "Fark etmez" if v is None else f"{v} g",
        )
        profile = st.selectbox("Mutfak profili", list(PROFILES))
        if PROFILES[profile] is None:
            available_tools = st.multiselect("Evimde olanlar", TOOLS, default=TOOLS)
        else:
            available_tools = PROFILES[profile]
            st.caption("Evde var sayılanlar: " + ", ".join(available_tools))

    filtered = filter_recipes(recipes, query, max_time, favorites_only)
    all_results = match_recipes(pantry, filtered, staples)
    if only_matching:
        results = [r for r in all_results if r["ratio"] > 0 and r["have"]]
    else:
        results = all_results
    hidden = len(all_results) - len(results)

    # Beslenme hedefi ve ekipman süzgeçleri
    before_filters = len(results)
    results = filter_by_goals(results, max_kcal, min_protein)
    results = filter_by_equipment(results, available_tools, equipment_overrides())
    goal_hidden = before_filters - len(results)

    if sort_by in ("kcal", "protein"):
        results = sort_by_nutrition(results, sort_by)
    else:
        results = sort_results(results, sort_by)

    if only_matching and not pantry:
        st.info(
            "Evdeki malzemelerine göre öneri için önce malzeme ekle "
            "ya da 'Sadece eşleşenler' anahtarını kapat."
        )
    elif not results:
        st.info("Bu filtrelere uyan tarif bulunamadı.")
    else:
        st.caption(f"{len(results)} tarif bulundu")
    if hidden and pantry:
        st.caption(
            f"Evdeki malzemelerinle eşleşmeyen {hidden} tarif gizlendi. "
            "Görmek için 'Sadece eşleşenler' anahtarını kapat."
        )
    if goal_hidden:
        st.caption(
            f"Kalori, protein ya da ekipman seçimine uymayan {goal_hidden} tarif gizlendi."
        )

    for r in results:
        recipe = r["recipe"]
        nut = recipe_nutrition(recipe)
        tools = tools_for(recipe, equipment_overrides())
        pct = int(r["ratio"] * 100)
        star = "⭐ " if recipe["is_favorite"] else ""
        title = (
            f"{star}{recipe['name']} — %{pct} eşleşme · {recipe['time_min']} dk · "
            f"{nut['per_serving']} kcal"
        )
        is_open = st.session_state.get("open_recipe") == recipe["id"]

        with st.expander(title, expanded=is_open):
            st.write(
                f"⏱ {recipe['time_min']} dk | 👥 {recipe['servings']} kişilik | "
                f"🔥 yaklaşık {nut['per_serving']} kcal / kişi"
            )
            st.write(
                f"💪 Protein {nut['protein']} g · 🍞 Karbonhidrat {nut['carbs']} g · "
                f"🧈 Yağ {nut['fat']} g (kişi başı)"
            )
            st.write(
                "🔧 Gerekenler: " + (", ".join(tools) if tools else "pişirme gerekmez")
            )
            if nut["unknown"]:
                st.caption(
                    "Besin hesabına katılmayan malzemeler: " + ", ".join(nut["unknown"])
                )

            st.write("**Malzemeler:**")
            for ing in recipe["ingredients"]:
                if ing["name"] in r["staples"]:
                    mark = "🧂"
                elif ing["name"] in r["have"]:
                    mark = "✅"
                else:
                    mark = "🛒"
                st.write(f"{mark} {ing['label']}")

            if r["insufficient"]:
                st.warning(
                    "Miktarı yetersiz olabilir: "
                    + ", ".join(
                        f"{i['name']} ({format_amount(i['quantity'], i['unit'])} gerekiyor)"
                        for i in r["insufficient"]
                    )
                )

            st.write("**Yapılışı:**")
            for n, step in enumerate(recipe["steps"], start=1):
                st.write(f"{n}. {step}")

            b1, b2 = st.columns(2)
            fav_label = (
                "★ Favorilerden çıkar" if recipe["is_favorite"] else "☆ Favorilere ekle"
            )
            if b1.button(fav_label, key=f"fav_{recipe['id']}"):
                with get_session() as session:
                    repo.toggle_favorite(session, recipe["id"])
                st.session_state["open_recipe"] = recipe["id"]
                st.rerun()

            if r["missing"] and b2.button(
                "Eksikleri listeye ekle", key=f"add_{recipe['id']}"
            ):
                with get_session() as session:
                    added = repo.add_shopping_many(session, r["missing"])
                st.session_state["open_recipe"] = recipe["id"]
                st.toast(f"{len(added)} malzeme alışveriş listesine eklendi!")
                st.rerun()

# --- Sekme 3: Alışveriş listesi ---
with tab_shopping:
    if not shopping:
        st.write("Liste boş.")

    for item in shopping:
        col1, col2 = st.columns([4, 1])
        col1.write(item["label"])
        if col2.button("Aldım", key=f"buy_{item['name']}"):
            with get_session() as session:
                repo.add_pantry(session, item["name"], item["quantity"], item["unit"])
            st.rerun()

# --- Sekme 4: Tarifleri yönet ---
with tab_manage:
    # Kaydet/sil sonrası hangi tarifin seçili olacağı (seçim kutusu çizilmeden önce ayarlanmalı)
    if "manage_next" in st.session_state:
        st.session_state["manage_choice"] = st.session_state.pop("manage_next")

    recipe_names = {r["id"]: r["name"] for r in recipes}
    choice = st.selectbox(
        "Düzenlenecek tarif",
        [None] + list(recipe_names),
        format_func=lambda rid: "➕ Yeni tarif" if rid is None else recipe_names[rid],
        key="manage_choice",
    )

    if choice is None:
        current = {
            "id": None,
            "name": "",
            "time_min": 15,
            "servings": 2,
            "ingredients": [],
            "steps": [],
        }
    else:
        current = next(r for r in recipes if r["id"] == choice)

    form_key = f"recipe_form_{current['id'] or 'new'}_{st.session_state.form_version}"

    with st.form(form_key):
        name = st.text_input("Tarif adı", value=current["name"])
        c1, c2 = st.columns(2)
        time_min = c1.number_input(
            "Hazırlama süresi (dk)", min_value=0, step=5, value=int(current["time_min"])
        )
        servings = c2.number_input(
            "Kaç kişilik", min_value=1, step=1, value=int(current["servings"])
        )

        st.write("**Malzemeler** (satır eklemek için tablonun altındaki + işaretini kullan)")
        ingredient_table = pd.DataFrame(
            [
                {"name": i["name"], "quantity": i["quantity"], "unit": i["unit"]}
                for i in current["ingredients"]
            ],
            columns=["name", "quantity", "unit"],
        )
        edited = st.data_editor(
            ingredient_table,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Malzeme"),
                "quantity": st.column_config.NumberColumn(
                    "Miktar", min_value=0.0, step=0.5
                ),
                "unit": st.column_config.SelectboxColumn("Birim", options=UNIT_CHOICES),
            },
            key=f"ingredients_{form_key}",
        )

        steps_text = st.text_area(
            "Yapılışı (her satıra bir adım)",
            value="\n".join(current["steps"]),
            height=150,
        )
        save = st.form_submit_button("Kaydet")

    if save:
        data = {
            "name": name,
            "time_min": time_min,
            "servings": servings,
            "ingredients": edited.to_dict("records"),
            "steps": steps_text,
        }
        try:
            with get_session() as session:
                saved_id = repo.save_recipe(session, data, current["id"])
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.form_version += 1
            st.session_state["manage_next"] = saved_id
            st.toast("Tarif kaydedildi!")
            st.rerun()

    if current["id"] is not None:
        with st.expander("🗑 Tarifi sil"):
            st.warning("Bu işlem geri alınamaz.")
            confirm = st.checkbox(
                f"Evet, '{current['name']}' tarifini silmek istiyorum",
                key=f"confirm_{current['id']}",
            )
            if st.button(
                "Tarifi sil", disabled=not confirm, key=f"delete_{current['id']}"
            ):
                with get_session() as session:
                    repo.delete_recipe(session, current["id"])
                st.session_state.form_version += 1
                st.session_state["manage_next"] = None
                st.toast("Tarif silindi.")
                st.rerun()