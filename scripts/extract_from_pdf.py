# -*- coding: utf-8 -*-
"""
Extracts the full Business Resource Guide dataset from the authoritative print PDF
(NMBorderplex-Business-Resource-Guide_BLEED_CMYK.pdf), using font size/family as the
structural signal (the PDF has no semantic tags, but its styling is fully consistent):

  10.5/9.0  Oswald-SemiBold / SourceSans3-(Semi)Bold  -> page chrome (section number corner,
            running header, footer, page number) -- always skip
  72.0/30.0 Oswald-Bold                               -> big section-divider page -- skip text,
            but use to confirm H1 boundaries
  12.0      SourceSerif4-Italic (on divider page)     -> H1 tagline -- skip
  15.8      Oswald-SemiBold                           -> H2 subsection header
  10.5      SourceSerif4-Italic                       -> H2 subsection tagline -- skip
  13.5      Oswald-SemiBold                           -> H3 industry-category header
                                                          (Industry-Specific Incentives only)
  8.6       SourceSans3-Bold                          -> per-entry category/kicker label
  9.0       SourceSans3-Bold  (ALL CAPS, own block)   -> mini-list group label (e.g. "COMMUNITY
                                                          WATER SYSTEMS", "OTHER AREA BANKS")
  11.2      SourceSans3-Bold                          -> entry name (may wrap 2 lines)
  9.8       SourceSans3-Bold                          -> mini-list entry name (may wrap 2 lines)
  10.1      SourceSans3-Regular                       -> description (may wrap many lines)
  9.4       SourceSans3-Regular                       -> address / phone+website block
  9.0       SourceSans3-Regular (under a mini-list)   -> phone-only line

A repeated 8.6-kicker across 2+ consecutive entries within the same H2 is collapsed into
one "group" header (e.g. "CITY OF LAS CRUCES" shown once over its 3 departments, "GENERAL
CONTRACTOR" shown once over its 3 contractors) -- a single generalization of the org-grouping
already used elsewhere in the widget, now driven by the print document's own repetition
instead of being special-cased per section.
"""
import re, json, sys
import fitz

PDF_PATH = sys.argv[1]
OUT_PATH = sys.argv[2]

doc = fitz.open(PDF_PATH)

H1_MARKERS = {
    'G E N E RA L BU S I N E S S A S S I S T A N C E': 'General Business Assistance',
    'LOC A L BU S I N E S S D I RE C T ORY': 'Local Business Directory',
    'FI N A N C I N G & C A PI T A L': 'Financing & Capital',
    'W ORKFORC E': 'Workforce',
    'I N C E N T I V E S': 'Incentives',
}
SKIP_EXACT = {'N M BO R D ER P L EX.C O M', 'BU S INES S RES OU RCE G U ID E'}
# mangled small-caps spacing loses real word-boundary info entirely (kerning gaps and word
# gaps render identically), so -- same as H1_MARKERS -- these are hardcoded, not regex-derived
MINILIST_LABELS = {
    'C OMMU N I T Y W AT E R S YS T E MS': 'COMMUNITY WATER SYSTEMS',
    'OT H E R A RE A BA N KS & C RE D I T U N I ON S': 'OTHER AREA BANKS & CREDIT UNIONS',
}

PHONE_RE = re.compile(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}')
ZIP_RE = re.compile(r'\d{5}(-\d{4})?\s*$')


def clean(t):
    return (t.replace('ﬀ', 'ff').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
             .replace('ﬃ', 'ffi').replace('ﬄ', 'ffl').strip())


def join_wrapped(lines):
    """Join word-wrapped lines, closing up a trailing hyphen from a mid-word line break
    (e.g. ['early-', 'stage'] -> 'early-stage') instead of inserting a stray space."""
    out = ''
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out.endswith('-'):
            out += ln
        elif out:
            out += ' ' + ln
        else:
            out = ln
    return out


sections = []  # [{title, subsections:[{title, entries:[...]}]}]
cur_h1 = None
cur_h2 = None
cur_h3_group = None  # for Industry-Specific Incentives sub-category (13.5pt)

pending = None  # {'category':..., 'name':[...], 'desc':[...], 'addr':[...], 'url':''}
last_size_bucket = None


