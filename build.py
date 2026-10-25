#!/usr/bin/env python3
"""Build the RedDot BrewHouse site: src/ -> _site/ (Python 3 stdlib only).

Pages live in src/pages/*.html with a front-matter block:

    ---
    title: Page title for <title>
    description: Meta description
    path: /url-path/
    crumb: Breadcrumb name
    parent: /events/|Events        (optional)
    nav: events                    (optional, highlights a nav item)
    faq: weddings                  (optional, key in src/data/faqs.json)
    image: <wix media id>          (optional, og:image)
    ---

Inside pages and partials:
    {{> partial-name}}             include src/partials/partial-name.html
    {{img:MEDIA_ID:W:H}}           Wix image URL cropped to W x H
    {{faq}}                        rendered FAQ section for the page
"""
import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "_site"
SITE_URL = "https://www.reddotbrewhouse.com.sg"
# Demo hosting (GitHub Pages): BASE_PATH=/reddot-website NOINDEX=1 python3 build.py
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
NOINDEX = os.environ.get("NOINDEX") == "1"
DEFAULT_IMAGE = "be081f_91140c26e0654f219f41a013e1569e47~mv2.jpg"

NAV = [
    ("beer", "/craft-beer/", "Beer"),
    ("food", "/menu/", "Food"),
    ("garden", "/dog-friendly-restaurant-dempsey/", "Dogs &amp; kids"),
    ("events", "/events/", "Events"),
    ("visit", "/visit/", "Visit"),
    ("shop", "/shop/", "Shop"),
]

BUSINESS = {
    "@type": ["Restaurant", "Brewery"],
    "@id": SITE_URL + "/#business",
    "name": "RedDot BrewHouse",
    "url": SITE_URL + "/",
    "logo": "https://static.wixstatic.com/media/be081f_f91c777214e240a5a14543c820666b05~mv2.png",
    "image": "https://static.wixstatic.com/media/" + DEFAULT_IMAGE,
    "foundingDate": "2007",
    "telephone": "+65 6475 0500",
    "email": "rd@reddotbrewhouse.com.sg",
    "priceRange": "$$",
    "servesCuisine": ["Western", "Craft beer"],
    "acceptsReservations": "https://cho.pe/dineatreddotbrewhousedempseyhillsg",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "25A Dempsey Road, #01-01",
        "addressLocality": "Singapore",
        "postalCode": "247691",
        "addressCountry": "SG",
    },
    "sameAs": [
        "https://www.instagram.com/reddotbrewhouse/",
        "https://www.tiktok.com/@reddotbrewhouse",
        "https://www.facebook.com/p/RedDot-BrewHouse-100089621965331/",
    ],
}


def wix(media_id, w, h):
    return (f"https://static.wixstatic.com/media/{media_id}"
            f"/v1/fill/w_{w},h_{h},al_c,q_80,enc_auto/img.jpg")


def add_srcset(page_html):
    """Give every Wix photo a srcset so phones download a phone-sized file.
    Full-width heroes also get a portrait crop for phones via <picture>."""
    def repl(m):
        tag, mid, w, h = m.group(0), m.group(2), int(m.group(3)), int(m.group(4))
        if "srcset=" in tag:
            return tag
        widths = sorted({x for x in (480, 800, 1200, 1600, 2000) if x < w} | {w})
        srcset = ", ".join(f"{wix(mid, x, round(h * x / w))} {x}w" for x in widths)
        sizes = "100vw" if w >= 1600 else "(max-width: 960px) 100vw, 50vw" if w >= 1000 else "(max-width: 600px) 80vw, 33vw"
        img = tag[:-1].rstrip("/").rstrip() + f' srcset="{srcset}" sizes="{sizes}" decoding="async">'
        if w < 1600:
            return img
        portrait = ", ".join(f"{wix(mid, x, round(x * 1.6))} {x}w" for x in (600, 900, 1200))
        return (f'<picture><source media="(max-width: 600px)" srcset="{portrait}" sizes="100vw">'
                f"{img}</picture>")
    return re.sub(r'<img [^>]*?src="(https://static\.wixstatic\.com/media/([^/]+)/v1/fill/w_(\d+),h_(\d+),al_c,q_80,enc_auto/img\.jpg)"[^>]*>',
                  repl, page_html)


