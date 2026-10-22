"""Attach map coordinates ("geo": [lat, lng, approx]) to every address in data/widget_data.json.

Coordinates come from the free U.S. Census Geocoder and are cached in data/geocodes.json, so the network is only used
for addresses that are new or changed. A PO box (or an address the Census cannot match) falls back to the centre of its
ZIP code (approx = 1). Run from the repository root:  python scripts/geocode.py
"""
import json, os, re, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding='utf-8')
DATA = 'data/widget_data.json'
CACHE = 'data/geocodes.json'
ZIPS = json.load(open('data/zips.json', encoding='utf-8'))
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}

SUITE = re.compile(r'^(suite|ste\.?|unit|#|bldg\.?|building|rm\.?|room|floor|fl\.?)\b', re.I)


def candidates(addr):
    """Cleaned street-address variants to try, most specific first."""
    a = re.sub(r'\([^)]*\)', '', addr)
    a = re.sub(r'\s+', ' ', a).strip()
    if re.search(r'\bP\.?\s?O\.?\s*(box|drawer)\b', a, re.I):
        return []
    parts = [p.strip() for p in a.split(',') if p.strip()]
    i = next((k for k, p in enumerate(parts) if re.match(r'^\d', p)), None)
    if i is None:
        return []
    parts = parts[i:]
    full = ', '.join(parts)
    short = ', '.join(p for k, p in enumerate(parts) if k == 0 or not SUITE.match(p))
    # "1155 S. Telshor Suite B" style: drop an inline suite
    short = re.sub(r'\s+(suite|ste\.?|unit|bldg\.?|#)\s*\S+', '', short, flags=re.I)
    return [full] if full == short else [full, short]


def census(q):
    url = ('https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?benchmark=Public_AR_Current&format=json&address='
           + urllib.parse.quote(q))
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'mveda-resource-guide'}), timeout=25) as r:
                m = json.load(r)['result']['addressMatches']
            if m:
                return [round(m[0]['coordinates']['y'], 6), round(m[0]['coordinates']['x'], 6)]
            return None
        except Exception:
            time.sleep(1.5)
    return None


def osm(q):
    """Second opinion for street addresses the Census cannot match (OpenStreetMap Nominatim; 1 request per second)."""
    url = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=us&q=' + urllib.parse.quote(q)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'mveda-resource-guide (brian@mveda.com)'}), timeout=25) as r:
            m = json.load(r)
        if m:
            return [round(float(m[0]['lat']), 6), round(float(m[0]['lon']), 6)]
    except Exception:
        pass
    return None


def locate(addr):
    key = re.sub(r'\s+', ' ', addr).strip()
    if key in cache:
        return cache[key]
    pt, src = None, None
    for q in candidates(key):
        pt = census(q); time.sleep(0.15)
        if pt:
            src = 'census'; break
    if not pt:
        for q in candidates(key):
            pt = osm(q); time.sleep(1.1)
            if pt:
                src = 'osm'; break
    if not pt:
        z = re.search(r'\b(\d{5})(?:-\d{4})?\s*$', key)
        if z and z.group(1) in ZIPS:
            pt, src = ZIPS[z.group(1)][:2], 'zip'
    cache[key] = {'lat': pt[0], 'lng': pt[1], 'src': src} if pt else {'src': 'none'}
    return cache[key]


def geo(addr):
    if not addr:
        return None
    g = locate(addr)
    return [g['lat'], g['lng'], 0 if g['src'] in ('census', 'osm') else 1] if g.get('lat') is not None else None


data = json.load(open(DATA, encoding='utf-8'))
n = 0
for h1 in data:
    for h2 in h1['subsections']:
        for e in h2['entries']:
            e.pop('geo', None)
            if e.get('locations'):
                for l in e['locations']:
                    l.pop('geo', None)
                    g = geo(l.get('address'))
                    if g:
                        l['geo'] = g; n += 1
            else:
                g = geo(e.get('address'))
                if g:
                    e['geo'] = g; n += 1
json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
srcs = {}
for v in cache.values(): srcs[v['src']] = srcs.get(v['src'], 0) + 1
print(f'geocoded {n} addresses; cache sources: {srcs}')