def bucket(size):
    # snap to the nearest known signature, tolerant of tiny CMYK-render float drift
    for s in (8.6, 9.0, 9.4, 9.8, 10.1, 10.5, 11.2, 13.5, 15.8, 30.0, 72.0):
        if abs(size - s) < 0.3:
            return s
    return round(size, 1)


def split_addr_phone_url(lines):
    address_lines = []
    phone = ''
    url = ''
    for ln in lines:
        m = PHONE_RE.search(ln)
        if m:
            phone = m.group(0)
            rest = ln[m.end():]
            rest = rest.lstrip(' ·').strip()
            if rest:
                url = (url + rest) if not url else url
            continue
        if re.match(r'^[a-z0-9][\w.-]*\.(com|org|net|gov|us|edu|biz)(/\S*)?$', ln.strip(), re.I) or ln.strip().startswith(('www.', 'http')):
            url = (url + ln.strip()) if not url.endswith(ln.strip()) else url
            continue
        # a line that's a continuation of a url broken across lines (no space, no comma)
        if url and not ZIP_RE.search(ln) and ',' not in ln and ' ' not in ln.strip():
            url += ln.strip()
            continue
        address_lines.append(ln)
    address = join_wrapped(address_lines)
    address = re.sub(r'\s+', ' ', address).strip().rstrip(',')
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return address, phone, url


def flush_entry():
    global pending
    if pending is None or mode == 'minilist':
        return
    name = clean(join_wrapped(pending['name']))
    if name:
        desc = clean(join_wrapped(pending['desc']))
        address, phone, url = split_addr_phone_url([clean(l) for l in pending['addr']])
        cur_h2['entries'].append({
            'name': name,
            'category': pending['category'],
            'group': '',
            'url': url,
            'desc': desc,
            'address': address,
            'phone': phone,
        })
    pending = None


def flush_minilist():
    global pending
    if pending is None or mode != 'minilist':
        return
    name = clean(join_wrapped(pending['name']))
    if name:
        phone = ''
        for ln in pending['addr']:
            m = PHONE_RE.search(ln)
            if m:
                phone = m.group(0)
        cur_h2['entries'].append({
            'name': name, 'category': '', 'group': pending['category'],
            'url': '', 'desc': '', 'address': '', 'phone': phone,
        })
    pending = None


mode = None  # None | 'entry' | 'minilist'

