#!/usr/bin/env python3
"""Build the deployable site (public/) from the design source pages.

  python3 tools/build.py            # writes public/
  node tools/prerender.cjs          # bakes the rendered HTML into every page + llms-full.txt

Env: SITE_URL (default https://saadaltamari.com)
"""
import datetime, html, json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'design-source')
STATIC = os.path.join(ROOT, 'static')        # hand-written files copied as they are
OUT = os.path.join(ROOT, 'public')
SITE = os.environ.get('SITE_URL', 'https://saadaltamari.com').rstrip('/')
TODAY = datetime.date.today().isoformat()
PUBLISHED = '2026-10-25'                      # first public launch of the site

BLOBS = {
    '58e3b5c19eeea79cc3b4d443bc5a20a7': 'assets/img/portrait.jpg',
    '5466f7faa9a4f8def5be3705b9cbad7a': 'assets/img/portrait-dots.png',
    '3f90143de3e4f9b11ac42614d757ed2d': 'assets/img/ember.jpg',
    'e5475fa57534c430364755ccaffa5714': 'assets/img/topography.svg',
    '9bcf0ee3201a4b125844915d68bdb52b': 'assets/img/world-dots.svg',
    'f7f37eb38bce1c4eab8e0bea5214dea4': 'cv/Saad-Al-Tamari-CV-AI-Specialist.pdf',
    'befad928a1065a524caf917c104e529f': 'cv/Saad-Al-Tamari-CV-AI-Trainer.pdf',
}
SKIP = {'Home-Mobile', 'Home-Tablet'}
SPECIAL = {'Main': 'index', 'Work': 'work', 'Services': 'services', 'About': 'about', 'Notes': 'writing'}

PERSON_ID = SITE + '/#person'
WEBSITE_ID = SITE + '/#website'
PERSON = {
    '@type': 'Person', '@id': PERSON_ID,
    'name': 'Saad Tamari',
    'alternateName': ['Saad Al-Tamari', 'Saad Altamari', 'سعد الطماري'],
    'jobTitle': 'AI Engineer',
    'description': 'Full-stack AI engineer in Amman, Jordan. Designs and ships AI products end to end: '
                   'agents, RAG and context systems, MCP gateways, and the apps on top. Co-founder of SKAI Group.',
    'url': SITE + '/',
    'image': SITE + '/assets/img/portrait.jpg',
    'email': 'mailto:saadaltamari@gmail.com',
    'address': {'@type': 'PostalAddress', 'addressLocality': 'Amman', 'addressCountry': 'JO'},
    'alumniOf': {'@type': 'CollegeOrUniversity', 'name': 'Yarmouk University'},
    'worksFor': {'@type': 'Organization', 'name': 'SKAI Group', 'url': 'https://skaigroup.tech'},
    'knowsLanguage': ['ar', 'en'],
    'knowsAbout': ['AI engineering', 'AI agents', 'Agent orchestration', 'Retrieval-augmented generation',
                   'RAG evaluation', 'Context engineering', 'Model Context Protocol (MCP)', 'Claude Code',
                   'Python', 'TypeScript', 'Full-stack web development', 'AI training and workshops'],
    'sameAs': ['https://www.linkedin.com/in/saad-altamari/', 'https://github.com/Saadtamari',
               'https://www.upwork.com/freelancers/saadaltamari'],
}


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


def path_of(name):                       # clean URL path for a page file name
    return '/' if name == 'index' else '/' + name