def parse(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def expand(text, depth=0):
    if depth > 5:
        return text
    text = re.sub(r"\{\{>\s*([\w-]+)\s*\}\}",
                  lambda m: expand((SRC / "partials" / f"{m.group(1)}.html").read_text(), depth + 1),
                  text)
    return re.sub(r"\{\{img:([^:}]+):(\d+):(\d+)\}\}",
                  lambda m: wix(m.group(1), m.group(2), m.group(3)), text)


def render_faq(items):
    rows = "\n".join(
        f'<details class="faq-item"><summary>{html.escape(q)}</summary><p>{a}</p></details>'
        for q, a in items)
    return (f'<section class="faq"><div class="wrap faq-grid">'
            f'<h2 class="display">Questions we get asked</h2>'
            f'<div class="faq-list">{rows}</div></div></section>')


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


# ---------- Shop ----------
CATALOG = json.loads((SRC / "data" / "products.json").read_text())
PRODUCTS = CATALOG["products"]
IMG_BASE = CATALOG["img_base"]
CATS = [("all", "Everything"), ("beer", "Beer"), ("spirits", "Spirits"), ("kegs-gifts", "Kegs &amp; gifts")]
FORMAT_LABELS = {"bottle": "Bottle", "4-pack": "4-pack", "carton": "Carton"}
FORMAT_DETAIL = {"bottle": "1 × 330ml bottle", "4-pack": "4 × 330ml bottles", "carton": "24 × 330ml bottles"}


def money(n):
    return f"S${n:,.0f}" if n == int(n) else f"S${n:,.2f}"


def fmt_label(key):
    return FORMAT_LABELS.get(key, key)


def product_img(p, key=None):
    key = key or next(iter(p["formats"]))
    return IMG_BASE + p["formats"][key]["img"]


def meta_line(p):
    return p["style"] + (f", {p['abv']} ABV" if p["abv"] else "")


def from_price(p):
    prices = [f["price"] for f in p["formats"].values()]
    return ("From " if len(prices) > 1 else "") + money(min(prices))


def format_picker(p, name):
    """Segmented control for beer formats; a single hidden value for everything else."""
    keys = list(p["formats"])
    if len(keys) == 1:
        return f'<input type="hidden" name="{name}" value="{keys[0]}">'
    opts = "".join(
        f'<label><input type="radio" name="{name}" value="{k}"{" checked" if i == 0 else ""}>'
        f'<span>{fmt_label(k)}<b>{money(f["price"])}</b></span></label>'
        for i, (k, f) in enumerate(p["formats"].items()))
    return f'<fieldset class="formats"><legend class="sr-only">Pack size</legend>{opts}</fieldset>'


def price_html(p):
    f = next(iter(p["formats"].values()))
    if len(p["formats"]) == 1 and f.get("was"):
        return f'<span class="price">{money(f["price"])}</span> <s class="was">{money(f["was"])}</s>'
    return f'<span class="price">{from_price(p)}</span>'


def product_card(p, variant="grid"):
    url = f"/shop/{p['slug']}/"
    sold = p.get("soldout")
    badge = ""
    if p.get("award"):
        badge = '<span class="badge badge-gold">Award winner</span>'
    elif any(f.get("was") for f in p["formats"].values()):
        badge = '<span class="badge badge-red">On sale</span>'
    if sold:
        badge = '<span class="badge badge-muted">Sold out</span>'
    action = ('<button class="btn btn-sold" type="button" disabled>Sold out</button>' if sold else
              '<button class="btn btn-red btn-add" type="submit">Add to cart</button>')
    picker = "" if sold else format_picker(p, f"f-{variant}-{p['slug']}")
    return f"""<article class="product is-{variant}" data-cat="{p['cat']}" data-price="{min(f['price'] for f in p['formats'].values())}" style="--tint:{p['tint']}">
  <a class="product-media" href="{url}" tabindex="-1" aria-hidden="true">{badge}<img loading="lazy" src="{product_img(p)}" alt=""></a>
  <div class="product-body">
    <p class="product-meta">{meta_line(p)}</p>
    <h3 class="product-name"><a href="{url}">{p['name']}</a></h3>
    <p class="product-price">{price_html(p)}</p>
    <form class="add-form" data-product="{p['slug']}">{picker}{action}</form>
  </div>
</article>"""


def shop_grid():
    chips = "".join(
        f'<button type="button" class="chip" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{label}</button>'
        for k, label in CATS)
    cards = "\n".join(product_card(p) for p in PRODUCTS)
    return f"""<div class="shop-tools">
  <div class="chips" role="group" aria-label="Filter products">{chips}</div>
  <label class="sort">Sort by
    <select id="sort"><option value="featured">Featured</option><option value="low">Price, low to high</option><option value="high">Price, high to low</option></select>
  </label>
</div>
<p class="shop-count" aria-live="polite"><span id="shown">{len(PRODUCTS)}</span> products</p>
<div class="product-grid" id="product-grid">
{cards}
</div>"""


def shelf():
    cards = "\n".join(product_card(p, "shelf") for p in PRODUCTS if p.get("featured"))
    return f'<div class="shelf" tabindex="0" aria-label="Our beers, scrollable">{cards}</div>'


def product_page(p, template):
    keys = list(p["formats"])
    sold = p.get("soldout")
    first = p["formats"][keys[0]]
    gallery = "".join(
        f'<img src="{product_img(p, k)}" alt="{p["name"]}, {fmt_label(k).lower()}" data-format="{k}"'
        f'{"" if i == 0 else " hidden"}{" loading=lazy" if i else ""}>'
        for i, k in enumerate(keys))
    thumbs = "" if len(keys) == 1 else '<div class="thumbs">' + "".join(
        f'<button type="button" data-format="{k}" aria-label="Show {fmt_label(k).lower()}"{" aria-pressed=true" if i == 0 else ""}>'
        f'<img src="{product_img(p, k)}" alt="" loading="lazy"></button>' for i, k in enumerate(keys)) + "</div>"
    details = [("Style", p["style"])]
    if p["abv"]:
        details.append(("Alcohol", p["abv"] + " ABV"))
    if p["cat"] == "beer":
        details.append(("Pack sizes", ", ".join(f"{fmt_label(k)} ({FORMAT_DETAIL[k]})" for k in keys)))
        details.append(("Brewed at", "RedDot BrewHouse, Dempsey Hill"))
    details_html = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in details)
    if sold:
        buy = '<p class="soldout-note">Sold out for now. Ask the team at the brewhouse when it\'s back.</p>'
    else:
        buy = (f'<form class="add-form buy-form" data-product="{p["slug"]}">{format_picker(p, "format")}'
               '<div class="buy-row"><label class="qty"><span class="sr-only">Quantity</span>'
               '<button type="button" class="qty-btn" data-step="-1" aria-label="Decrease quantity">−</button>'
               '<input type="number" name="qty" value="1" min="1" max="99" inputmode="numeric">'
               '<button type="button" class="qty-btn" data-step="1" aria-label="Increase quantity">+</button></label>'
               '<button class="btn btn-red btn-add" type="submit">Add to cart</button></div></form>')
    award = f'<p class="badge badge-gold">{p["award"]}</p>' if p.get("award") else ""
    buybar = "" if sold else (
        f'<div class="buy-bar" aria-hidden="true"><div><strong>{p["name"]}</strong>'
        f'<span data-live-price>{money(first["price"])}</span></div>'
        '<button class="btn btn-red" type="button" tabindex="-1" data-buybar>Add to cart</button></div>')
    related_pool = [q for q in PRODUCTS if q["slug"] != p["slug"] and q["cat"] == p["cat"] and not q.get("soldout")]
    related = "\n".join(product_card(q) for q in related_pool[:4])
    body = (template
            .replace("{{p.name}}", p["name"]).replace("{{p.meta}}", meta_line(p))
            .replace("{{p.notes}}", p["notes"]).replace("{{p.price}}", price_html(p) if len(keys) == 1 else f'<span class="price" data-live-price>{money(first["price"])}</span>')
            .replace("{{p.gallery}}", gallery).replace("{{p.thumbs}}", thumbs)
            .replace("{{p.details}}", details_html).replace("{{p.buy}}", buy).replace("{{p.award}}", award)
            .replace("{{p.tint}}", p["tint"]).replace("{{p.related}}", related).replace("{{p.buybar}}", buybar))
    title = f"{p['name']} | Buy Online | RedDot BrewHouse"
    if len(title) > 60:
        title = f"{p['name']} | RedDot BrewHouse"
    meta = {"title": title, "description": f"{p['notes']} {from_price(p)} with free delivery in Singapore over S$75."[:158],
            "path": f"/shop/{p['slug']}/", "crumb": p["name"], "parent": "/shop/|Shop", "nav": "shop",
            "og": SITE_URL + product_img(p)}
    offers = [{"@type": "Offer", "name": fmt_label(k), "price": f["price"], "priceCurrency": "SGD",
               "availability": "https://schema.org/" + ("OutOfStock" if sold else "InStock"),
               "url": SITE_URL + meta["path"]} for k, f in p["formats"].items()]
    schema = {"@type": "Product", "name": p["name"], "description": p["notes"], "image": SITE_URL + product_img(p),
              "brand": {"@type": "Brand", "name": "Hidden Hills" if "Hidden Hills" in p["name"] else
                        "Island Spirits" if "Island Spirits" in p["name"] else "RedDot BrewHouse"},
              "offers": offers}
    return meta, body, schema


