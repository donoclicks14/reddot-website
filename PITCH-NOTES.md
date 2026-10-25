# RedDot BrewHouse website pitch: notes

Multi-page static site built from `src/` by `build.py` (Python 3, no dependencies).

- Build: `python3 build.py` (outputs `_site/`, plus sitemap.xml and robots.txt)
- Preview: `python3 -m http.server 8790 -d _site`, then open http://localhost:8790
- Deploy: Netlify reads `netlify.toml` (build `python3 build.py`, publish `_site`)
- **Edit files in `src/`, never `_site/`.** Pages are `src/pages/*.html` with front matter
  (title, description, path, breadcrumb, FAQ key). Shared blocks are in `src/partials/`, FAQs in `src/data/faqs.json`.

## Pages and target searches
| URL | Targets |
|---|---|
| `/` | RedDot BrewHouse, craft brewery restaurant Dempsey |
| `/craft-beer/` | craft beer Singapore, award-winning local beer |
| `/menu/` | restaurant Dempsey Hill, RedDot menu |
| `/dog-friendly-restaurant-dempsey/` | dog-friendly restaurant, kids' activities, live band |
| `/events/` | event venue Singapore, garden venue |
| `/garden-wedding-venue-singapore/` | garden wedding venue, solemnisation venue |
| `/corporate-event-venue-singapore/` | corporate event venue, D&D venue |
| `/private-party-venue-singapore/` | birthday venue, dog birthday party |
| `/brewery-tour-singapore/` | brewery tour Singapore, beer tasting |
| `/contract-brewing-singapore/` | contract brewing, OEM beer, hard seltzer |
| `/brewery-consulting-singapore/` | brewery/distillery consulting |
| `/beer-distribution-singapore/` | craft beer distribution, wholesale |
| `/about/` | brand story, Crystalla Huang |
| `/visit/` | address, parking, directions |

Every page has its own title (60 characters or fewer), meta description, canonical URL, Open Graph tags, a single H1,
breadcrumbs, and JSON-LD (Restaurant + Brewery, WebPage, BreadcrumbList, plus FAQPage where there are FAQs).
Pages link to each other through hub rows, the footer and in-text links.

**At launch:** `src/_redirects` already 301-redirects every old Wix URL to its new page (Netlify format),
so existing Google rankings carry over. Submit `/sitemap.xml` in Google Search Console.

## Content to confirm with RedDot before going live
- **Opening hours**: placeholder "Daily, 11am till late" (marked "to confirm" on the page).
- **Beer descriptions** are short and generic. Get tasting notes and ABVs. Confirm Monster Green Lager is still pouring.
- **Wedding pricing table**: rebuilt from the current weddings page. Check that the column mapping is right.
- **Upper indoor deck capacity**: their weddings page says 30, corporate page says 40. Both are kept as they appear on their site.
- **Food menu** descriptions are general, based on their photos. Get the real menu and link the PDF.
- **Photos** are hotlinked from their Wix media library. Get originals before launch.
- **Enquiry form** is a front-end demo. Wire it to Netlify Forms or email.
