from pathlib import Path

import streamlit as st

from core import repository as repo
from core.db import get_session, init_db
from core.matcher import match_recipes

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
    pantry = repo.list_pantry(session)
    recipes = repo.list_recipes(session)

st.title("🍳 Yemek Planlayıcı")

tab_pantry, tab_recipes, tab_shopping = st.tabs(
    ["Evdeki malzemeler", "Önerilen tarifler", "Alışveriş listesi"]
)

# --- Sekme 1: Evdeki malzemeler ---
with tab_pantry:
    with st.form("add_pantry_form", clear_on_submit=True):
        new_item = st.text_input("Malzeme ekle")
        submitted = st.form_submit_button("Ekle")
    if submitted:
        with get_session() as session:
            repo.add_pantry(session, new_item)
        st.rerun()

    if not pantry:
        st.write("Henüz malzeme eklemedin.")

    for item in pantry:
        col1, col2 = st.columns([4, 1])
        col1.write(item)
        if col2.button("Sil", key=f"del_{item}"):
            with get_session() as session:
                repo.remove_pantry(session, item)
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
                st.write("**Yapılışı:**")
                for n, step in enumerate(recipe["steps"], start=1):
                    st.write(f"{n}. {step}")
                if r["missing"] and st.button(
                    "Eksikleri listeye ekle", key=f"add_{recipe['id']}"
                ):
                    with get_session() as session:
                        for m in r["missing"]:
                            repo.add_shopping(session, m)
                    st.success("Alışveriş listesine eklendi!")

# --- Sekme 3: Alışveriş listesi ---
with tab_shopping:
    with get_session() as session:
        shopping = repo.list_shopping(session)

    if not shopping:
        st.write("Liste boş.")

    for item in shopping:
        col1, col2 = st.columns([4, 1])
        col1.write(item)
        if col2.button("Aldım", key=f"buy_{item}"):
            with get_session() as session:
                repo.remove_shopping(session, item)
                repo.add_pantry(session, item)
            st.rerun()