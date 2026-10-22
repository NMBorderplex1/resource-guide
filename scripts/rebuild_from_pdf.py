import json, re, sys, copy
sys.stdout.reconfigure(encoding='utf-8')

PDF = json.load(open('data/en_pdf.json', encoding='utf-8'))
OLD = json.load(open('data/widget_data_en.json', encoding='utf-8'))  # log-patched widget data

def norm(s):
    return re.sub(r'\s+', ' ', (s or '')).strip().lower()

def entries(d):
    for h1 in d:
        for h2 in h1['subsections']:
            for e in h2['entries']:
                yield h1, h2, e

report = []

# 1. Industry-Specific Incentives: PDF extractor can't segment it; names/groups are unchanged
#    in the new PDF (verified against page 31), so reuse the widget's 25 entries.
old_ind = [e for h1, h2, e in entries(OLD) if h2['title'].upper() == 'INDUSTRY-SPECIFIC INCENTIVES']
assert len(old_ind) == 25, len(old_ind)
for h1, h2, e in entries(PDF):
    pass
for h1 in PDF:
    for h2 in h1['subsections']:
        if h2['title'].upper() == 'INDUSTRY-SPECIFIC INCENTIVES':
            assert not h2['entries']
            h2['entries'] = copy.deepcopy(old_ind)

# 2. Carry over descriptions the print PDF doesn't print (widget-only enrichment) where PDF desc is empty
old_by_key = {}
for h1, h2, e in entries(OLD):
    old_by_key.setdefault((h2['title'].upper(), norm(e['name'])), []).append(e)
carried = 0
for h1, h2, e in entries(PDF):
    if e['desc']:
        continue
    cands = old_by_key.get((h2['title'].upper(), norm(e['name'])), [])
    for c in cands:
        if c['desc']:
            e['desc'] = c['desc']; carried += 1; break
report.append(f'descriptions carried over from prior widget data: {carried}')

# 3. Extraction-artifact cleanup (PDF prints "phone . website" on one line and rep emails on separate lines)
def by_name(name, group_or_cat=None):
    out = []
    for h1, h2, e in entries(PDF):
        if e['name'] == name and (group_or_cat is None or (e['group'] or e['category']) == group_or_cat):
            out.append(e)
    assert len(out) <= 1, (name, len(out))
    return out[0] if out else None   # entry may have been dropped from the print guide

def fix(e, **f):
    if e is None:
        return
    for k, v in f.items():
        if e[k] != v:
            report.append(f"{e['name']} :: {k}: {e[k]!r} -> {v!r}")
            e[k] = v

fix(by_name('Community Development', 'TOWN OF MESILLA'),
    url='https://mesillanm.gov/government/departments/economic-community-development',
    phone='(575) 524-3262, ext. 104')
fix(by_name('NAI 1st Valley'), url='https://1stvalley.com', phone='(575) 521-1535, ext. 108')
fix(by_name('Killam Development'), url='https://killamdevelopment.com', phone='(956) 724-7141, ext. 212')
fix(by_name('USDA Rural Development'), url='https://rd.usda.gov/nm', phone='(575) 522-8775, ext. 4')
fix(by_name('Aries Worldwide Logistics'), url='https://ariesww.com')
fix(by_name('WaFd Bank'), url='https://wafdbank.com')
for nm, rx in [('New Mexico Economic Development Department (EDD)', r'^(?:\S+@\S+\s+)+'), ('VA Veteran Readiness & Employment (VR&E)', r'\s+\S+@\S+$')]:
    e = by_name(nm)
    if e:
        fix(e, address=re.sub(rx, '', e['address']))
e = by_name('Las Cruces Association of Realtors')
if e:
    fix(e, address=re.sub(r'\s+lascrucesassociationofrealtors\.co\s?m$', '', e['address']), url=e['url'] or 'https://lcarnm.com')

# 3b. Web-only entries (FY27 partners that are not in the print guide), from data/extra_entries.json
for item in json.load(open('data/extra_entries.json', encoding='utf-8')):
    h2 = next((h2 for h1 in PDF if h1['title'] == item['h1'] for h2 in h1['subsections'] if h2['title'].upper() == item['h2']), None)
    assert h2 is not None, item['h2']
    if not any(norm(x['name']) == norm(item['entry']['name']) for x in h2['entries']):
        h2['entries'].append(dict(item['entry']))
        report.append('added web-only entry: ' + item['entry']['name'])

# 3c. Keep each headed group's companies together: a card with a different label between two members
#     (e.g. Dekker, "Architecture & Planning") would otherwise split one group heading into two.
for h1 in PDF:
    for h2 in h1['subsections']:
        order, buckets = [], {}
        for e in h2['entries']:
            g = e['group']
            if g and g in buckets:
                buckets[g].append(e)
            else:
                if g:
                    buckets[g] = [e]
                order.append(('g', g) if g else ('e', e))
        merged = []
        for kind, v in order:
            merged.extend(buckets[v] if kind == 'g' else [v])
        if [x['name'] for x in merged] != [x['name'] for x in h2['entries']]:
            report.append('regrouped ' + h2['title'])
        h2['entries'] = merged

# 4. Widget-only decision (user: "it could live in both for the ones that are specific to a city"):
#    keep the city-specific utilities also under their municipality's Licensing group, values taken from the PDF's Utilities entries.
util = {}
for h1, h2, e in entries(PDF):
    if h2['title'].upper().startswith('UTILITIES'):
        util[e['name']] = e
lic = next(h2 for h1, h2, e in entries(PDF) if h2['title'].upper().startswith('LICENSING'))
DUPES = [('Las Cruces Utilities', 'CITY OF LAS CRUCES'), ('Camino Real Regional Utility Authority', 'CITY OF SUNLAND PARK'),
         ('Anthony Water & Sanitation District', 'CITY OF ANTHONY'), ('Doña Ana County Utilities', 'DOÑA ANA COUNTY')]
for name, grp in DUPES:
    src = copy.deepcopy(util[name]); src['category'] = ''; src['group'] = grp
    idxs = [i for i, x in enumerate(lic['entries']) if (x['group'] or x['category']) == grp]
    assert idxs, grp
    # normalize municipality heads: PDF singletons keep category; convert to group so the head renders
    for i in idxs:
        x = lic['entries'][i]
        if x['category'] and not x['group']:
            x['group'], x['category'] = x['category'], ''
    lic['entries'].insert(max(idxs) + 1, src)
    report.append(f'duplicated {name} under {grp}')
# remaining singleton municipality heads (Mesilla, Hatch) -> group heads
for x in lic['entries']:
    if x['category'] and not x['group'] and x['category'].startswith(('TOWN OF', 'VILLAGE OF', 'CITY OF')):
        x['group'], x['category'] = x['category'], ''

# 5. sanity
total = sum(len(h2['entries']) for h1 in PDF for h2 in h1['subsections'])
report.append(f'TOTAL ENTRIES: {total}')
json.dump(PDF, open('data/widget_data_from_pdf.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(report))