def strip_tags(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def clip(t, n=158):
    t = re.sub(r'\s+([.,:;!?])', r'\1', t)
    return t if len(t) <= n else t[:n - 1].rsplit(' ', 1)[0].rstrip(',;:') + '…'


def describe(page):
    body = page.split('<header', 1)[-1]
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', body, re.S):
        t = strip_tags(m.group(1))
        if len(t) > 70 and '{{' not in t:
            return clip(t)
    return clip(PERSON['description'])


def rewrite_assets(s):
    s = re.sub(r"\(\(\) => \{ let o = ''; try \{ o = window\.location\.origin; \} catch \(e\) \{\} "
               r"return \(o && o !== 'null' \? o : ''\) \+ '/_blob/([0-9a-f]{32})'; \}\)\(\)",
               lambda m: "'/" + BLOBS[m.group(1)] + "'", s)
    return re.sub(r'/_blob/([0-9a-f]{32})', lambda m: '/' + BLOBS[m.group(1)], s)


# Page descriptions written by hand where the first paragraph isn't a good summary.
DESC = {
    'index': 'Saad Tamari, AI engineer in Amman. I design and ship AI products end to end: the agents, '
             'the data underneath, and the app people use. 20+ projects shipped.',
    'work': 'Selected work by Saad Tamari: 11 case studies across agent platforms, MCP gateways, '
            'context engines, Arabic AI products and full-stack apps.',
    'services': 'Hire Saad Tamari, AI engineer: full-time, part-time or contract roles, AI product builds, '
                'agent and RAG systems, and hands-on AI workshops for teams.',
    'about': 'About Saad Tamari: AI engineer and co-founder of SKAI Group in Amman, Jordan. '
             'How I build, the tools I use, and 15+ competition wins.',
    'writing': 'Field guides and build notes by Saad Tamari on RAG, agent orchestration, evaluation, '
               'context engineering, MCP gateways and AGI benchmarks.',
}


TITLES = {
    'index': 'Saad Tamari · Full-Stack AI Engineer in Amman, Jordan',
    'about': 'About Saad Tamari · AI Engineer and SKAI Group co-founder',
    'work': 'Work · 11 AI case studies by Saad Tamari',
    'services': 'Hire an AI Engineer · Services by Saad Tamari',
    'writing': 'Writing on RAG, agents and AI evaluation · Saad Tamari',
}


def seo_title(name, title):
    if name in TITLES:
        return TITLES[name]
    if name.startswith('case-'):
        return title.split(' · ')[0] + ' · AI case study by Saad Tamari'
    return title if len(title) <= 62 else title.rsplit(' · ', 1)[0]


def ld(obj):
    return ('<script type="application/ld+json">' +
            json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>')


def crumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + p} for i, (n, p) in enumerate(items)]}


