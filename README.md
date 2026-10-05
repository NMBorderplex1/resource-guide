# NM Borderplex Business Resource Guide — Interactive Edition

A searchable, bilingual (English / Español) web version of the printed *NM Borderplex Business Resource Guide* for Las Cruces and Doña Ana County, NM. It is a single self-contained HTML/CSS/JS file that can be pasted into a Divi **Code module** (or hosted as a page). The printed guide PDF is the authoritative source; this repo turns the PDF into the widget.

## What the widget does

- Search by name, service or keyword (works in English and Spanish); five section tabs
- **Locations in** chips (Las Cruces, Anthony, Sunland Park, Hatch, Mesilla, …); organizations with several county locations list every one, and the nearest match is highlighted
- EN / ES toggle, tap-to-call and tap-for-directions links, photo section banners with parallax
- Deep links, e.g. `#sec=incentives&near=anthony&q=bank&lang=es`
- Scoped styles (everything lives under `.mv-widget`) so the host page is not affected

## Use it on the website

1. Build (below) or copy `dist/business-resource-finder-DIVI-EMBED.html`.
2. In Divi, add a **Code module** and paste the file's contents.
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
dist/                  built output (committed so it can be used without building)
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
4. `build_bilingual.py` attaches the Spanish text; `build_widget.py` writes `dist/`.

If the printed guide changes, re-run `build.py all` against the new PDFs and review the diff of `data/widget_data.json` before publishing. PDFs and other large source files are intentionally not stored in this repository (see `.gitignore`).

## Data notes

The data comes from a printed publication that is reviewed by MVEDA staff; entries can be out of date between editions. Contact details were spot-checked against each organization's own website in October 2026.
