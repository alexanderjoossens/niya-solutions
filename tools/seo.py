#!/usr/bin/env python3
"""SEO pass over the built pages (runs at the end of build.py, safe to run again on its own).

- canonical, og:url and all absolute self-links end in '/' (the URL GitHub Pages serves;
  /page without slash 301-redirects there, so old Webhero links keep working)
- one clean JSON-LD graph per page: business, website, webpage, breadcrumb, service
  (replaces the Webhero blocks: relative @id's, a NewsArticle with an author page that
  does not exist, a single-item breadcrumb)
- og:locale nl_BE, og:site_name, a real 1200x630 og:image, Twitter card
- noindex on helper pages that are not meant to rank (search, embedded form/blocks, 404)
- own description / title where the old site had a duplicate or a too thin one
- alt attribute on every image, h1 on the pages that had none

Usage: python3 tools/seo.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = 'https://www.niya-solutions.be'
ORG_ID = DOMAIN + '/#organization'
SITE_ID = DOMAIN + '/#website'
LOGO = DOMAIN + '/assets/img/efea26091411.png'
OG_IMAGE = 'assets/img/og-niya-solutions.jpg'
OG_SOURCE = 'assets/img/069ea05a38ba.jpg'

FAMILIES = ['facilitair-bedrijf', 'facility-manager', 'industriele-schoonmaak', 'kuisbedrijf', 'poetsbedrijf',
            'poetshulp', 'projectcoordinator', 'schoonmaakbedrijf', 'schoonmaker-kantoren']

NOINDEX = {'search/', 'contact/contactformulier-homepage/', 'onze-diensten-homepage/', '404'}

TITLES = {
    '': 'Niya Solutions | Facility management, schoonmaak en kluswerken',
    'klusbedrijf/': 'Klusbedrijf voor herstellingen en afwerking | Niya Solutions',
    'offerte/': 'Vrijblijvende offerte aanvragen | Niya Solutions',
    'contact/': 'Contact | Niya Solutions, Sint-Niklaas',
}

DESCRIPTIONS = {
    'privacy/': 'Lees hoe Niya Solutions omgaat met je persoonsgegevens en welke cookies de website gebruikt.',
    'disclaimer/': 'De algemene voorwaarden van Niya Solutions voor facility management, projectbeheer, schoonmaak en kluswerken.',
    'sitemap/': 'Overzicht van alle pagina\'s op de website van Niya Solutions: diensten, regio\'s, offertes en contact.',
    'search/': 'Zoek op de website van Niya Solutions.',
    'contact/contactformulier/': 'Neem contact op met Niya Solutions. Vraag een vrijblijvende offerte aan of stel je vragen over facility management, schoonmaak of kluswerken.',
    'dit-maakt-ons-uniek/': 'Ontdek wat Niya Solutions uniek maakt: één vast aanspreekpunt voor facility management, projectbeheer, schoonmaak en kluswerken.',
    'offerte/': 'Vraag een vrijblijvende offerte aan bij Niya Solutions voor facility management, projectmanagement, schoonmaak of kluswerken.',
    'ai-info/': 'Officiële informatie over Niya Solutions voor AI-assistenten: diensten, werkgebied en contactgegevens.',
}


def esc(s):
    return html.escape(s, quote=True)


def page_paths():
    for d, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(d, ROOT)
        if rel.split(os.sep)[0] in ('tools', 'assets', '.git', '.playwright-mcp'):
            dirs[:] = []
            continue
        if 'index.html' in files:
            yield '' if rel == '.' else rel.replace(os.sep, '/') + '/'


def title_of(h):
    return html.unescape(re.search(r'<title>(.*?)</title>', h, flags=re.S).group(1)).strip()


def short(title):
    return title.split(' | ')[0].strip()


def make_og_image():
    dest = os.path.join(ROOT, OG_IMAGE)
    if os.path.exists(dest):
        return
    os.system('sips -s format jpeg -s formatOptions 80 --resampleWidth 1200 "%s" --out "%s" >/dev/null && '
              'sips --cropToHeightWidth 630 1200 "%s" >/dev/null' % (os.path.join(ROOT, OG_SOURCE), dest, dest))


def breadcrumb(path, titles):
    """Home > (service hub for a city page | parent folder) > page."""
    items = [('Home', DOMAIN + '/')]
    if path:
        parts = path.strip('/').split('/')
        parents = ['/'.join(parts[:i]) + '/' for i in range(1, len(parts))]
        if len(parts) == 1:
            fam = next((f for f in FAMILIES if parts[0].startswith(f + '-')), None)
            if fam and fam + '/' in titles:
                parents = [fam + '/']
        for p in parents:
            if p in titles:
                items.append((titles[p], DOMAIN + '/' + p))
        items.append((titles[path], DOMAIN + '/' + path))
    return {'@type': 'BreadcrumbList', '@id': DOMAIN + '/' + path + '#breadcrumb',
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
                                for i, (n, u) in enumerate(items)]}


def area_served(path, name):
    slug = path.strip('/')
    fam = next((f for f in FAMILIES if slug.startswith(f + '-')), None)
    if not fam:
        return {'@type': 'Country', 'name': 'België'}
    city = slug[len(fam) + 1:]
    m = re.search(re.sub(r'-', '[- ]', re.escape(city).replace('\\-', '-')) + r'$', name, flags=re.I)
    place = m.group(0) if m else city.replace('-', ' ').title()
    kind = 'AdministrativeArea' if 'vlaanderen' in city or city in ('limburg', 'antwerpen-provincie') else 'City'
    return {'@type': kind, 'name': place}


def organization(description):
    return {
        '@type': 'ProfessionalService', '@id': ORG_ID, 'name': 'Niya Solutions', 'url': DOMAIN + '/',
        'logo': {'@type': 'ImageObject', 'url': LOGO}, 'image': DOMAIN + '/' + OG_IMAGE,
        'description': description, 'email': 'info@niya-solutions.be', 'vatID': 'BE0830139163',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Vrasenestraat 14', 'postalCode': '9100',
                    'addressLocality': 'Sint-Niklaas', 'addressCountry': 'BE'},
        'areaServed': {'@type': 'Country', 'name': 'België'},
        'knowsAbout': ['Facility management', 'Projectmanagement', 'Schoonmaak', 'Kantoorschoonmaak',
                       'Industriële schoonmaak', 'Kluswerken'],
    }


def process(path, titles, org_desc):
    fn = os.path.join(ROOT, path, 'index.html') if path != '404' else os.path.join(ROOT, '404.html')
    h = open(fn, encoding='utf-8').read()
    url = DOMAIN + '/' + (path if path != '404' else '')
    head_end = h.find('</head>')
    head, body = h[:head_end], h[head_end:]

    # --- title / description
    title = TITLES.get(path, title_of(h))
    head = re.sub(r'<title>.*?</title>', '<title>%s</title>' % esc(title), head, count=1, flags=re.S)
    desc = DESCRIPTIONS.get(path)
    if desc:
        if 'name="description"' in head:
            head = re.sub(r'((?:name="description"|property="og:description") content=")[^"]*"', lambda m: m.group(1) + esc(desc) + '"', head)
        else:
            head = head.replace('<meta name="format-detection"',
                                '<meta id="description" name="description" content="%s"/>\n    <meta name="format-detection"' % esc(desc), 1)
    m = re.search(r'name="description" content="([^"]*)"', head)
    desc = html.unescape(m.group(1)) if m else ''

    # --- clean up Webhero leftovers
    head = re.sub(r'\s*<meta name="keywords" content=""\s*/?>', '', head)
    head = re.sub(r'\s*<meta http-equiv="last-modified"[^>]*>', '', head)
    head = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)
    head = re.sub(r'\s*<meta name="(robots|twitter:[a-z]+)"[^>]*>', '', head)
    head = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', '', head)
    head = head.replace('type="image/x-icon"', 'type="image/png"')

    # --- canonical + Open Graph
    noindex = path in NOINDEX
    head = re.sub(r'\s*<link rel="canonical"[^>]*>', '', head)
    if not noindex:
        head = head.replace('<meta name="format-detection" content="telephone=no">',
                            '<meta name="format-detection" content="telephone=no">\n    <link rel="canonical" href="%s">' % url, 1)
    robots = 'noindex, follow' if noindex else 'index, follow, max-image-preview:large, max-snippet:-1'
    head = head.replace('<meta name="viewport"', '<meta name="robots" content="%s">\n    <meta name="viewport"' % robots, 1)
    head = re.sub(r'(<meta property="og:url" content=")[^"]*"', r'\g<1>%s"' % url, head)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*"', lambda m: m.group(1) + esc(title) + '"', head)
    head = re.sub(r'(<meta property="og:site_name" content=")[^"]*"', r'\1Niya Solutions"', head)
    head = head.replace('content="nl_NL"', 'content="nl_BE"')
    head = re.sub(r'(<meta property="og:image" content=")[^"]*"', r'\g<1>%s/%s"' % (DOMAIN, OG_IMAGE), head)
    head = re.sub(r'(<meta property="og:image:width" content=")[^"]*"', r'\g<1>1200"', head)
    head = re.sub(r'(<meta property="og:image:height" content=")[^"]*"', r'\g<1>630"', head)
    if 'og:image:alt' not in head:
        head = re.sub(r'(<meta property="og:image:height"[^>]*>)', r'\1\n    <meta property="og:image:alt" content="Niya Solutions">', head)
    favicon = re.search(r'<link[^>]*rel="icon"[^>]*href="([^"]+)"', head).group(1)
    head = re.sub(r'(<link[^>]*rel="icon"[^>]*>)',
                  r'\1\n    <link rel="apple-touch-icon" href="%s">' % favicon.replace('5e9bdd4b3268', 'efea26091411'), head, count=1)
    head = re.sub(r'(<meta property="og:image:alt"[^>]*>)', r'\1\n    <meta name="twitter:card" content="summary_large_image">', head)

    # --- structured data
    graph = [organization(org_desc)]
    if path == '':
        graph.append({'@type': 'WebSite', '@id': SITE_ID, 'url': DOMAIN + '/', 'name': 'Niya Solutions',
                      'inLanguage': 'nl-BE', 'publisher': {'@id': ORG_ID}})
    if not noindex:
        page = {'@type': 'WebPage', '@id': url + '#webpage', 'url': url, 'name': title, 'description': desc,
                'inLanguage': 'nl-BE', 'isPartOf': {'@id': SITE_ID}, 'about': {'@id': ORG_ID},
                'primaryImageOfPage': {'@type': 'ImageObject', 'url': DOMAIN + '/' + OG_IMAGE}}
        if path:
            page['breadcrumb'] = {'@id': url + '#breadcrumb'}
            graph.append(breadcrumb(path, titles))
        graph.append(page)
        if SERVICE.get(path):
            name = short(title)
            graph.append({'@type': 'Service', '@id': url + '#service', 'name': name, 'serviceType': SERVICE[path],
                          'description': desc, 'url': url, 'provider': {'@id': ORG_ID},
                          'areaServed': area_served(path, name)})
    ld = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=1)
    head = head.rstrip() + '\n    <script type="application/ld+json">\n%s\n    </script>\n' % ld.replace('</', '<\\/')

    # --- body: absolute self-links (share buttons) end in '/'
    body = re.sub(r'(https://www\.niya-solutions\.be)(/[a-z0-9\-/]*)?(?=["&<\s])',
                  lambda m: m.group(1) + ((m.group(2) or '/').rstrip('/') + '/'), body)
    # images: every <img> gets an alt (decorative icons empty, photos the page subject)
    subject = short(title)

    def alt(m):
        tag = m.group(0)
        if re.search(r'\salt=', tag):
            return tag
        photo = re.search(r'src="[^"]+\.jpe?g"', tag) and not re.search(r'width:\s*\d+px', tag)
        return tag[:4] + ' alt="%s"' % (esc(subject) if photo else '') + tag[4:]
    body = re.sub(r'<img\b[^>]*>', alt, body)
    # pages that had no h1 (form pages): the first heading of the content becomes the h1
    if '<h1' not in body:
        body = re.sub(r'<h2>(.*?)</h2>', r'<h1 class="seo-h1">\1</h1>', body, count=1, flags=re.S)

    open(fn, 'w', encoding='utf-8').write(head + body)


def write_sitemap(paths):
    urls = ''.join('  <url><loc>%s/%s</loc></url>\n' % (DOMAIN, p) for p in sorted(paths) if p not in NOINDEX)
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n')


SERVICE = {}


def main():
    make_og_image()
    paths = sorted(page_paths())
    titles = {}
    for p in paths:
        h = open(os.path.join(ROOT, p, 'index.html'), encoding='utf-8').read()
        # breadcrumb name: the visible page title (h1), else the <title> without the brand
        h1 = re.search(r'<h1\b(?![^>]*seo-h1)[^>]*>(.*?)</h1>', h, flags=re.S)
        titles[p] = html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else short(title_of(h))
        # pages the old site marked as a Service keep that, with the service category it used
        m = re.search(r'"@type":\s*"Service",\s*"name":\s*"([^"]+)"', h)
        if m:
            SERVICE[p] = m.group(1)
        elif p in SERVICE_DONE:
            SERVICE[p] = SERVICE_DONE[p]
    org_desc = ('Bij Niya Solutions zorgen we ervoor dat jouw bedrijf optimaal draait. Of het nu gaat om facility management, '
                'projectbeheer, schoonmaak of kluswerken, wij nemen het uit jouw handen. Met een persoonlijke aanpak en oog '
                'voor detail bieden we op maat gemaakte oplossingen voor bedrijven in heel België.')
    for p in paths:
        process(p, titles, org_desc)
    process('404', titles, org_desc)
    write_sitemap(paths)
    print('seo: %d pages, %d with Service schema' % (len(paths), len(SERVICE)))


SERVICE_DONE = {}
_cache = os.path.join(ROOT, 'tools', 'seo-services.json')
if os.path.exists(_cache):
    SERVICE_DONE = json.load(open(_cache, encoding='utf-8'))

if __name__ == '__main__':
    main()
    json.dump(SERVICE, open(_cache, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