def products_js():
    data = {p["slug"]: {"name": p["name"], "url": f"/shop/{p['slug']}/", "tint": p["tint"],
                        "formats": {k: {"label": fmt_label(k), "price": f["price"], "img": BASE_PATH + IMG_BASE + f["img"]}
                                    for k, f in p["formats"].items()}}
            for p in PRODUCTS}
    return f"window.RD_BASE={json.dumps(BASE_PATH)};\nwindow.RD_PRODUCTS={json.dumps(data, ensure_ascii=False)};\n"


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")
    shutil.copy(SRC / "_redirects", OUT / "_redirects")
    (OUT / "assets" / "products.js").write_text(products_js())
    base = (SRC / "base.html").read_text()
    for asset in ("styles.css", "script.js", "products.js"):
        digest = hashlib.md5((OUT / "assets" / asset).read_bytes()).hexdigest()[:8]
        base = base.replace(f"/assets/{asset}", f"/assets/{asset}?v={digest}")
    faqs = json.loads((SRC / "data" / "faqs.json").read_text())
    template = (SRC / "product.html").read_text()
    urls = []

    jobs = []
    for page in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse(page.read_text())
        jobs.append((meta, body, None))
    for p in PRODUCTS:
        jobs.append(product_page(p, template))

    for meta, body, extra_schema in jobs:
        path = meta["path"]
        canonical = SITE_URL + path

        faq_items = faqs.get(meta.get("faq", ""), [])
        body = body.replace("{{faq}}", render_faq(faq_items) if faq_items else "")
        body = body.replace("{{shop-grid}}", shop_grid()).replace("{{shelf}}", shelf())
        body = expand(body)

        crumbs = [("Home", "/")]
        if meta.get("parent"):
            p_path, p_name = meta["parent"].split("|")
            crumbs.append((p_name, p_path))
        if path != "/":
            crumbs.append((meta.get("crumb", meta["title"]), path))
        crumb_html = ""
        if len(crumbs) > 1:
            parts = [f'<a href="{u}">{n}</a>' for n, u in crumbs[:-1]]
            parts.append(f'<span aria-current="page">{crumbs[-1][0]}</span>')
            crumb_html = ('<nav class="breadcrumb" aria-label="Breadcrumb"><div class="wrap">'
                          + '<span aria-hidden="true">/</span>'.join(parts) + "</div></nav>")
        body = body.replace("{{breadcrumb}}", crumb_html)

        graph = [BUSINESS, {
            "@type": "WebPage", "@id": canonical + "#webpage", "url": canonical,
            "name": meta["title"], "description": meta["description"],
            "isPartOf": {"@type": "WebSite", "url": SITE_URL + "/", "name": "RedDot BrewHouse"},
            "about": {"@id": SITE_URL + "/#business"},
        }]
        if len(crumbs) > 1:
            graph.append({"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": strip_tags(html.unescape(n)), "item": SITE_URL + u}
                for i, (n, u) in enumerate(crumbs)]})
        if faq_items:
            graph.append({"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in faq_items]})
        if extra_schema:
            graph.append(extra_schema)
        jsonld = json.dumps({"@context": "https://schema.org", "@graph": graph},
                            ensure_ascii=False, indent=1)

        nav_html = "\n".join(
            f'<a href="{u}"{" aria-current=page" if meta.get("nav") == k else ""}>{label}</a>'
            for k, u, label in NAV)

        out = (base
               .replace("{{title}}", html.escape(meta["title"]))
               .replace("{{description}}", html.escape(meta["description"]))
               .replace("{{canonical}}", canonical)
               .replace("{{og_image}}", meta.get("og") or wix(meta.get("image", DEFAULT_IMAGE), 1200, 630))
               .replace("{{nav}}", nav_html)
               .replace("{{jsonld}}", jsonld)
               .replace("{{content}}", body)
               .replace("{{body_class}}", "page-shop" if meta.get("nav") == "shop" else ""))
        out = add_srcset(expand(out))
        if BASE_PATH:
            out = re.sub(r'((?:href|src)=")/(?!/)', rf"\1{BASE_PATH}/", out)
        if NOINDEX:
            out = out.replace("<head>", '<head>\n  <meta name="robots" content="noindex, nofollow">', 1)

        dest = OUT / "404.html" if path == "/404/" else OUT / path.strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out)
        if path != "/404/":
            urls.append(canonical)

    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in sorted(urls))
        + "</urlset>\n")
    robots = "User-agent: *\nDisallow: /\n" if NOINDEX else f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots)
    print(f"Built {len(urls)} pages + 404 into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
