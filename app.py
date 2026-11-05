from pathlib import Path

import pandas as pd
import streamlit as st

from core import repository as repo
from core.catalog import catalog_names
from core.db import get_session, init_db
from core.equipment import (
    PROFILES,
    TOOLS,
    filter_by_equipment,
    load_overrides,
    tools_for,
)
from core.filters import SORT_LABELS, filter_recipes, sort_results, turkish_key
from core.goals import filter_by_goals, sort_by_nutrition
from core.matcher import match_recipes
from core.nutrition import recipe_nutrition
from core.staples import STAPLE_CANDIDATES
from core.units import UNIT_CHOICES, format_amount

DATA_DIR = Path(__file__).parent / "data"
PAGE_SIZE = 10  # tarif listesinde bir seferde gösterilen tarif sayısı

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
st.caption("Evdeki malzemeleri seç, ne pişirebileceğini gör.")

tab_pantry, tab_recipes, tab_shopping, tab_manage = st.tabs(
    [
        "🥕 Dolabım",
        "🍽 Tarifler",
        f"🛒 Alışveriş ({len(shopping)})" if shopping else "🛒 Alışveriş",
        "✏️ Tariflerim",
    ]
)

# ======================================================================
# Sekme 1: Dolabım
# ======================================================================
with tab_pantry:
    pantry_names = [item["name"] for item in pantry_items]
    options = sorted(
        set(catalog_names()) | set(all_ingredients) | set(pantry_names),
        key=turkish_key,
    )

    st.subheader("Evimdeki malzemeler")
    chosen = st.multiselect(
        "Evimdeki malzemeler",
        options,
        default=pantry_names,
        placeholder="Yazarak ara ve seç: domates, tavuk, süt…",
        label_visibility="collapsed",
        help="Listeden seçtiğin malzemeler 'Tarifler' sekmesinde kullanılır. "
        "Çıkarmak için malzemenin üzerindeki × işaretine bas.",
    )
    if set(chosen) != set(pantry_names):
        with get_session() as session:
            for name in chosen:
                if name not in pantry_names:
                    repo.add_pantry(session, name)
            for name in pantry_names:
                if name not in chosen:
                    repo.remove_pantry(session, name)
        st.rerun()

    if not pantry_names:
        st.info("Henüz malzeme seçmedin. Yukarıdaki kutuya tıkla ve evdeki malzemeleri seç.")
    else:
        st.caption(f"{len(pantry_names)} malzeme seçili. Şimdi **Tarifler** sekmesine geçebilirsin.")

    # Listede olmayan malzeme için küçük form
    with st.form("add_pantry_form", clear_on_submit=True):
        c1, c2 = st.columns([4, 1])
        new_item = c1.text_input(
            "Listede yoksa yaz",
            placeholder="Listede yok mu? Buraya yaz (virgülle birden fazla)",
            label_visibility="collapsed",
        )
        submitted = c2.form_submit_button("Ekle", use_container_width=True)
    if submitted and new_item.strip():
        with get_session() as session:
            repo.add_pantry_many(session, new_item)
        st.rerun()

    st.divider()

    with st.expander(f"🧂 Her zaman evde olanlar ({len(staples)})"):
        st.caption(
            "Tuz, yağ, baharat gibi hep evde bulunan malzemeler. Eksik sayılmaz ve "
            "alışveriş listesine eklenmez."
        )
        staple_options = sorted(set(STAPLE_CANDIDATES) | set(staples), key=turkish_key)
        chosen_staples = st.multiselect(
            "Her zaman evde olanlar",
            staple_options,
            default=staples,
            placeholder="ör. tuz, yağ, şeker",
            label_visibility="collapsed",
        )
        if sorted(chosen_staples) != sorted(staples):
            with get_session() as session:
                repo.set_staples(session, chosen_staples)
            st.rerun()

    if pantry_items:
        with st.expander("📏 Miktarları gir (isteğe bağlı)"):
            st.caption(
                "Miktar girersen yetersiz kalan malzemeler için uyarı alırsın. "
                "Boş bırakırsan malzeme 'yeterli' sayılır."
            )
            for item in pantry_items:
                col1, col2, col3 = st.columns([3, 1.5, 2])
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

