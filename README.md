# Perks TR

Türkiye'deki **kredi kartları**, **operatör ayrıcalıkları**, **cashback / dijital cüzdanlar** ve
**sadakat & avantaj uygulamalarının** (Chippin, Oliz, Hopi, Migros Money, Shell ClubSmart vb.)
kullanıcıya sağladığı avantajları tek yerde toplayan statik site.

- 85 ürün ve program, 4 kategori
- Arama, kategori, avantaj türü, ücret ve durum filtreleri
- En fazla 4 ürünü yan yana karşılaştırma
- Avantaj türüne göre görünüm (mil, nakit iade, akaryakıt, market, kahve, hediye internet…)
- Bitiş tarihine göre sıralı güncel kampanyalar
- Her ürün için ayrı detay sayfası; her bilgide kaynak bağlantısı, son kontrol tarihi ve güvenilirlik düzeyi

Son veri kontrolü: **1 Ekim 2026**.

## Sayfalar

| Sayfa | İçerik |
| --- | --- |
| `index.html` | Tüm ürünler, filtreler ve karşılaştırma seçimi |
| `avantajlar.html` | Avantaj türüne göre gruplanmış ürünler |
| `kampanyalar.html` | Bitiş tarihine göre güncel kampanyalar |
| `karsilastir.html?ids=a,b` | Seçilen ürünlerin karşılaştırma tablosu |
| `hakkinda.html` | Yöntem, güvenilirlik düzeyleri, kaynak listesi |
| `urun/<id>.html` | Ürün detay sayfası (otomatik üretilir) |

## Veriyi güncelleme

Tüm içerik `data/products.json` içindedir. Sayfalar bu dosyadan üretilir:

```bash
python3 scripts/build.py          # doğrular, assets/data.js + tüm HTML sayfalarını ve sitemap.xml'i üretir
python3 -m http.server 8000       # http://localhost:8000 adresinden önizleme
```

Bir ürün kaydının alanları:

```jsonc
{
  "id": "garanti-bonus",                  // benzersiz, sayfa adı olur: urun/garanti-bonus.html
  "name": "Bonus Kart",
  "provider": "Garanti BBVA",
  "category": "kredi-karti",              // kredi-karti | operator | cashback | sadakat
  "subcategory": "Puan kartı",
  "program": "Bonus",
  "perks": ["puan", "taksit"],            // meta.perks içindeki anahtarlar
  "summary": "…",
  "benefits": ["…"],
  "costs": { "fee": "841,50 TL / yıl", "conditions": ["…"], "expiry": "…" },
  "campaigns": [{ "title": "…", "until": "2026-10-15", "source": { "label": "…", "url": "https://…" } }],
  "appStore": "https://apps.apple.com/tr/app/id…",
  "sources": [{ "label": "…", "url": "https://…" }],
  "status": "aktif",                      // aktif | kapandi | belirsiz
  "confidence": "ikincil",                // dogrulandi | ikincil | dogrulanmali
  "lastChecked": "2026-10-01"
}
```

`until` tarihi geçen kampanyalar sitede otomatik olarak "sona erdi" görünür; kaydı silmenize gerek yoktur.
Kapanan ürünleri silmek yerine `status: "kapandi"` yapın.

## Yayınlama (GitHub Pages)

`.github/workflows/pages.yml` her push'ta veriyi doğrular ve sayfaları üretir; varsayılan dala yapılan
push'larda siteyi GitHub Pages'e yayınlar. İlk kurulumda bir kez:
**Settings → Pages → Build and deployment → Source: GitHub Actions** seçilmelidir.

## Ziyaret istatistikleri (StatCounter)

1. [statcounter.com](https://statcounter.com)'da ücretsiz hesap açıp `https://sunugur.github.io/perks/` için proje ekleyin.
2. Kurulum kodundaki `sc_project` ve `sc_security` değerlerini `config.json` dosyasına yazın:

```json
{ "statcounter": { "project": "1234567", "security": "abcd1234" } }
```

3. `main`'e gönderin; sayaç kodu tüm sayfalara eklenir ve "Yöntem & kaynaklar" sayfasına gizlilik notu çıkar.
Alanlar boşken hiçbir analytics kodu eklenmez.

## Sorumluluk reddi

Bu proje hiçbir banka, operatör veya markayla bağlantılı değildir. Bilgiler bilgilendirme amaçlıdır;
ücret, oran ve kampanyalar sık değişir. Karar vermeden önce resmi kaynağı kontrol edin.