for pno in range(doc.page_count):
    page = doc[pno]
    d = page.get_text('dict')
    spans = []
    for block in d['blocks']:
        if 'lines' not in block:
            continue
        for line in block['lines']:
            for span in line['spans']:
                t = span['text'].strip()
                if not t:
                    continue
                spans.append((bucket(span['size']), span['font'], t))

    merged = []
    for sp in spans:
        if merged and sp[0] == 8.6 and sp[1] == 'SourceSans3-Bold' and merged[-1][0] == 8.6 and merged[-1][1] == 'SourceSans3-Bold':
            merged[-1] = (8.6, sp[1], merged[-1][2] + ' ' + sp[2])
        else:
            merged.append(sp)
    spans = merged
    for size, font, text in spans:
        if text in SKIP_EXACT:
            continue
        if size in (72.0, 30.0) or (size == 15.0 and font.startswith('Oswald')):
            continue  # big divider page number/title, or bottom page-number
        if font == 'Oswald-SemiBold' and re.match(r'^\d{1,2}$', text):
            continue  # page-corner section number like "01"
        if text in H1_MARKERS:
            if cur_h1 is None or cur_h1['title'] != H1_MARKERS[text]:
                flush_entry(); flush_minilist()
                cur_h1 = {'title': H1_MARKERS[text], 'subsections': []}
                sections.append(cur_h1)
                cur_h2 = None
            continue  # this running-header text is never itself content
        if size == 9.0 and 'Bold' in font and text.isupper() and len(text.replace(' ', '')) > 3 and cur_h2 is not None:
            # mini-list group label (e.g. "COMMUNITY WATER SYSTEMS") -- also rendered in the
            # same spaced-letter small-caps style as the page running header below, so this
            # must be checked first or the generic header-skip would eat it.
            flush_entry(); flush_minilist()
            mode = 'minilist'
            cur_h3_group = MINILIST_LABELS.get(text, clean(text))
            continue
        if font.startswith('SourceSans3') and ('Bold' in font or 'SemiBold' in font) and re.search(r'(?<![A-Za-z])[A-Z] [A-Z] [A-Z] [A-Z](?![A-Za-z])', text):
            continue  # spaced-caps running header e.g. "G E N E RA L ..."
        if size == 12.0 and font == 'SourceSerif4-Italic':
            continue  # H1 tagline on divider page

        if size == 15.8 and font == 'Oswald-SemiBold':
            flush_entry()
            flush_minilist()
            title = clean(re.sub(r'\s*\(CONTINUED\)\s*$', '', text, flags=re.I))
            existing = next((h2 for h2 in (cur_h1['subsections'] if cur_h1 else []) if h2['title'] == title), None)
            cur_h2 = existing or {'title': title, 'entries': []}
            if existing is None and cur_h1 is not None:
                cur_h1['subsections'].append(cur_h2)
            cur_h3_group = None
            mode = 'entry'
            continue

        if cur_h2 is None:
            continue

        if size == 10.5 and font == 'SourceSerif4-Italic':
            continue  # H2 tagline

        if size == 13.5 and font == 'Oswald-SemiBold':
            flush_entry()
            cur_h3_group = clean(text)
            continue

        if mode == 'minilist':
            if size == 9.8 and font == 'SourceSans3-Bold':
                if pending is not None and not pending['addr']:
                    pending['name'].append(text)  # wrapped second line of the same name
                else:
                    flush_minilist()
                    pending = {'category': cur_h3_group, 'name': [text], 'desc': [], 'addr': []}
                continue
            if size == 9.0 and font == 'SourceSans3-Regular' and pending is not None:
                pending['addr'].append(text)
                continue
            # fell out of minilist shape -> treat as a normal entry from here
            flush_minilist()
            mode = 'entry'

        if size == 11.2 and font == 'SourceSans3-Bold':
            if pending is not None and pending['desc']:
                flush_entry()
            elif pending is not None and not pending['desc'] and not pending['addr']:
                pending['name'].append(text)
                continue
            else:
                flush_entry()
            pending = {'category': cur_h3_group or '', 'name': [text], 'desc': [], 'addr': []}
            continue

        if size == 8.6 and font == 'SourceSans3-Bold':
            flush_entry()
            cur_h3_group = clean(text)
            continue

        if size == 10.1 and font == 'SourceSans3-Regular' and pending is not None:
            pending['desc'].append(text)
            continue

        if size in (9.0, 9.4) and font == 'SourceSans3-Regular' and pending is not None:
            pending['addr'].append(text)
            continue

        # Industry-Specific Incentives: bare 10.1-regular names with a 13.5pt category above,
        # and no bold name span at all -- handled separately via INDUSTRY_INCENTIVES_MAP below.

flush_entry()
flush_minilist()

# ---- fix a page-layout artifact: a transitional page can place the NEXT section's first
# H2 block (reading-order-wise) before the big divider text that marks the H1 switch,
# so its entries land under the wrong (earlier) H1. Any H2 title that exists in two
# consecutive H1 sections is such a split -- merge the earlier entries into the later H2.
for i in range(len(sections) - 1):
    h1a, h1b = sections[i], sections[i + 1]
    for h2a in list(h1a['subsections']):
        h2b = next((h for h in h1b['subsections'] if h['title'] == h2a['title']), None)
        if h2b is not None:
            h2b['entries'] = h2a['entries'] + h2b['entries']
            h1a['subsections'].remove(h2a)

