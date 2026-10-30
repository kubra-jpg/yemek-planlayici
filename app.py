from pathlib import Path

import streamlit as st

from core import repository as repo
from core.db import get_session, init_db
from core.matcher import match_recipes
from core.units import UNIT_CHOICES

DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(page_title="Yemek Planlayıcı", page_icon="🍳")


@st.cache_resource
def setup_database():
    """Tabloları oluşturur; tarifler boşsa JSON'dan yükler (açılışta bir kez)."""
    init_db()
    with get_session() as session:
        repo.seed_recipes_if_empty(session, DATA_DIR / "recipes.json")


setup_database()

# --- Veritabanından güncel verileri oku ---
with get_session() as session:
    pantry = repo.pantry_as_dict(session)
    pantry_items = repo.list_pantry_items(session)
    recipes = repo.list_recipes(session)
    shopping = repo.list_shopping(session)

st.title("🍳 Yemek Planlayıcı")

tab_pantry, tab_recipes, tab_shopping = st.tabs(
    ["Evdeki malzemeler", "Önerilen tarifler", "Alışveriş listesi"]
)

# --- Sekme 1: Evdeki malzemeler ---
with tab_pantry:
    with st.form("add_pantry_form", clear_on_submit=True):
        new_item = st.text_input(
            "Malzeme ekle",
            placeholder="domates, soğan, yumurta",
            help="Birden fazla malzemeyi virgülle ayırabilirsin.",
        )
        submitted = st.form_submit_button("Ekle")
    if submitted:
        with get_session() as session:
            repo.add_pantry_many(session, new_item)
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
    if not pantry:
        st.info("Önce 'Evdeki malzemeler' sekmesinden malzeme ekle.")
    else:
        results = match_recipes(pantry, recipes)
        for r in results:
            recipe = r["recipe"]
            pct = int(r["ratio"] * 100)
            with st.expander(f"{recipe['name']} — %{pct} eşleşme"):
                st.write(f"⏱ {recipe['time_min']} dk | 👥 {recipe['servings']} kişilik")
                st.write("**Elimde olanlar:** " + (", ".join(r["have"]) or "-"))
                st.write("**Eksikler:** " + (", ".join(r["missing"]) or "-"))
                if r["insufficient"]:
                    st.warning(
                        "Miktarı yetersiz olabilir: " + ", ".join(r["insufficient"])
                    )
                st.write("**Yapılışı:**")
                for n, step in enumerate(recipe["steps"], start=1):
                    st.write(f"{n}. {step}")
                if r["missing"] and st.button(
                    "Eksikleri listeye ekle", key=f"add_{recipe['id']}"
                ):
                    with get_session() as session:
                        repo.add_shopping_many(session, r["missing"])
                    st.success(
                        f"{len(r['missing'])} malzeme alışveriş listesine eklendi!"
                    )

# --- Sekme 3: Alışveriş listesi ---
with tab_shopping:
    if not shopping:
        st.write("Liste boş.")

    for item in shopping:
        col1, col2 = st.columns([4, 1])
        col1.write(item)
        if col2.button("Aldım", key=f"buy_{item}"):
            with get_session() as session:
                repo.add_pantry(session, item)
            st.rerun()