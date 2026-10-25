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
    ("tours", "/brewery-tour-singapore/", "Tours"),
    ("trade", "/contract-brewing-singapore/", "Brew with us"),
    ("visit", "/visit/", "Visit"),
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


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")
    shutil.copy(SRC / "_redirects", OUT / "_redirects")
    base = (SRC / "base.html").read_text()
    faqs = json.loads((SRC / "data" / "faqs.json").read_text())
    urls = []

    for page in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse(page.read_text())
        path = meta["path"]
        canonical = SITE_URL + path

        faq_items = faqs.get(meta.get("faq", ""), [])
        body = body.replace("{{faq}}", render_faq(faq_items) if faq_items else "")
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
                {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE_URL + u}
                for i, (n, u) in enumerate(crumbs)]})
        if faq_items:
            graph.append({"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in faq_items]})
        jsonld = json.dumps({"@context": "https://schema.org", "@graph": graph},
                            ensure_ascii=False, indent=1)

        nav_html = "\n".join(
            f'<a href="{u}"{" aria-current=page" if meta.get("nav") == k else ""}>{label}</a>'
            for k, u, label in NAV)

        out = (base
               .replace("{{title}}", html.escape(meta["title"]))
               .replace("{{description}}", html.escape(meta["description"]))
               .replace("{{canonical}}", canonical)
               .replace("{{og_image}}", wix(meta.get("image", DEFAULT_IMAGE), 1200, 630))
               .replace("{{nav}}", nav_html)
               .replace("{{jsonld}}", jsonld)
               .replace("{{content}}", body))
        out = expand(out)
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
