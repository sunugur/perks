#!/usr/bin/env python3
"""Build the Perks TR static site from data/products.json.

Generates: assets/data.js, the top-level pages, one page per product under
urun/, and sitemap.xml. Run from anywhere: `python3 scripts/build.py`.
Exits non-zero if the data fails validation.
"""
import html
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "products.json")
SITE_URL = os.environ.get("SITE_URL", "https://sunugur.github.io/perks/")

REQUIRED = ["id", "name", "provider", "category", "subcategory", "program", "perks", "summary",
            "benefits", "costs", "sources", "status", "confidence", "lastChecked"]
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

NAV = [("index.html", "Tümü"), ("avantajlar.html", "Avantaj türüne göre"), ("kampanyalar.html", "Güncel kampanyalar"),
       ("karsilastir.html", "Karşılaştır"), ("hakkinda.html", "Yöntem & kaynaklar")]


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def fmt_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def validate(doc):
    meta, products = doc["meta"], doc["products"]
    errors, seen = [], set()
    for i, p in enumerate(products):
        where = p.get("id", f"#{i}")
        for k in REQUIRED:
            if k not in p:
                errors.append(f"{where}: '{k}' alanı eksik")
        if p.get("id") in seen:
            errors.append(f"{where}: id tekrar ediyor")
        seen.add(p.get("id"))
        if p.get("category") not in meta["categories"]:
            errors.append(f"{where}: bilinmeyen kategori {p.get('category')}")
        for k in p.get("perks", []):
            if k not in meta["perks"]:
                errors.append(f"{where}: bilinmeyen avantaj türü {k}")
        if p.get("status") not in meta["status"]:
            errors.append(f"{where}: bilinmeyen durum {p.get('status')}")
        if p.get("confidence") not in meta["confidence"]:
            errors.append(f"{where}: bilinmeyen güvenilirlik {p.get('confidence')}")
        if "fee" not in p.get("costs", {}):
            errors.append(f"{where}: costs.fee eksik")
        for s in p.get("sources", []):
            if not str(s.get("url", "")).startswith("https://"):
                errors.append(f"{where}: kaynak URL https ile başlamalı: {s}")
        for c in p.get("campaigns", []):
            if "title" not in c or "source" not in c:
                errors.append(f"{where}: kampanyada title/source eksik")
    return errors


def page(title, body, page_id, base="", description="", active=""):
    active_attr = ' class="active"'
    nav = "".join(
        f'<a href="{base}{href}"{active_attr if href == active else ""}>{e(label)}</a>' for href, label in NAV)
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body data-page="{page_id}" data-base="{base}">
<header class="site-header"><div class="wrap">
<a class="brand" href="{base}index.html">Perks<span>TR</span></a>
<nav class="nav">{nav}</nav>
<button class="theme-btn" id="theme-btn" type="button" aria-label="Tema değiştir">◐</button>
</div></header>
<main class="wrap">
{body}
</main>
<div class="tray" id="tray"><div class="wrap"><b>Karşılaştır:</b><div class="sel"></div>
<button class="btn ghost" id="tray-clear" type="button">Temizle</button>
<button class="btn" id="tray-go" type="button">Karşılaştır →</button></div></div>
<footer class="site-footer"><div class="wrap">
<p>Perks TR – Türkiye'deki kredi kartı, operatör, cashback ve sadakat avantajlarının bağımsız derlemesi. Hiçbir kurumla bağlantılı değildir.</p>
<p>Bilgiler bilgilendirme amaçlıdır; oran, ücret ve kampanyalar sık değişir. Karar vermeden önce resmi kaynağı kontrol edin.</p>
</div></footer>
<script src="{base}assets/data.js"></script>
<script src="{base}assets/app.js"></script>
</body>
</html>
"""


def build_index(meta):
    body = f"""
