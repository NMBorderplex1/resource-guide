"""Build the interactive widget from src/widget.html + src/assets + data/widget_data.json.

Writes:
  dist/business-resource-finder.html              full page (what is published as a Claude artifact)
  dist/business-resource-finder-DIVI-EMBED.html   same file minus <meta>/<title>, for a Divi Code module
  docs/index.html                                 the page GitHub Pages serves (embed it in Divi with an iframe)
Run from the repository root:  python scripts/build_widget.py
"""
import base64, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'src', 'assets')


def b64(name):
    return base64.b64encode(open(os.path.join(A, name), 'rb').read()).decode()


html = open(os.path.join(ROOT, 'src', 'widget.html'), encoding='utf-8').read()
for key, asset in [('__BANNER_B64__', 'hero-banner.jpg'), ('__NMB_B64__', 'logo-nmborderplex.png'),
                   ('__PB_B64__', 'logo-powered-by-mveda.png'), ('__MV_B64__', 'logo-mveda.png')]:
    html = html.replace(key, b64(asset))
for i in range(1, 6):
    html = html.replace(f'__B{i}__', b64(f'section-{i}.jpg'))

data = json.load(open(os.path.join(ROOT, 'data', 'widget_data.json'), encoding='utf-8'))
payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
head, tail = html.split('__DATA_JSON__')
out = head + payload + tail
assert not re.findall(r'__[A-Z0-9_]+__', out), 'unreplaced placeholder'

os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
open(os.path.join(ROOT, 'dist', 'business-resource-finder.html'), 'w', encoding='utf-8', newline='').write(out)
embed = out.replace('<meta charset="utf-8">\n', '', 1).replace('<title>Business Resource Finder</title>\n', '', 1)
open(os.path.join(ROOT, 'dist', 'business-resource-finder-DIVI-EMBED.html'), 'w', encoding='utf-8', newline='').write(embed)
os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
page = '<!doctype html>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<style>html,body{margin:0;background:transparent}</style>\n' + out
open(os.path.join(ROOT, 'docs', 'index.html'), 'w', encoding='utf-8', newline='').write(page)
open(os.path.join(ROOT, 'docs', '.nojekyll'), 'w').close()
n = sum(len(h2['entries']) for h1 in data for h2 in h1['subsections'])
print(f'built dist/ ({len(out):,} bytes, {n} entries)')