# ---- Industry-Specific Incentives: the PDF wraps bare program names across lines with no
# per-item marker, so names can't be reliably re-segmented from this layout alone. Reuse the
# already-correct names from the prior (docx-sourced) dataset and apply the industry grouping
# exactly as printed in the PDF, read by hand from its INDUSTRY-SPECIFIC INCENTIVES page.
INDUSTRY_GROUPS = {
    'Aircraft Refurbishing or Remodeling Tax Deduction': 'AEROSPACE/AVIATION',
    'Aerospace Research and Development Tax Deduction': 'AEROSPACE/AVIATION',
    'Aircraft Manufacturing Tax Deduction': 'AEROSPACE/AVIATION',
    'Space Gross Receipts Tax Deduction': 'AEROSPACE/AVIATION',
    'Agricultural Business Tax Deductions and Exemptions': 'AGRI-BUSINESS',
    'Beer and Wine Producers Preferential Tax Rate': 'AGRI-BUSINESS',
    'Advanced Energy Tax Credits': 'CLEAN AND RENEWABLE ENERGY',
    'Alternative Energy Product Manufacturers Tax Credit': 'CLEAN AND RENEWABLE ENERGY',
    'Solar Energy Systems Gross Receipts Tax Exemption': 'CLEAN AND RENEWABLE ENERGY',
    'Solar Market Development Income Tax Credit': 'CLEAN AND RENEWABLE ENERGY',
    'Sustainable Building Tax Credit': 'CLEAN AND RENEWABLE ENERGY',
    'Hybrid Vehicle Tax Exemption': 'CLEAN AND RENEWABLE ENERGY',
    'Geothermal Electricity Generation Tax Credit and GRT Deduction': 'CLEAN AND RENEWABLE ENERGY',
    'Biomass-related Equipment and Materials Deduction': 'CLEAN AND RENEWABLE ENERGY',
    '25% Film Production Tax Rebate': 'CREATIVE MEDIA',
    'Film Investment Loan Program': 'CREATIVE MEDIA',
    'Angel Investment Tax Credit': 'FINANCE',
    'Financial Management Tax Credit': 'FINANCE',
    'Research and Development Gross Receipts Tax Deduction': 'TECHNOLOGY AND MANUFACTURING',
    'Technology Jobs Tax Credit': 'TECHNOLOGY AND MANUFACTURING',
    'Rural Software and Web Site Gross Receipts Tax Deduction': 'TECHNOLOGY AND MANUFACTURING',
    'Investment Tax Credit for Manufacturers': 'TECHNOLOGY AND MANUFACTURING',
    'Single Sales Factor Apportionment for Manufacturers': 'TECHNOLOGY AND MANUFACTURING',
    'Manufacturers Consumables Gross Receipts Tax Deduction': 'TECHNOLOGY AND MANUFACTURING',
    'Web Hosting Gross Receipts Tax Deduction': 'TECHNOLOGY AND MANUFACTURING',
}
PRIOR_DATA_PATH = sys.argv[3] if len(sys.argv) > 3 else None
if PRIOR_DATA_PATH:
    prior = json.load(open(PRIOR_DATA_PATH, encoding='utf-8'))
    prior_entries = {}
    for h1 in prior:
        if h1['title'] == 'Incentives':
            for h2 in h1['subsections']:
                if h2['title'] == 'Industry Specific Incentives':
                    for e in h2['entries']:
                        prior_entries[e['name'].strip()] = e
    for h1 in sections:
        if h1['title'] != 'Incentives':
            continue
        for h2 in h1['subsections']:
            if h2['title'] == 'INDUSTRY-SPECIFIC INCENTIVES':
                for name, group in INDUSTRY_GROUPS.items():
                    src = prior_entries.get(name)
                    if src is None:
                        print('WARNING: no prior entry found for', name)
                        continue
                    h2['entries'].append({
                        'name': src['name'], 'category': '', 'group': group,
                        'url': src.get('url', ''), 'desc': src.get('desc', ''),
                        'address': src.get('address', ''), 'phone': src.get('phone', ''),
                    })

# ---- collapse a repeated consecutive 8.6pt category/kicker into one "group" header ----
for h1 in sections:
    for h2 in h1['subsections']:
        ents = h2['entries']
        i = 0
        while i < len(ents):
            if not ents[i]['category']:
                i += 1
                continue
            j = i + 1
            while j < len(ents) and ents[j]['category'] == ents[i]['category']:
                j += 1
            if j - i >= 2:
                for k in range(i, j):
                    ents[k]['group'] = ents[k]['category']
                    ents[k]['category'] = ''
            i = j

total = sum(len(h2['entries']) for h1 in sections for h2 in h1['subsections'])
print('TOTAL ENTRIES:', total)
for h1 in sections:
    print(h1['title'], sum(len(h2['entries']) for h2 in h1['subsections']))
    for h2 in h1['subsections']:
        print('  -', h2['title'], len(h2['entries']))

json.dump(sections, open(OUT_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
