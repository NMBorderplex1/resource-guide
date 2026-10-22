# NM Borderplex Business Resource Guide — Interactive Edition

A searchable, bilingual (English / Español) web version of the printed *NM Borderplex Business Resource Guide* for Las Cruces and Doña Ana County, NM. It is a single self-contained HTML/CSS/JS file that can be pasted into a Divi **Code module** (or hosted as a page). The printed guide PDF is the authoritative source; this repo turns the PDF into the widget.

## What the widget does

- Search by name, service or keyword (works in English and Spanish); five section tabs
- **Locations in** chips (Las Cruces, Anthony, Sunland Park, Hatch, Mesilla, …); organizations with several county locations list every one, and the nearest match is highlighted
- **Closest to you**: visitors can press *Use my location* or type a ZIP code and see listings sorted by straight-line distance (the nearest branch of multi-location organizations is shown first). A visitor's location stays in their browser; nothing is sent anywhere. Listings without a street address are not part of the distance view.
- EN / ES toggle, tap-to-call and tap-for-directions links, photo section banners with parallax
- Deep links, e.g. `#sec=incentives&near=anthony&q=bank&lang=es`
- Scoped styles (everything lives under `.mv-widget`) so the host page is not affected

## Use it on the website

### Option A (recommended): GitHub Pages + an iframe, so pushes to this repo update the site

One-time setup:

1. In this repository: **Settings → Pages → Build and deployment → Source: "Deploy from a branch"**, branch `main`, folder `/docs`. (On a free GitHub plan the repository must be public.)
2. After a minute the widget is live at `https://nmborderplex1.github.io/resource-guide/`.
3. In Divi, add a **Code module** with:

```html
<iframe id="mv-guide" allow="geolocation" src="https://nmborderplex1.github.io/resource-guide/?theme=light&pdfEn=PDF_URL_ENGLISH&pdfEs=PDF_URL_SPANISH"
        style="width:100%;height:900px;border:0" loading="lazy" title="Business Resource Guide"></iframe>
<script>
/* the widget reports its height so the frame fits on every screen size */
window.addEventListener('message', function (e) {
  var f = document.getElementById('mv-guide');
  if (f && e.source === f.contentWindow && e.data && e.data.type === 'mv-resize' && e.data.height > 200 && e.data.height < 3000) {
    f.style.height = e.data.height + 'px';
  }
});
</script>
```

`allow="geolocation"` is required for the *Use my location* button to work inside the iframe (the ZIP code box works either way).

The width follows the Divi column. The height is set automatically by the small script (900 px is only the starting height before the widget loads); without the script the frame stays at 900 px, which can cut off the bottom on phones.

Settings go in the iframe address (all optional):

| Parameter | Meaning |
|---|---|
| `theme` | `auto` (visitor's system setting), `light` or `dark` |
| `height` | Height in pixels of the scrolling results list (200–1600, default 440); the whole widget is about 430 px taller than this. |
| `pdfEn`, `pdfEs`, `contactUrl` | Links for the PDF download button (hidden until set) and the call-to-action button; only `nmborderplex.com` and `mveda.com` addresses are accepted |
| `phone` | Phone number on the call-to-action |

Deep links work on the Pages address itself (e.g. `…/#sec=incentives&near=anthony&lang=es`). Updating: run `python build.py` (or `build.py all …`), commit, and push; `docs/index.html` is rebuilt and Pages redeploys.

### Option B: paste into a Divi Code module

1. Build (below) or copy `dist/business-resource-finder-DIVI-EMBED.html`.
2. In Divi, add a **Code module** and paste the file's contents (needs a user who may add unfiltered HTML).
3. Edit the `CONFIG` block at the top of the `<script>`:

| Setting | Meaning |
|---|---|
| `pdfEn`, `pdfEs` | URLs of the English / Spanish PDF guides (the download button stays hidden until set) |
| `contactUrl`, `phone` | Call-to-action button and phone number |
| `ctaClass` | Optional CSS class on the button, e.g. to trigger a Divi popup |
| `theme` | `'auto'` (visitor's system setting), `'light'` or `'dark'` |
| `height` | Height in pixels of the scrolling results area (default 440) |

## Repository layout

```
src/widget.html        widget template (HTML + CSS + JS, placeholders for images and data)
src/assets/            logos and photo banners
data/                  extracted guide data (see below) and multi-location research
scripts/               PDF extractors and data/build scripts
build.py               one entry point for the pipeline
dist/                  built output: full page and the Divi Code-module embed
docs/                  index.html = the page GitHub Pages serves (built by build.py)
```

## Build

Python 3.10+ and `pymupdf` (only needed to read PDFs).

```bash
python build.py                       # rebuild dist/ from the committed data
python build.py data                  # regenerate data/widget_data.json from the committed extracts, then rebuild dist/
python build.py all --en EN_TRIM.pdf --es ES_TRIM.pdf   # re-extract both PDFs first
```

Pipeline (`build.py all`):

1. `extract_from_pdf.py` / `extract_es.py` parse the PDFs by font size and family (the print layout has no semantic tags, but its styling is consistent: 11.2 pt bold = entry name, 10.1 pt = description, 9.4/9.0 pt = address and phone, 8.6 pt bold = kicker, 15.8 pt = subsection, and so on). Spanish is aligned to English entry-for-entry by position.
2. `rebuild_from_pdf.py` adds the Industry-Specific Incentives list (not parseable from the PDF's wrapped layout) and cleans extraction artifacts such as phone extensions that land in URL fields.
3. `apply_locations.py` merges the multi-location research in `data/multiloc/`.
4. `build_bilingual.py` attaches the Spanish text.
5. `geocode.py` adds map coordinates to every address (U.S. Census geocoder, with OpenStreetMap as a fallback; PO boxes and unmatched addresses use the centre of their ZIP code and are shown as approximate, e.g. "~2.1 mi"). Results are cached in `data/geocodes.json`, so the network is only used for new or changed addresses. `data/zips.json` (ZIP code centres for Doña Ana County and El Paso, from `scripts/build_zips.py`) powers the ZIP code box.
6. `build_widget.py` writes `dist/` and `docs/`.

If the printed guide changes, re-run `build.py all` against the new PDFs and review the diff of `data/widget_data.json` before publishing. PDFs and other large source files are intentionally not stored in this repository (see `.gitignore`).

## Data notes

The data comes from a printed publication that is reviewed by MVEDA staff; entries can be out of date between editions. Contact details were spot-checked against each organization's own website in October 2026.

## Copyright

(c) 2026 Mesilla Valley Economic Development Alliance (MVEDA). All rights reserved. This repository is visible for hosting and maintaining the interactive guide only; see [LICENSE](LICENSE). Logos and names belong to their owners.

## Web-only entries

`data/extra_entries.json` holds listings that are not in the print guide (currently three FY27 MVEDA partners). The data pipeline adds them after every PDF extraction, so they survive rebuilds. Edit that file to add or remove web-only entries.
