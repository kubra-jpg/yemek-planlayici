from pathlib import Path
import streamlit

index = Path(streamlit.__file__).parent / "static" / "index.html"
text = index.read_text(encoding="utf-8")
text = text.replace('<html lang="en">', '<html lang="tr" translate="no">')
index.write_text(text, encoding="utf-8")
print("Tamam:", index)