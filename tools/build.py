#!/usr/bin/env python3
"""Build the deployable static site from the Claude Design source pages.

Usage: python3 tools/build.py [SOURCE_DIR] [OUT_DIR]
  SOURCE_DIR  folder with the *.dc.html pages, site.css, motion.js, cv/, logos/ (default: design-source)
  OUT_DIR     where the static site is written (default: repo root)
Optional env SITE_URL=https://example.com adds canonical links, og:url and sitemap.xml.
"""
import html, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'design-source'))
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else ROOT)
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')

# Published Claude Design blobs -> local files
BLOBS = {
    '58e3b5c19eeea79cc3b4d443bc5a20a7': 'assets/img/portrait.jpg',
    '5466f7faa9a4f8def5be3705b9cbad7a': 'assets/img/portrait-dots.png',
    '3f90143de3e4f9b11ac42614d757ed2d': 'assets/img/ember.jpg',
    'e5475fa57534c430364755ccaffa5714': 'assets/img/topography.svg',
    '9bcf0ee3201a4b125844915d68bdb52b': 'assets/img/world-dots.svg',
    'f7f37eb38bce1c4eab8e0bea5214dea4': 'cv/Saad-Al-Tamari-CV-AI-Specialist.pdf',
    'befad928a1065a524caf917c104e529f': 'cv/Saad-Al-Tamari-CV-AI-Trainer.pdf',
}
SKIP = {'Home-Mobile', 'Home-Tablet'}  # canvas-only device previews
SPECIAL = {'Main': 'index', 'Work': 'work', 'Services': 'services', 'About': 'about', 'Notes': 'writing'}
DEFAULT_DESC = ('Saad Tamari is an AI engineer in Amman who designs and ships AI products end to end: '
                'agents, the data underneath, and the app people actually use.')


def kebab(s):
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', s)
    s = re.sub(r'([A-Za-z])([0-9])', r'\1-\2', s)
    return s.lower()


def slug(stem):
    if stem in SPECIAL:
        return SPECIAL[stem]
    kind, _, rest = stem.partition('-')
    return ('case-' if kind == 'Case' else 'writing-') + kebab(rest)


def strip_tags(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def describe(page):
    body = page.split('<header', 1)[-1]
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', body, re.S):
        t = strip_tags(m.group(1))
        if len(t) > 70 and '{{' not in t:
            return (t[:157].rsplit(' ', 1)[0] + '…') if len(t) > 160 else t
    return DEFAULT_DESC


def rewrite_assets(s):
    # CV links built in component logic: origin + '/_blob/<id>' -> relative path
    s = re.sub(r"\(\(\) => \{ let o = ''; try \{ o = window\.location\.origin; \} catch \(e\) \{\} "
               r"return \(o && o !== 'null' \? o : ''\) \+ '/_blob/([0-9a-f]{32})'; \}\)\(\)",
               lambda m: "'" + BLOBS[m.group(1)] + "'", s)
    return re.sub(r'/_blob/([0-9a-f]{32})', lambda m: BLOBS[m.group(1)], s)


def main():
    pages = sorted(f[:-8] for f in os.listdir(SRC) if f.endswith('.dc.html') and f[:-8] not in SKIP)
    names = {p: slug(p) for p in pages}

    def links(s):
        return re.sub(r'\b([A-Za-z0-9-]+)\.dc\.html', lambda m: names.get(m.group(1), m.group(0)) + '.html'
                      if m.group(1) in names else m.group(0), s)

    os.makedirs(OUT, exist_ok=True)
    for d in ('cv', 'logos'):
        shutil.copytree(os.path.join(SRC, d), os.path.join(OUT, d), dirs_exist_ok=True)
    for f in ('site.css', 'motion.js'):
        s = open(os.path.join(SRC, f), encoding='utf-8').read()
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(links(rewrite_assets(s)))

    sitemap = []
    for p in pages:
        s = open(os.path.join(SRC, p + '.dc.html'), encoding='utf-8').read()
        s = links(rewrite_assets(s))
        title = strip_tags(re.search(r'<title>(.*?)</title>', s, re.S).group(1))
        desc = describe(s)
        out_name = names[p] + '.html'
        url = (SITE_URL + '/' + ('' if out_name == 'index.html' else out_name)) if SITE_URL else ''
        e = lambda t: html.escape(t, quote=True)
        head = [
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            f'<meta name="description" content="{e(desc)}">',
            '<meta name="author" content="Saad Tamari">',
            '<meta name="theme-color" content="#EFEDE7" media="(prefers-color-scheme: light)">',
            '<meta name="theme-color" content="#111110" media="(prefers-color-scheme: dark)">',
            '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
            '<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">',
            '<meta property="og:type" content="' + ('article' if p.startswith('Note-') else 'website') + '">',
            f'<meta property="og:title" content="{e(title)}">',
            f'<meta property="og:description" content="{e(desc)}">',
            '<meta property="og:image" content="' + ((SITE_URL + '/') if SITE_URL else '') + 'assets/img/og.jpg">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            '<style>x-dc{display:none}</style>',
        ]
        if url:
            head += [f'<link rel="canonical" href="{url}">', f'<meta property="og:url" content="{url}">']
            sitemap.append(url)
        s = s.replace('<script src="./support.js"></script>',
                      '\n'.join(head) + '\n<script src="./dc-runtime.js"></script>', 1)
        open(os.path.join(OUT, out_name), 'w', encoding='utf-8').write(s)
        print(f'{p + ".dc.html":34} -> {out_name}')

    open(os.path.join(OUT, 'robots.txt'), 'w').write(
        'User-agent: *\nAllow: /\n' + (f'Sitemap: {SITE_URL}/sitemap.xml\n' if SITE_URL else ''))
    if sitemap:
        xml = ''.join(f'  <url><loc>{u}</loc></url>\n' for u in sitemap)
        open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + xml + '</urlset>\n')
    json.dump(names, open(os.path.join(HERE, 'page-map.json'), 'w'), indent=2)


if __name__ == '__main__':
    main()