<section class="hero">
<h1>Türkiye'deki kart, operatör, cashback ve sadakat avantajları tek yerde</h1>
<p>Kredi kartlarından operatör ayrıcalıklarına, nakit iade cüzdanlarından Chippin, Oliz ve Hopi gibi sadakat uygulamalarına kadar
hangi ürünün size ne kazandırdığını, ne kadara mal olduğunu ve şu an hangi kampanyaların sürdüğünü karşılaştırın.</p>
<div class="stats" id="stats"></div>
<div class="notice"><b>Son kontrol: {fmt_date(meta['lastUpdated'])}.</b> Her bilginin yanında kaynağı ve güvenilirlik düzeyi var.
"⚠ doğrulayın" işaretli kayıtlarda kısmi bilgi bulunur.</div>
</section>
<div class="cat-grid" id="cat-tiles"></div>
<section id="liste">
<div class="filters">
  <div class="row">
    <input type="search" id="f-q" placeholder="Ara: ör. akaryakıt, Netflix, mil, Migros…" aria-label="Ara">
    <select id="f-cat" aria-label="Kategori"></select>
    <select id="f-fee" aria-label="Ücret">
      <option value="">Tüm ücretler</option><option value="free">Aidatsız / ücretsiz</option><option value="paid">Ücretli</option>
    </select>
    <select id="f-status" aria-label="Durum">
      <option value="aktif">Sadece aktif</option><option value="tum">Kapananlar dahil</option>
    </select>
    <select id="f-sort" aria-label="Sıralama">
      <option value="kategori">Kategoriye göre</option><option value="kampanya">En çok kampanya</option><option value="ad">A–Z</option>
    </select>
  </div>
  <div class="chips" id="f-perks" aria-label="Avantaj türü"></div>
  <div class="row"><span class="result-count" id="count"></span><button class="chip" id="f-reset" type="button">Filtreleri sıfırla</button></div>
</div>
<div class="grid" id="grid"></div>
</section>"""
    return page("Perks TR – Kart, operatör, cashback ve sadakat avantajları", body, "list",
                description="Türkiye'deki kredi kartı, operatör aboneliği, cashback ve sadakat uygulamalarının avantajlarını karşılaştırın.",
                active="index.html")


def build_perks():
    body = """
<section class="hero"><h1>Avantaj türüne göre</h1>
<p>Akaryakıtta, markette, seyahatte ya da dijital aboneliklerde en çok kazandıran ürünleri kategoriler arası görün.</p></section>
<div class="chips" id="perk-nav" style="margin:10px 0 0"></div>
<div id="perk-sections"></div>"""
    return page("Avantaj türüne göre – Perks TR", body, "perks",
                description="Mil, nakit iade, akaryakıt, market, kahve ve daha fazlası: avantaj türüne göre ürünler.", active="avantajlar.html")


def build_compare():
    body = """
<section class="hero"><h1>Karşılaştır</h1>
<p>En fazla 4 ürünü yan yana karşılaştırın. Listeden "Karşılaştır" kutusunu işaretleyin veya buradan ekleyin.</p></section>
<div class="filters"><div class="row"><select id="cmp-add" aria-label="Ürün ekle"></select></div></div>
<div id="compare"></div>"""
    return page("Karşılaştır – Perks TR", body, "compare", description="Kredi kartı, cüzdan ve sadakat programlarını yan yana karşılaştırın.",
                active="karsilastir.html")


def build_campaigns(meta):
    body = f"""
<section class="hero"><h1>Güncel kampanyalar</h1>
<p>Bitiş tarihine göre sıralı. Kampanya listesi {fmt_date(meta['lastUpdated'])} itibarıyla derlendi; bitiş tarihleri kaynakta
"X gün kaldı" şeklinde verildiğinde yaklaşık olarak hesaplandı. Katılmadan önce bankanın/markanın koşullarını okuyun.</p></section>
<div class="filters"><div class="row"><label class="cmp-toggle"><input type="checkbox" id="show-expired"> Sona erenleri de göster</label>
<span class="result-count" id="camp-count"></span></div></div>
<div id="campaigns"></div>"""
    return page("Güncel kampanyalar – Perks TR", body, "campaigns", description="Kredi kartı, cüzdan ve sadakat programlarında süren kampanyalar.",
                active="kampanyalar.html")


def build_about(meta, products):
    sources = {}
    for p in products:
        for s in p["sources"]:
            if "apps.apple.com" not in s["url"]:
                sources[s["url"]] = s["label"]
    src_list = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(l)}</a></li>' for u, l in sorted(sources.items(), key=lambda x: x[1]))
    conf = "".join(f"<li><b>{e(v)}</b> (<code>{e(k)}</code>)</li>" for k, v in meta["confidence"].items())
    body = f"""