# ======================================================================
# Sekme 2: Tarifler
# ======================================================================
with tab_recipes:
    if not pantry:
        st.info(
            "👋 Önce **Dolabım** sekmesinde evdeki malzemeleri seç. "
            "Ya da aşağıdan 'Evimdekilerle yapılabilenler' anahtarını kapatıp tüm tariflere bak."
        )

    sort_labels = {
        **SORT_LABELS,
        "kcal": "Kalori (az → çok)",
        "protein": "Protein (çok → az)",
    }

    # Satır 1: arama ve sıralama
    r1, r2 = st.columns([3, 2])
    query = r1.text_input(
        "Tarif ara",
        placeholder="🔍 Tarif ya da malzeme ara (ör. çorba, tavuk)",
        label_visibility="collapsed",
    )
    sort_by = r2.selectbox(
        "Sırala",
        list(sort_labels),
        format_func=lambda k: f"Sırala: {sort_labels[k]}",
        label_visibility="collapsed",
    )

    # Satır 2: iki ana anahtar ve gelişmiş filtreler
    r3, r4, r5 = st.columns([2.3, 1.5, 1.4])
    only_matching = r3.toggle("Evimdekilerle yapılabilenler", value=True)
    favorites_only = r4.toggle("Favorilerim")
    with r5.popover("⚙️ Filtreler", use_container_width=True):
        max_time = st.selectbox(
            "En fazla süre",
            [None, 15, 30, 45, 60],
            format_func=lambda m: "Fark etmez" if m is None else f"{m} dakika",
        )
        max_kcal = st.selectbox(
            "En fazla kalori (kişi başı)",
            [None, 300, 400, 500, 600, 800],
            format_func=lambda v: "Fark etmez" if v is None else f"{v} kcal",
        )
        min_protein = st.selectbox(
            "En az protein (kişi başı)",
            [None, 10, 20, 30, 40],
            format_func=lambda v: "Fark etmez" if v is None else f"{v} g",
        )
        profile = st.selectbox("Mutfağımda neler var?", list(PROFILES))
        if PROFILES[profile] is None:
            available_tools = st.multiselect("Evimde olanlar", TOOLS, default=TOOLS)
        else:
            available_tools = PROFILES[profile]

    # --- Süzme ve sıralama ---
    filtered = filter_recipes(recipes, query, max_time, favorites_only)
    all_results = match_recipes(pantry, filtered, staples)
    if only_matching:
        results = [r for r in all_results if r["ratio"] > 0 and r["have"]]
    else:
        results = all_results
    hidden_by_pantry = len(all_results) - len(results)

    before = len(results)
    results = filter_by_goals(results, max_kcal, min_protein)
    results = filter_by_equipment(results, available_tools, equipment_overrides())
    hidden_by_filters = before - len(results)

    if sort_by in ("kcal", "protein"):
        results = sort_by_nutrition(results, sort_by)
    else:
        results = sort_results(results, sort_by)

    # Filtre değişince listeyi başa al
    signature = (
        query, max_time, only_matching, favorites_only, sort_by,
        max_kcal, min_protein, profile, tuple(available_tools),
    )
    if st.session_state.get("recipe_signature") != signature:
        st.session_state["recipe_signature"] = signature
        st.session_state["recipe_limit"] = PAGE_SIZE
    limit = st.session_state.get("recipe_limit", PAGE_SIZE)

    # --- Özet satırı ---
    active = []
    if max_time:
        active.append(f"≤ {max_time} dk")
    if max_kcal:
        active.append(f"≤ {max_kcal} kcal")
    if min_protein:
        active.append(f"≥ {min_protein} g protein")
    if PROFILES[profile] != TOOLS:
        active.append("ekipman: " + (", ".join(available_tools) or "yok"))
    summary = f"**{len(results)} tarif**"
    if active:
        summary += " · " + " · ".join(active)
    st.markdown(summary)

    if not results:
        if hidden_by_pantry and pantry:
            st.info(
                "Evimdeki malzemelerle yapılabilen tarif bulunamadı. "
                "Daha fazla malzeme ekleyebilir ya da 'Evimdekilerle yapılabilenler' anahtarını kapatabilirsin."
            )
        else:
            st.info("Bu filtrelere uyan tarif bulunamadı. Filtreleri gevşetmeyi dene.")
    elif hidden_by_filters:
        st.caption(f"Filtrelere uymayan {hidden_by_filters} tarif gizlendi.")

    # --- Tarif kartları ---
    for r in results[:limit]:
        recipe = r["recipe"]
        nut = recipe_nutrition(recipe)
        tools = tools_for(recipe, equipment_overrides())
        pct = int(r["ratio"] * 100)
        star = "⭐ " if recipe["is_favorite"] else ""
        is_open = st.session_state.get("open_recipe") == recipe["id"]
        missing_names = [m["name"] for m in r["missing"]]

        with st.container(border=True):
            head, badge = st.columns([4, 1])
            head.markdown(f"**{star}{recipe['name']}**")
            badge.markdown(f":green[**%{pct}**]" if pct == 100 else f"**%{pct}**")
            st.caption(
                f"⏱ {recipe['time_min']} dk · 👥 {recipe['servings']} kişilik · "
                f"🔥 {nut['per_serving']} kcal / kişi"
            )
            if pantry:
                if missing_names:
                    st.markdown("🛒 Eksik: " + ", ".join(missing_names))
                else:
                    st.markdown(":green[✅ Gereken her şey evde]")

            with st.expander("Tarifi göster", expanded=is_open):
                st.markdown("**Malzemeler**")
                for ing in recipe["ingredients"]:
                    if ing["name"] in r["staples"]:
                        mark = "🧂"
                    elif ing["name"] in r["have"]:
                        mark = "✅"
                    else:
                        mark = "🛒"
                    st.write(f"{mark} {ing['label']}")
                st.caption("✅ evde var · 🛒 eksik · 🧂 her zaman evde olanlar")

                if r["insufficient"]:
                    st.warning(
                        "Miktarı yetersiz olabilir: "
                        + ", ".join(
                            f"{i['name']} ({format_amount(i['quantity'], i['unit'])} gerekiyor)"
                            for i in r["insufficient"]
                        )
                    )

                st.markdown("**Yapılışı**")
                for n, step in enumerate(recipe["steps"], start=1):
                    st.write(f"{n}. {step}")

                st.markdown("**Kişi başı yaklaşık değerler**")
                st.caption(
                    f"🔥 {nut['per_serving']} kcal · 💪 {nut['protein']} g protein · "
                    f"🍞 {nut['carbs']} g karbonhidrat · 🧈 {nut['fat']} g yağ"
                )
                st.caption(
                    "🔧 Gerekenler: " + (", ".join(tools) if tools else "pişirme gerekmez")
                )
                if nut["unknown"]:
                    st.caption(
                        "Besin hesabına katılmayan malzemeler: " + ", ".join(nut["unknown"])
                    )

                b1, b2 = st.columns(2)
                fav_label = (
                    "★ Favorilerden çıkar" if recipe["is_favorite"] else "☆ Favorilere ekle"
                )
                if b1.button(fav_label, key=f"fav_{recipe['id']}", use_container_width=True):
                    with get_session() as session:
                        repo.toggle_favorite(session, recipe["id"])
                    st.session_state["open_recipe"] = recipe["id"]
                    st.rerun()

                if r["missing"] and b2.button(
                    "🛒 Eksikleri listeye ekle",
                    key=f"add_{recipe['id']}",
                    use_container_width=True,
                ):
                    with get_session() as session:
                        added = repo.add_shopping_many(session, r["missing"])
                    st.session_state["open_recipe"] = recipe["id"]
                    st.toast(f"{len(added)} malzeme alışveriş listesine eklendi!")
                    st.rerun()

    if len(results) > limit:
        remaining = len(results) - limit
        if st.button(f"Daha fazla göster ({remaining} tarif daha)", use_container_width=True):
            st.session_state["recipe_limit"] = limit + PAGE_SIZE
            st.rerun()

# ======================================================================
# Sekme 3: Alışveriş
# ======================================================================
with tab_shopping:
    if not shopping:
        st.info(
            "Alışveriş listen boş. Bir tarifte **'Eksikleri listeye ekle'** düğmesine basınca "
            "eksik malzemeler buraya gelir."
        )
    else:
        st.subheader("Alışveriş listem")
        st.caption("Aldığın malzemeye 'Aldım' de; dolabına otomatik eklenir.")
        for item in shopping:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1.4])
                col1.write(item["label"])
                if col2.button("✔ Aldım", key=f"buy_{item['name']}", use_container_width=True):
                    with get_session() as session:
                        repo.add_pantry(session, item["name"], item["quantity"], item["unit"])
                    st.rerun()

# --- Sekme 4: Tariflerim (ekle / düzenle / sil) ---
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