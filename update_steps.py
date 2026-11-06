"""data/recipes.json içindeki adım ve süreleri, VAR OLAN veritabanındaki tariflere
isme göre uygular. Dolap, favoriler ve kendi eklediğin tariflere dokunmaz.
Kullanım:  python update_steps.py
"""
import json, sqlite3, sys

DB = "data/yemek.db"
con = sqlite3.connect(DB)
cur = con.cursor()
tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
print("Tablolar:", tables)
tbl = next((t for t in tables if t.lower() in ("recipes", "recipe")), None)
if not tbl:
    sys.exit("Tarif tablosu bulunamadı; yukarıdaki tablo listesini bana gönder.")
cols = [r[1] for r in cur.execute(f"pragma table_info({tbl})")]
print("Sütunlar:", cols)
name_c = "name" if "name" in cols else None
steps_c = "steps" if "steps" in cols else None
time_c = next((c for c in ("time_min", "minutes", "duration") if c in cols), None)
if not (name_c and steps_c):
    sys.exit("name/steps sütunu bulunamadı; sütun listesini bana gönder.")

data = json.load(open("data/recipes.json", encoding="utf-8"))
n = 0
for r in data:
    text = "\n".join(r["steps"])
    if time_c:
        cur.execute(f"update {tbl} set {steps_c}=?, {time_c}=? where {name_c}=?",
                    (text, r["time_min"], r["name"]))
    else:
        cur.execute(f"update {tbl} set {steps_c}=? where {name_c}=?", (text, r["name"]))
    n += cur.rowcount
con.commit()
print(f"{n} tarifin adımları güncellendi.")