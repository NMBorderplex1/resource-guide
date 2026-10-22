"""One-time helper: build data/zips.json (ZIP code -> [lat, lng, place]) for Doña Ana County and the El Paso area,
using the free zippopotam.us service. Only needed to refresh the table; the widget embeds data/zips.json.
Run from the repository root:  python scripts/build_zips.py
"""
import json, time, urllib.request, urllib.error

BOX = {'NM': (31.7, 32.95, -107.5, -106.3), 'TX': (31.55, 32.1, -106.75, -106.0)}   # lat min/max, lng min/max
CANDIDATES = [(f'{z}', 'NM') for z in list(range(87930, 87950)) + list(range(88000, 88090))] + [(f'{z}', 'TX') for z in range(79901, 79940)]

zips = {}
for z, st in CANDIDATES:
    try:
        with urllib.request.urlopen(urllib.request.Request(f'https://api.zippopotam.us/us/{z}', headers={'User-Agent': 'mveda-resource-guide'}), timeout=15) as r:
            d = json.load(r)
    except urllib.error.HTTPError:
        continue
    except Exception as e:
        print('error', z, e); continue
    p = d['places'][0]
    if p['state abbreviation'] != st:
        continue
    lat, lng = float(p['latitude']), float(p['longitude'])
    a, b, c, e = BOX[st]
    if a <= lat <= b and c <= lng <= e:
        zips[z] = [round(lat, 4), round(lng, 4), p['place name']]
    time.sleep(0.08)

json.dump(zips, open('data/zips.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
print(len(zips), 'ZIP codes written to data/zips.json')
print(sorted(zips)[:60])
