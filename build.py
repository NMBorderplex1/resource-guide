"""One entry point for the whole data + widget pipeline.

  python build.py                         rebuild dist/ from the committed data (no PDFs needed)
  python build.py data                    regenerate data/widget_data.json from the committed extracts (no PDFs needed), then rebuild dist/
  python build.py all --en EN.pdf --es ES.pdf
                                          re-extract both PDFs first (steps 1-2), then everything above

Steps run by "all" (each is a script in scripts/ and works from the repo root):
  1 extract_from_pdf.py  EN.pdf -> data/en_pdf.json         (font-signature parser for the English guide)
  2 extract_es.py        ES.pdf -> data/es_pdf.json         (same parser, Spanish headers)
  3 rebuild_from_pdf.py                                     (PDF entries + industry incentives + carried-over descriptions
                                                             + artifact cleanups -> data/widget_data_from_pdf.json)
  4 apply_locations.py                                      (multi-location research in data/multiloc -> data/widget_data_en.json)
  5 build_bilingual.py                                      (attach Spanish -> data/widget_data.json)
  6 build_widget.py                                         (-> dist/)
"""
import argparse, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(*args):
    print('>', os.path.basename(args[0]), *args[1:])
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    subprocess.run([PY, os.path.join('scripts', args[0]), *args[1:]], cwd=ROOT, check=True, env=env)


ap = argparse.ArgumentParser()
ap.add_argument('step', nargs='?', default='widget', choices=['widget', 'data', 'all'])
ap.add_argument('--en', help='path to the English print PDF (TRIM)')
ap.add_argument('--es', help='path to the Spanish print PDF (TRIM)')
a = ap.parse_args()

if a.step == 'all':
    if not (a.en and a.es):
        ap.error('"all" needs --en and --es')
    run('extract_from_pdf.py', a.en, 'data/en_pdf.json')
    run('extract_es.py', a.es, 'data/es_pdf.json')
if a.step in ('all', 'data'):
    run('rebuild_from_pdf.py')
    run('apply_locations.py')
    run('build_bilingual.py')
run('build_widget.py')