<section class="hero"><h1>Yöntem ve kaynaklar</h1>
<p>Bu site, Türkiye'de kullanıcılara avantaj sağlayan finansal ve sadakat ürünlerinin bağımsız bir derlemesidir.</p></section>
<div class="panel"><h2>Nasıl derlendi?</h2><ul>
<li>Kredi kartı aidatları ve mil kartları için 2026 tarihli karşılaştırma kaynakları ve bankaların resmi sayfaları kullanıldı.</li>
<li>Cashback ve sadakat uygulamaları, App Store Türkiye'de kategori aramalarıyla (nakit iade, cashback, sadakat, puan kazan, akaryakıt puan, market indirim, fiş okut vb.) tarandı; açıklamalar uygulamaların resmi mağaza metinlerinden alındı.</li>
<li>Güncel kampanyalar {fmt_date(meta['lastUpdated'])} itibarıyla kampanya derleme sitelerinden ve bankaların sayfalarından alındı.</li>
<li>Kapanan veya durumu belirsiz ürünler (ör. Nays) listeden silinmedi; "kapananlar dahil" filtresiyle görülebilir.</li>
</ul></div>
<div class="panel"><h2>Güvenilirlik düzeyleri</h2><ul>{conf}</ul></div>
<div class="panel"><h2>Veriyi güncelleme</h2>
<p>Tüm içerik <code>data/products.json</code> dosyasındadır. Dosyayı düzenleyip <code>main</code> dalına gönderdiğinizde GitHub Actions siteyi yeniden üretir ve yayınlar.
Ayrıntılar için depodaki README dosyasına bakın.</p></div>
<div class="panel"><h2>Kaynak listesi (uygulama mağazası bağlantıları hariç)</h2><ul>{src_list}</ul></div>
<div class="panel"><h2>Sorumluluk reddi</h2><p>Bilgiler yatırım veya finansal tavsiye değildir. Ücretler, oranlar ve kampanyalar kurumlar tarafından sık sık değiştirilir;
kaynaklar arasında farklılık olduğunda bu durum ilgili kayıtta belirtilmiştir.</p></div>"""
    return page("Yöntem ve kaynaklar – Perks TR", body, "about", description="Perks TR verilerinin nasıl derlendiği ve kaynakları.",
                active="hakkinda.html")


def ul(items):
    return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>" if items else "<p>—</p>"


def build_product(p, meta):
    cat = meta["categories"][p["category"]]
    costs = p["costs"]
    tags = " ".join(f'<span class="tag">{e(meta["perks"][k])}</span>' for k in p["perks"])
    status = "" if p["status"] == "aktif" else f' <span class="badge {p["status"]}">{e(meta["status"][p["status"]])}</span>'
    camps = ""
    for c in p.get("campaigns", []):
        until = f'data-until="{e(c["until"])}"' if c.get("until") else ""
        when = f'{fmt_date(c["until"])} tarihine kadar' if c.get("until") else "Bitiş tarihi belirtilmemiş"
        note = f' · {e(c["note"])}' if c.get("note") else ""
        camps += (f'<div class="camp" {until}>{e(c["title"])}<small>{when}{note} · '
                  f'<a href="{e(c["source"]["url"])}" target="_blank" rel="noopener">{e(c["source"]["label"])}</a></small></div>')
    camps_panel = f'<div class="panel"><h2>Kampanyalar</h2>{camps}</div>' if camps else ""
    srcs = "".join(f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["label"])}</a></li>' for s in p["sources"])
    app_link = f'<dt>Uygulama</dt><dd><a href="{e(p["appStore"])}" target="_blank" rel="noopener">App Store</a></dd>' if p.get("appStore") else ""
    related = [q for q in PRODUCTS if q["id"] != p["id"] and q["category"] == p["category"] and q["status"] == "aktif"
               and set(q["perks"]) & set(p["perks"])][:5]
    rel = "".join(f'<li><a href="{e(q["id"])}.html">{e(q["name"])}</a> <small>– {e(q["provider"])}</small></li>' for q in related)
    rel_panel = f'<div class="panel"><h2>Benzer ürünler</h2><ul>{rel}</ul></div>' if rel else ""
    body = f"""