def main():
    pages = sorted(f[:-8] for f in os.listdir(SRC) if f.endswith('.dc.html') and f[:-8] not in SKIP)
    names = {p: slug(p) for p in pages}
    notes = json.load(open(os.path.join(HERE, 'notes-index.json'), encoding='utf-8'))
    note_meta = {n['f'][:-8]: n for n in notes}

    def links(s):
        return re.sub(r'(?<![\w/.-])([A-Za-z0-9-]+)\.dc\.html',
                      lambda m: path_of(names[m.group(1)]) if m.group(1) in names else m.group(0), s)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(STATIC, OUT, dirs_exist_ok=True)
    for d in ('cv', 'logos'):
        shutil.copytree(os.path.join(SRC, d), os.path.join(OUT, d))
    for f in ('site.css', 'motion.js'):
        s = open(os.path.join(SRC, f), encoding='utf-8').read()
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(links(rewrite_assets(s)))

    info = {}
    for p in pages:
        s = open(os.path.join(SRC, p + '.dc.html'), encoding='utf-8').read()
        s = links(rewrite_assets(s))
        name = names[p]
        title = strip_tags(re.search(r'<title>(.*?)</title>', s, re.S).group(1))
        if p.startswith('Note-'):
            title = title.replace('Saad Al-Tamari', 'Saad Tamari')
        desc = DESC.get(name) or describe(s)
        url = SITE + path_of(name)
        og_img = SITE + ('/assets/og/' + name + '.jpg' if os.path.exists(os.path.join(STATIC, 'assets/og', name + '.jpg'))
                         else '/assets/img/og.jpg')
        title = seo_title(name, title)
        s = re.sub(r'<title>.*?</title>', '<title>' + html.escape(title, quote=False) + '</title>', s, count=1, flags=re.S)
        info[name] = {'stem': p, 'title': title, 'desc': desc, 'url': url, 'img': og_img}

        # ---------- structured data ----------
        graph = []
        if name == 'index':
            graph += [PERSON, {'@type': 'WebSite', '@id': WEBSITE_ID, 'url': SITE + '/', 'name': 'Saad Tamari',
                               'description': desc, 'inLanguage': 'en', 'publisher': {'@id': PERSON_ID}},
                      {'@type': 'ProfilePage', '@id': url + '#page', 'url': url, 'name': title,
                       'isPartOf': {'@id': WEBSITE_ID}, 'mainEntity': {'@id': PERSON_ID}}]
        elif name == 'about':
            graph += [{'@type': 'ProfilePage', '@id': url + '#page', 'url': url, 'name': title, 'description': desc,
                       'isPartOf': {'@id': WEBSITE_ID}, 'mainEntity': PERSON},
                      crumbs([('Home', '/'), ('About', '/about')])]
        elif name == 'services':
            svc = ['AI product engineering (full-time, part-time or contract)', 'AI agents and orchestration',
                   'MCP gateways and tool integrations', 'RAG and context engineering', 'AI workshops for teams']
            graph += [{'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title, 'description': desc,
                       'isPartOf': {'@id': WEBSITE_ID}, 'about': {'@id': PERSON_ID}},
                      {'@type': 'Person', '@id': PERSON_ID, 'makesOffer': [
                          {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': n, 'provider': {'@id': PERSON_ID},
                                                             'areaServed': 'Worldwide (remote) and Amman, Jordan'}}
                          for n in svc]},
                      crumbs([('Home', '/'), ('Services', '/services')])]
        elif name in ('work', 'writing'):
            kids = [n for n in names.values() if n.startswith('case-' if name == 'work' else 'writing-')]
            graph += [{'@type': 'CollectionPage', '@id': url + '#page', 'url': url, 'name': title, 'description': desc,
                       'isPartOf': {'@id': WEBSITE_ID}, 'author': {'@id': PERSON_ID},
                       'mainEntity': {'@type': 'ItemList', 'itemListElement': [
                           {'@type': 'ListItem', 'position': i + 1, 'url': SITE + path_of(k)} for i, k in enumerate(sorted(kids))]}},
                      crumbs([('Home', '/'), (name.title(), '/' + name)])]
        elif p.startswith('Note-'):
            m = note_meta.get(p, {})
            head = m.get('title') or title.split(' · ')[0]
            art = {'@type': 'TechArticle' if m.get('kind') == 'Field guide' else 'BlogPosting',
                   '@id': url + '#article', 'headline': head, 'description': desc, 'url': url,
                   'mainEntityOfPage': url, 'author': {'@id': PERSON_ID}, 'publisher': {'@id': PERSON_ID},
                   'datePublished': PUBLISHED, 'dateModified': TODAY, 'inLanguage': 'en',
                   'image': og_img, 'isPartOf': {'@id': WEBSITE_ID}}
            if m.get('kind'):
                art['articleSection'] = m['kind']
            if m.get('mins'):
                art['timeRequired'] = 'PT' + re.sub(r'\D', '', m['mins']) + 'M'
            graph += [art, crumbs([('Home', '/'), ('Writing', '/writing'), (head, '/' + name)])]
        elif p.startswith('Case-'):
            head = title.split(' · ')[0]
            graph += [{'@type': 'CreativeWork', '@id': url + '#work', 'name': head, 'headline': title,
                       'description': desc, 'url': url, 'creator': {'@id': PERSON_ID}, 'author': {'@id': PERSON_ID},
                       'genre': 'Case study', 'inLanguage': 'en', 'isPartOf': {'@id': WEBSITE_ID}},
                      crumbs([('Home', '/'), ('Work', '/work'), (head, '/' + name)])]
        info[name]['graph'] = graph

        e = lambda t: html.escape(t, quote=True)
        og_type = 'article' if p.startswith('Note-') else ('profile' if name in ('index', 'about') else 'website')
        head = [
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            f'<meta name="description" content="{e(desc)}">',
            '<meta name="author" content="Saad Tamari">',
            '<meta name="msvalidate.01" content="DAE7C7DDD865BD4352E0B73989D57F77">',
            '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">',
            f'<link rel="canonical" href="{url}">',
            '<meta name="theme-color" content="#EFEDE7" media="(prefers-color-scheme: light)">',
            '<meta name="theme-color" content="#111110" media="(prefers-color-scheme: dark)">',
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
            '<link rel="icon" href="/favicon.ico" sizes="32x32">',
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
            '<link rel="manifest" href="/site.webmanifest">',
            '<link rel="alternate" type="text/plain" title="LLM summary" href="/llms.txt">',
            '<link rel="alternate" type="application/atom+xml" title="Saad Tamari · Writing" href="/feed.xml">',
            f'<link rel="alternate" hreflang="en" href="{url}">',
            f'<link rel="alternate" hreflang="x-default" href="{url}">',
            f'<meta property="og:type" content="{og_type}">',
            '<meta property="og:site_name" content="Saad Tamari">',
            '<meta property="og:locale" content="en_US">',
            f'<meta property="og:title" content="{e(title)}">',
            f'<meta property="og:description" content="{e(desc)}">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:image" content="{og_img}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            f'<meta property="og:image:alt" content="{e(title)}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{e(title)}">',
            f'<meta name="twitter:description" content="{e(desc)}">',
            f'<meta name="twitter:image" content="{og_img}">',
            f'<meta name="twitter:image:alt" content="{e(title)}">',
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            # Prerendered HTML (#ssr) is for crawlers and no-JS readers; the live components replace it.
            '<script>document.documentElement.classList.add("ssr-js")</script>',
            '<style>x-dc{display:none}.ssr-js #ssr{display:none}</style>',
        ]
        if p.startswith('Note-'):
            head += [f'<meta property="article:published_time" content="{PUBLISHED}">',
                     '<meta property="article:author" content="Saad Tamari">']
        if graph:
            head.append(ld({'@context': 'https://schema.org', '@graph': graph}))
        s = s.replace('<script src="./support.js"></script>', '\n'.join(head) + '\n<script src="/dc-runtime.js"></script>', 1)
        s = s.replace('href="./site.css"', 'href="/site.css"').replace('src="./motion.js"', 'src="/motion.js"')
        s = s.replace('<html lang="en">', '<html lang="en" dir="ltr">', 1)

        # Keep the component template out of the readable HTML: it lives in a script tag and is
        # turned back into <x-dc> before the runtime boots (DOMContentLoaded).
        a, b = s.index('<x-dc>'), s.index('</x-dc>') + len('</x-dc>')
        tpl = s[a:b]
        assert '</script' not in tpl.lower()
        boot = ('<script>(function(){var t=document.getElementById("dc-tpl"),d=document.createElement("div");'
                'd.innerHTML=t.textContent.replace(/ d="\\{\\{menuPath\\}\\}"/g," d=\\"M0 0\\"");t.replaceWith(d.firstElementChild);'
                'var r=document.documentElement,o=new MutationObserver(function(){var m=document.getElementById("dc-root");'
                'if(m&&m.childElementCount){var x=document.getElementById("ssr");x&&x.remove();o.disconnect();}});'
                'o.observe(document.body,{childList:true,subtree:true});'
                'setTimeout(function(){if(!document.getElementById("dc-root"))r.classList.remove("ssr-js");},5000);})();</script>')
        s = s[:a] + '<!--SSR-->\n<script type="text/x-dc-template" id="dc-tpl">' + tpl + '</script>\n' + boot + s[b:]
        open(os.path.join(OUT, name + '.html'), 'w', encoding='utf-8').write(s)

    # ---------- crawl files ----------
    order = ['index', 'work', 'services', 'about', 'writing'] + sorted(n for n in info if n.startswith('case-')) + \
            sorted(n for n in info if n.startswith('writing-'))
    pri = lambda n: '1.0' if n == 'index' else ('0.8' if n in ('work', 'services', 'about', 'writing') else '0.6')
    def imgs(n):
        out = [info[n]['img']] + ([SITE + '/assets/img/portrait.jpg'] if n in ('index', 'about') else [])
        return ''.join(f'<image:image><image:loc>{u}</image:loc></image:image>' for u in out)
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
        ''.join(f'  <url><loc>{info[n]["url"]}</loc><lastmod>{TODAY}</lastmod><priority>{pri(n)}</priority>{imgs(n)}</url>\n'
                for n in order) + '</urlset>\n')

    # Atom feed for the writing
    X = lambda t: html.escape(t, quote=True)
    posts = [n for n in order if n.startswith('writing-')]
    feed = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">',
            '  <title>Saad Tamari · Writing</title>',
            '  <subtitle>Field guides and build notes on RAG, agents, evaluation and AI infrastructure.</subtitle>',
            f'  <link href="{SITE}/writing"/>', f'  <link rel="self" href="{SITE}/feed.xml"/>',
            f'  <id>{SITE}/writing</id>', f'  <updated>{TODAY}T00:00:00Z</updated>',
            f'  <author><name>Saad Tamari</name><uri>{SITE}/</uri></author>', f'  <icon>{SITE}/favicon.svg</icon>']
    for n in posts:
        i = info[n]; head = i['title'].rsplit(' · Saad Tamari', 1)[0]
        feed += ['  <entry>', f'    <title>{X(head)}</title>', f'    <link href="{i["url"]}"/>', f'    <id>{i["url"]}</id>',
                 f'    <published>{PUBLISHED}T00:00:00Z</published>', f'    <updated>{TODAY}T00:00:00Z</updated>',
                 f'    <summary>{X(i["desc"])}</summary>', '  </entry>']
    feed.append('</feed>')
    open(os.path.join(OUT, 'feed.xml'), 'w', encoding='utf-8').write('\n'.join(feed) + '\n')

    bots = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User',
            'anthropic-ai', 'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'Googlebot', 'Bingbot',
            'Applebot', 'Applebot-Extended', 'DuckAssistBot', 'meta-externalagent', 'Amazonbot',
            'MistralAI-User', 'cohere-ai', 'CCBot']
    open(os.path.join(OUT, 'robots.txt'), 'w').write(
        '# saadaltamari.com: everything here is public and may be crawled, indexed and quoted.\n\n'
        'User-agent: *\nAllow: /\n\n' + ''.join(f'User-agent: {b}\n' for b in bots) + 'Allow: /\n\n'
        f'Sitemap: {SITE}/sitemap.xml\n')

    llms = open(os.path.join(HERE, 'llms-head.md'), encoding='utf-8').read().strip() + '\n'
    sect = [('Main pages', ['index', 'work', 'services', 'about', 'writing']),
            ('Case studies', [n for n in order if n.startswith('case-')]),
            ('Writing', [n for n in order if n.startswith('writing-')])]
    for h, ns in sect:
        llms += f'\n## {h}\n\n' + ''.join(
            f'- [{info[n]["title"].split(" · ")[0] if n != "index" else "Home"}]({info[n]["url"]}): {info[n]["desc"]}\n'
            for n in ns)
    llms += (f'\n## Optional\n\n- [Full text of every page]({SITE}/llms-full.txt): all pages as plain Markdown\n'
             f'- [Writing feed (Atom)]({SITE}/feed.xml)\n'
             f'- [CV, AI Specialist (PDF)]({SITE}/cv/Saad-Al-Tamari-CV-AI-Specialist.pdf)\n'
             f'- [CV, AI Trainer (PDF)]({SITE}/cv/Saad-Al-Tamari-CV-AI-Trainer.pdf)\n')
    open(os.path.join(OUT, 'llms.txt'), 'w', encoding='utf-8').write(llms)
    json.dump({n: {k: v for k, v in i.items() if k != 'graph'} for n, i in info.items()},
              open(os.path.join(HERE, 'pages.json'), 'w'), indent=2, ensure_ascii=False)
    print(f'built {len(info)} pages -> {OUT}')


if __name__ == '__main__':
    main()
