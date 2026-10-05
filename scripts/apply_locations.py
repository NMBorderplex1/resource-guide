import json, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'data/widget_data_from_pdf.json'
OUT = 'data/widget_data_en.json'
d = json.load(open(BASE, encoding='utf-8'))

def norm(s):
    return re.sub(r'\s+', ' ', (s or '')).strip().lower()

entries = [e for h1 in d for h2 in h1['subsections'] for e in h2['entries']]
applied = []
SKIP = {'Union Pacific', 'W Silver Recycling', 'Anthony Water & Sanitation District'}

# Hardcoded (confirmed by Brian's map listing, 2026-10-02)
for e in entries:
    if e['name'].startswith('NM Workforce Solutions'):
        e['locations'] = [
            {'label': 'Las Cruces', 'address': '226 S. Alameda Blvd., Las Cruces, NM 88005', 'phone': '(575) 524-6250'},
            {'label': 'Sunland Park', 'address': '1500 Appaloosa Dr., Suite A-160, Sunland Park, NM 88063', 'phone': '(575) 618-1249'},
        ]
        applied.append(e['name'] + ' (manual)')

for f in sorted(glob.glob('data/multiloc/*_result.json')):
    res = json.load(open(f, encoding='utf-8'))
    inp = json.load(open(f.replace('_result', ''), encoding='utf-8'))
    for r, i in zip(res, inp):
        if r.get('status') != 'multiple_locations' or r.get('confidence') == 'low':
            continue
        if i['name'] in SKIP:
            continue
        locs = [l for l in r.get('locations', []) if l.get('address')]
        locs = [l for l in locs if not re.search(r'mobile pantry|directory listings|Healthgrades|not FYI\+ website|BBB profile|Outside Dona Ana', l.get('label', '') + ' ' + l.get('note', ''), re.I)]
        if len(locs) < 2:
            continue
        for l in locs:
            if l.get('note') and not re.match(r'(Mon|Daily|M-F|Wed and|Payment center|Full service|Freestanding|Includes|Houses|Main campus|MountainView Medical Group|Youth Success|Family Success|Adjacent|Open )', l['note']):
                l['note'] = ''
        num =lambda a: (re.match(r'\s*(\d+)', a or '') or [None, None])[1]
        if num(locs[0]['address']) and num(locs[0]['address']) == num(i['address']):
            locs[0]['address'] = i['address']
            if i['phone']:
                locs[0]['phone'] = i['phone']
        for e in entries:
            if norm(e['name']) == norm(i['name']) and norm(e['address']) == norm(i['address']) and 'locations' not in e:
                e['locations'] = [{k: v for k, v in l.items() if k in ('label', 'address', 'phone', 'note') and v} for l in locs]
                applied.append(f"{e['name']} ({len(locs)} locations, {r.get('confidence')})")

json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(applied), 'entries with locations')
for a in applied: print(' ', a)