<div class="breadcrumb"><a href="../index.html">Tümü</a> › <a href="../index.html?kategori={e(p['category'])}#liste">{e(cat['label'])}</a> › {e(p['name'])}</div>
<div class="detail">
<div>
<h1>{e(p['name'])}{status}</h1>
<p class="lead">{e(p['summary'])}</p>
<div class="tags" style="margin-bottom:14px">{tags}</div>
<div class="panel"><h2>Kullanıcıya sağladığı avantajlar</h2>{ul(p['benefits'])}</div>
{camps_panel}
<div class="panel"><h2>Maliyet ve koşullar</h2>
<dl class="kv"><dt>Ücret</dt><dd><b>{e(costs['fee'])}</b></dd>
{f"<dt>Puan geçerliliği</dt><dd>{e(costs['expiry'])}</dd>" if costs.get('expiry') else ""}
</dl>{ul(costs.get('conditions', [])) if costs.get('conditions') else ""}</div>
</div>
<aside>
<div class="panel"><h2>Özet bilgi</h2><dl class="kv">
<dt>Sağlayıcı</dt><dd>{e(p['provider'])}</dd>
<dt>Kategori</dt><dd>{e(cat['icon'])} {e(cat['label'])}</dd>
<dt>Tür</dt><dd>{e(p['subcategory'])}</dd>
<dt>Program</dt><dd>{e(p['program'])}</dd>
<dt>Durum</dt><dd>{e(meta['status'][p['status']])}</dd>
{app_link}
<dt>Son kontrol</dt><dd>{fmt_date(p['lastChecked'])}</dd>
<dt>Güvenilirlik</dt><dd>{e(meta['confidence'][p['confidence']])}</dd>
</dl>
<p style="margin:14px 0 0"><button class="btn" id="cmp-btn" data-id="{e(p['id'])}" type="button">Karşılaştırmaya ekle</button></p>
</div>
<div class="panel"><h2>Kaynaklar</h2><ul>{srcs}</ul></div>
{rel_panel}
</aside>
</div>"""
    return page(f"{p['name']} ({p['provider']}) avantajları – Perks TR", body, "detail", base="../",
                description=p["summary"])


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


PRODUCTS = []


def main():
    with open(DATA, encoding="utf-8") as f:
        doc = json.load(f)
    errors = validate(doc)
    if errors:
        print("Veri doğrulama hataları:", *errors, sep="\n  ")
        sys.exit(1)
    meta = doc["meta"]
    PRODUCTS.extend(doc["products"])

    write("assets/data.js", "/* Generated by scripts/build.py from data/products.json – do not edit. */\nwindow.PERKS = "
          + json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + ";\n")
    write("index.html", build_index(meta))
    write("avantajlar.html", build_perks())
    write("karsilastir.html", build_compare())
    write("kampanyalar.html", build_campaigns(meta))
    write("hakkinda.html", build_about(meta, PRODUCTS))

    shutil.rmtree(os.path.join(ROOT, "urun"), ignore_errors=True)
    for p in PRODUCTS:
        write(f"urun/{p['id']}.html", build_product(p, meta))

    urls = ["index.html", "avantajlar.html", "kampanyalar.html", "karsilastir.html", "hakkinda.html"] + [f"urun/{p['id']}.html" for p in PRODUCTS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{meta['lastUpdated']}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    print(f"{len(PRODUCTS)} ürün, {len(urls)} sayfa üretildi.")


if __name__ == "__main__":
    main()
