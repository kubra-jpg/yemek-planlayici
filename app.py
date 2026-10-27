import json
from pathlib import Path

import streamlit as st

from core.matcher import match_recipes, normalize

st.set_page_config(page_title="Yemek Planlayıcı", page_icon="🍳")

# --- Veri yükleme ---
@st.cache_data
def load_recipes():
    path = Path(__file__).parent / "data" / "recipes.json"
    return json.loads(path.read_text(encoding="utf-8"))


recipes = load_recipes()

# --- Oturum durumu (sayfa yenilense de listeler korunur) ---
if "pantry" not in st.session_state:
    st.session_state.pantry = []
if "shopping" not in st.session_state:
    st.session_state.shopping = []

st.title("🍳 Yemek Planlayıcı")

tab_pantry, tab_recipes, tab_shopping = st.tabs(
    ["Evdeki malzemeler", "Önerilen tarifler", "Alışveriş listesi"]
)

# --- Sekme 1: Evdeki malzemeler ---
with tab_pantry:
    new_item = st.text_input("Malzeme ekle", key="new_item")
    if st.button("Ekle"):
        item = normalize(new_item)
        if item and item not in st.session_state.pantry:
            st.session_state.pantry.append(item)
        st.rerun()

    if not st.session_state.pantry:
        st.write("Henüz malzeme eklemedin.")

    for item in list(st.session_state.pantry):
        col1, col2 = st.columns([4, 1])
        col1.write(item)
        if col2.button("Sil", key=f"del_{item}"):
            st.session_state.pantry.remove(item)
            st.rerun()

# --- Sekme 2: Önerilen tarifler ---
with tab_recipes:
    if not st.session_state.pantry:
        st.info("Önce 'Evdeki malzemeler' sekmesinden malzeme ekle.")
    else:
        results = match_recipes(st.session_state.pantry, recipes)
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
                    for m in r["missing"]:
                        if m not in st.session_state.shopping:
                            st.session_state.shopping.append(m)
                    st.success("Alışveriş listesine eklendi!")

# --- Sekme 3: Alışveriş listesi ---
with tab_shopping:
    if not st.session_state.shopping:
        st.write("Liste boş.")

    for item in list(st.session_state.shopping):
        col1, col2 = st.columns([4, 1])
        col1.write(item)
        if col2.button("Aldım", key=f"buy_{item}"):
            st.session_state.shopping.remove(item)
            if item not in st.session_state.pantry:
                st.session_state.pantry.append(item)
            st.rerun()