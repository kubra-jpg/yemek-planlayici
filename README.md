# Yemek Planlayıcı

Evdeki malzemelere göre yapılabilecek yemekleri öneren ve eksik malzemeleri alışveriş listesine ekleyen küçük bir uygulama.

## Özellikler
- Evdeki malzemeleri ekleme ve silme
- Tarifleri malzeme eşleşme yüzdesine göre sıralama
- Tarif detaylarını ve yapılış adımlarını görme
- Eksik malzemeleri tek tıkla alışveriş listesine ekleme
- Alışveriş listesinde "Aldım" ile ürünü evdeki malzemelere taşıma

## Kullanılan teknolojiler
- Python 3.11+
- Streamlit (arayüz)
- pytest (testler)

## Kurulum
```
git clone https://github.com/kubra-jpg/yemek-planlayici.git
cd yemek-planlayici
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Uygulama tarayıcıda `http://localhost:8501` adresinde açılır.

## Testler
```
pytest
```

## Proje yapısı
```
app.py              Streamlit arayüzü
core/matcher.py     Tarif eşleştirme mantığı
data/recipes.json   Tarif verisi
tests/              Birim testleri
```

## Bilinen notlar
- Tarayıcının otomatik çevirisi yazıları bozabilir. Sorun yaşarsan `python fix_lang.py` komutunu bir kez çalıştır ve uygulamayı yeniden başlat.
- Veriler şimdilik sadece oturum boyunca saklanır; sayfa yenilenince sıfırlanır. Kalıcı saklama (SQLite) sonraki aşamada eklenecek.

## Yol haritası
- [x] Aşama 1: Malzeme girişi, tarif eşleştirme, alışveriş listesi
- [ ] Aşama 2: Kalıcı veri, miktar/birim, tarif ekleme ve düzenleme
- [ ] Aşama 3: Haftalık plan, son kullanma tarihi takibi
- [ ] Aşama 4: Diyet ve alerji filtreleri
- [ ] Aşama 5: Alışveriş listesi geliştirmeleri