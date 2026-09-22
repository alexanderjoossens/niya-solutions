#!/usr/bin/env python3
"""Build the static Niya Solutions site from the pages mirrored from the old
Webhero site (tools/source/*.html).

- strips the Webhero/Vue/jQuery scripts and replaces them with assets/js/main.js
- downloads images, video, icons and fonts into assets/ and rewrites all URLs
- turns internal links into relative links (works on any host / subfolder)
- renders the Webhero form definitions (tools/forms.json) as static HTML forms

Usage: python3 tools/build.py
"""
import hashlib
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'tools', 'source')
FORMS = os.path.join(ROOT, 'tools', 'forms.json')
CACHE = os.path.join(ROOT, 'tools', 'cache')
DOMAIN = 'https://www.niya-solutions.be'

os.makedirs(CACHE, exist_ok=True)

# ---------------------------------------------------------------- downloads

def fetch(url, dest):
    """Download url to dest (cached)."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(['curl', '-sfL', '--retry', '3', '-A', 'Mozilla/5.0', url, '-o', dest])
    if r.returncode != 0:
        print('  !! download failed', url, file=sys.stderr)
        return None
    return dest


def ext_for(path):
    out = subprocess.run(['file', '-b', '--mime-type', path], capture_output=True, text=True).stdout.strip()
    return {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif',
            'image/svg+xml': '.svg', 'image/x-icon': '.ico', 'image/vnd.microsoft.icon': '.ico'}.get(out, '.jpg')


IMG_MAP = {}


def local_image(url):
    """Map a googleusercontent URL to a local asset path (relative to site root)."""
    base, _, params = url.partition('=')
    small = 'w450' in params  # logo / favicon
    key = base + ('#s' if small else '')
    if key in IMG_MAP:
        return IMG_MAP[key]
    size = '=w450' if small else '=w2000'
    h = hashlib.sha1(key.encode()).hexdigest()[:12]
    tmp = os.path.join(CACHE, h)
    if not fetch(base + size, tmp):
        IMG_MAP[key] = url
        return url
    name = h + ext_for(tmp)
    dest = os.path.join(ROOT, 'assets', 'img', name)
    if not os.path.exists(dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(tmp, 'rb') as a, open(dest, 'wb') as b:
            b.write(a.read())
    IMG_MAP[key] = 'assets/img/' + name
    return IMG_MAP[key]


# ---------------------------------------------------------------- pages


def slug_to_path(slug):
    """'index' -> '', 'contact__contactformulier' -> 'contact/contactformulier/'"""
    if slug == 'index':
        return ''
    return slug.replace('__', '/') + '/'


def rel_prefix(page_path):
    depth = page_path.count('/')
    return '../' * depth if depth else './'


def rewrite_internal(url, prefix):
    """Return a relative link for an internal URL, or None if external."""
    u = url
    if u.startswith(DOMAIN):
        u = u[len(DOMAIN):] or '/'
    elif u.startswith('http://www.niya-solutions.be'):
        u = u[len('http://www.niya-solutions.be'):] or '/'
    if not u.startswith('/') or u.startswith('//'):
        return None
    path, sep, frag = u.partition('#')
    path, qsep, query = path.partition('?')
    path = path.strip('/')
    target = (path + '/') if path else ''
    out = prefix + target if target else (prefix if prefix != './' else './')
    if qsep:
        out += '?' + query
    if sep:
        out += '#' + frag
    return out


def first_word(m):
    inner = m.group(2)
    text = re.sub(r'<[^>]+>', '', inner)
    text = html.unescape(text).strip()
    words = text.split(' ')
    if not words or not words[0]:
        return m.group(0)
    words[0] = '<span class="first-word">%s</span>' % html.escape(words[0], quote=False)
    rest = [html.escape(w, quote=False) for w in words[1:]]
    return m.group(1) + ' '.join([words[0]] + rest) + '</span>'


def find_block(h, start):
    """Given index of an opening <div, return end index after its matching </div>."""
    depth = 0
    for m in re.finditer(r'<div\b|</div>', h[start:]):
        if m.group().startswith('<div'):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return start + m.end()
    raise ValueError('unbalanced div')


def esc(s):
    return html.escape(str(s), quote=True)


def render_question(q):
    t = q['formtype']
    req = ' <span> *</span>' if q.get('required') else ''
    reqattr = ' data-required' if q.get('required') else ''
    label = esc(q['question'])
    qid = q['id']
    if t == 'form-type-0':
        email = ' data-email' if 'mail' in q['question'].lower() else ''
        low = q['question'].lower()
        extra = ' inputmode="email" autocomplete="email"' if email else (
            ' inputmode="tel" autocomplete="tel"' if 'telefoon' in low else (
            ' autocomplete="name"' if 'naam' in low else ''))
        return ('<div class="event_input-half"><label for="q%s">%s%s</label> '
                '<input type="text" data-sort="%s" id="q%s" name="q%s" placeholder="" aria-label="%s" data-question="%s"%s%s%s></div>'
                % (qid, label, req, q['sort'], qid, qid, label, label, reqattr, email, extra))
    if t == 'form-type-3':
        return ('<div class="event_input-half"><label for="q%s">%s%s</label> '
                '<textarea type="text" data-sort="%s" id="q%s" name="q%s" placeholder="" aria-label="%s" data-question="%s"%s></textarea></div>'
                % (qid, label, req, q['sort'], qid, qid, label, label, reqattr))
    if t == 'form-type-1':
        opts = ''.join('<div class="check-w"><input data-sort="%s" type="checkbox" name="o%s" id="o%s" value="%s"> '
                       '<label for="o%s" class="after-check">%s</label></div>'
                       % (q['sort'], o['id'], o['option_id'], esc(o['option']), o['option_id'], esc(o['option']))
                       for o in q['options'])
        return ('<div class="event_input-half"><label>%s%s</label> <div class="checks" data-question="%s"%s>%s</div></div>'
                % (label, req, label, reqattr, opts))
    if t == 'form-type-2':
        if len(q['options']) < 5:
            opts = ''.join('<div class="check-w"><input data-sort="%s" type="radio" name="r%s" id="o%s" value="%s"> '
                           '<label for="o%s" class="after-check">%s</label></div>'
                           % (q['sort'], qid, o['option_id'], esc(o['option']), o['option_id'], esc(o['option']))
                           for o in q['options'])
            return ('<div class="event_input-half"><div><label>%s%s</label> <div class="checks" data-question="%s"%s>%s</div></div></div>'
                    % (label, req, label, reqattr, opts))
        opts = ''.join('<option id="o%s" value="%s">%s</option>' % (o['option_id'], esc(o['option']), esc(o['option']))
                       for o in q['options'])
        return ('<div class="event_input-half"><div><label>%s%s</label> <div class="event__select__wrapper">'
                '<div class="event__select__icon"><i class="material-icons">arrow_drop_down</i></div>'
                '<select class="event__select" data-sort="%s" data-question="%s"%s aria-label="%s">'
                '<option selected disabled>Maak een keuze</option>%s</select></div></div></div>'
                % (label, req, q['sort'], label, reqattr, label, opts))
    if t == 'form-type-6':
        return '<div class="event_input-full"><h3 class="event_form_subtitle custom_font">%s</h3></div>' % label
    if t in ('form-type-4', 'form-type-5'):  # date / time
        itype = 'date' if t == 'form-type-4' else 'time'
        return ('<div class="event_input-half"><label for="q%s">%s%s</label> '
                '<input type="%s" data-sort="%s" id="q%s" name="q%s" aria-label="%s" data-question="%s"%s></div>'
                % (qid, label, req, itype, q['sort'], qid, qid, label, label, reqattr))
    raise ValueError('unknown form type %s' % t)


def render_form(block, event_id, name, prefix):
    form = FORMS[str(event_id)]
    gdpr = re.search(r'<div class="checks event_input-full">.*?</label>\s*</div>\s*</div>', block, flags=re.S)
    gdpr = gdpr.group(0) if gdpr else ''
    gdpr = gdpr.replace(' v-model="gdpr"', '')
    btn = re.search(r'<div class="event_input-full">\s*<button v-on:click="storeAnswers" class="([^"]*)">\s*<span class="txt">\s*(.*?)\s*</span>', block, flags=re.S)
    btn_cls, btn_txt = (btn.group(1).strip(), btn.group(2).strip()) if btn else ('button bg_color_2', 'Verstuur')
    questions = ' '.join(render_question(q) for q in sorted(form['questions'], key=lambda q: q['sort']))
    success = form.get('success', 'Bedankt voor je bericht! We nemen zo snel mogelijk contact met je op.')
    return ('<div id="event_api" data-part="event"><div id="event-form_w"><div id="upload_form"><div>'
            '<form id="event-form" data-niya-form data-name="%s" data-subject="%s" data-success="%s" novalidate>'
            '<ul id="event_api_errors" class="error-ul" style="display:none"></ul> %s '
            '<input type="checkbox" name="contact_me_by_fax_only" value="1" style="display:none !important" tabindex="-1" autocomplete="off"> '
            '%s <div class="event_input-full"><button type="submit" class="%s"><span class="txt">%s</span></button></div>'
            '</form></div></div></div></div>'
            % (esc(name), esc('Niya Solutions website: ' + name), esc('<p>' + success + '</p>'),
               questions, gdpr, esc(btn_cls), btn_txt))


def cf_decode(hexstr):
    b = bytes.fromhex(hexstr)
    return ''.join(chr(c ^ b[0]) for c in b[1:])


def undo_cloudflare(h):
    """Pages fetched through a proxy may carry Cloudflare e-mail obfuscation; restore the original text."""
    h = re.sub(r'<(a|span)\b[^>]*class="__cf_email__"[^>]*data-cfemail="([0-9a-f]+)"[^>]*>.*?</\1>',
               lambda m: html.escape(cf_decode(m.group(2)), quote=False), h, flags=re.S)
    h = re.sub(r'href="/cdn-cgi/l/email-protection#([0-9a-f]+)"',
               lambda m: 'href="mailto:%s"' % html.escape(cf_decode(m.group(1))), h)
    h = re.sub(r'<script[^>]*email-decode[^>]*></script>', '', h)
    return h


SEARCH_HTML = (
    '<div data-part="webshop" data-search=""><div id="search_page_w" data-webshop-search=""><div id="search_page">'
    '<div id="search_page_side"><div data-webshop-sticky="" data-offset="20" class="search_sticky"><div class="search_sticky_i">'
    '<div id="search_page_side_i" data-webshop-search-side=""><div id="page_search">'
    '<h2 id="page_search_title"> <span class="custom_font"><span class="first-word">Zoeken</span></span></h2> '
    '<form id="searchForm" method="get" action=""> <input type="text" id="keyword" name="keyword" placeholder="Waar ben je naar op zoek?"> '
    '<button class="search_button search_full_button search_button_mt search_button_grey"><span>Zoeken</span></button> '
    '<button type="reset" value="Reset" class="reset_button reset_full_button reset_button_mt"><span>Filters wissen</span></button>'
    '</form></div></div></div></div></div> '
    '<div id="search_page_content"><div class="webshop_product_list_with_side"></div> '
    '<div class="page_search_wrapper"><div class="text_styles"><div id="page_search_i" data-search-index="@@INDEX@@"></div></div></div>'
    '<div id="search_noresult" style="display:none"><div class="text_styles"><h2>Niet gevonden wat u zoekt? Neem contact met ons op!</h2></div></div>'
    '</div></div></div></div>')


def build_page(slug, h):
    h = undo_cloudflare(h)
    page_path = slug_to_path(slug)
    prefix = rel_prefix(page_path)

    # --- remove Webhero scripts / tracking / Vue-only markup
    h = re.sub(r'\s*<!-- Google Tag Manager -->.*?<!-- End Google Tag Manager -->', '', h, flags=re.S)
    h = re.sub(r'\s*<!-- Google Tag Manager \(noscript\) -->.*?<!-- End Google Tag Manager \(noscript\) -->', '', h, flags=re.S)
    h = re.sub(r'<noscript>\s*<iframe[^>]*googletagmanager.*?</noscript>', '', h, flags=re.S)
    h = re.sub(r'<script(?![^>]*application/ld\+json)[^>]*>.*?</script>', '', h, flags=re.S)
    h = re.sub(r'\s*<link rel="preload"[^>]*>', '', h)
    h = re.sub(r'\s*<link rel="stylesheet" href="https://cdn.webhero.be/css/flatpickr.min.css"\s*/?>', '', h)
    i = h.find('<div class="custom__popup__wrapper')
    if i > -1:
        h = h[:i] + h[find_block(h, i):]

    # --- forms (Vue) -> static HTML
    for m in list(re.finditer(r'<div id="event_api" data-part="event">', h))[::-1]:
        end = find_block(h, m.start())
        block = h[m.start():end]
        ev = EVENT_IDS.get(slug)
        if not ev:
            print('  !! no event id for', slug, file=sys.stderr)
            continue
        name = 'Homepage' if slug == 'index' else html.unescape(re.search(r'<title>(.*?)</title>', h).group(1)).split('|')[0].strip()
        h = h[:m.start()] + render_form(block, ev, name, prefix) + h[end:]

    # --- search page (was a Vue app on the Webhero API) -> static markup + assets/js/main.js
    i = h.find('<div data-part="webshop"')
    if slug == 'search' and i > -1:
        h = h[:i] + SEARCH_HTML.replace('@@INDEX@@', prefix + 'assets/search-index.json') + h[find_block(h, i):]

    # --- wide tables scroll inside their own box on phones (style.css already styles .table__wrapper)
    if 'table__wrapper' not in h:
        h = re.sub(r'(<table\b.*?</table>)', r'<div class="table__wrapper">\1</div>', h, flags=re.S)

    # --- agency credit (the new site is not built by Webhero)
    i = h.find('<div id="agency_logos_wrapper"')
    if i > -1:
        h = h[:i] + h[find_block(h, i):]

    # --- static equivalents of what the old scripts did on load
    h = h.replace('style="--font-family: roboto; --color-1: #212c52; --color-2:#cd9932;"',
                  'style="--font-family: roboto; --color-1: #212c52; --color-2:#cd9932; --color-1-contrast-color: white; --color-2-contrast-color: black;" '
                  'data-textcolor="white" data-textcolor2="black" data-page-textcolor="black"')
    if 'menu__dropdown--container' in h:
        h = h.replace('<div class="header__items">', '<div class="header__items nav__dropdown">')
        h = h.replace('<div class="nav__links">', '<div class="nav__links pillar__submenu">')
    h = re.sub(r'(<span class="custom_font">)(.*?)</span>', first_word, h, flags=re.S)

    # --- share icons: inline the SVGs (was svgInject)
    def svg_img(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        cls = re.search(r'class="([^"]+)"', tag).group(1).replace('svgInject', '').strip()
        name = 'social-' + src.split('/')[-1]
        fetch(src, os.path.join(ROOT, 'assets', 'icons', name))
        return tag.replace(src, '@@ASSET@@assets/icons/' + name).replace(' svgInject', '')
    h = re.sub(r'<img[^>]*class="[^"]*svgInject[^"]*"[^>]*>', svg_img, h, flags=re.S)

    # --- images / video
    def img_url(m):
        return local_image(m.group(0))
    h = re.sub(r'https://lh3\.googleusercontent\.com/[^"\'\s)]+', lambda m: '@@ASSET@@' + img_url(m), h)
    h = h.replace('https://storage.googleapis.com/smooty-1220.appspot.com/uploads/7305/1743580594_shutterstock3752090841.mp4',
                  '@@ASSET@@assets/video/hero.mp4')
    # absolute URLs for social meta tags, relative everywhere else
    h = re.sub(r'(<meta property="og:image" content=")@@ASSET@@', r'\1' + DOMAIN + '/', h)
    h = re.sub(r'(<script type="application/ld\+json">.*?</script>)',
               lambda m: m.group(1).replace('@@ASSET@@', DOMAIN + '/'), h, flags=re.S)
    h = h.replace('@@ASSET@@', prefix if prefix != './' else '')
    # lazy content images: <img src='' data-src=...> -> native lazy loading
    h = re.sub(r'<img\b([^>]*?)\ssrc=(?:\'\'|"")([^>]*?)\sdata-src="([^"]+)"', r'<img\1 src="\3"\2 loading="lazy" decoding="async"', h)

    # --- links
    def href(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        new = rewrite_internal(html.unescape(url), prefix)
        return '%s=%s%s%s' % (attr, q, esc(new) if new is not None else url, q)
    head_end = h.find('</head>')
    head, body = h[:head_end], h[head_end:]
    body = re.sub(r'\b(href|action)=(["\'])(.*?)\2', href, body)
    # favicon in head
    head = re.sub(r'(<link[^>]*rel="icon"[^>]*href=")([^"]+)"', lambda m: m.group(1) + m.group(2) + '"', head)
    h = head + body

    # --- stylesheet + script
    h = re.sub(r'<link property=["\']stylesheet["\'] rel="stylesheet" href="/css/style.min.css(?:\?\d+)?"\s*/?>',
               '<link rel="stylesheet" href="%sassets/css/style.css">' % ('' if prefix == './' else prefix), h)
    h = h.replace('</body>', '<script src="%sassets/js/main.js" defer></script>\n</body>' % ('' if prefix == './' else prefix))

    # tidy runs of blank lines left behind by removed blocks
    h = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', h)

    out = os.path.join(ROOT, page_path, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(h)
    return page_path


# ---------------------------------------------------------------- CSS


def build_css():
    css = open(os.path.join(ROOT, 'tools', 'style.source.css'), encoding='utf-8').read()

    def asset(m):
        url = m.group(2)
        name = url.split('/')[-1].split('?')[0]
        if 'fonts' in url or url.endswith(('.woff', '.woff2', '.ttf')):
            sub = 'fonts'
        else:
            sub = 'icons'
        if 'social-icons' in url:
            name = 'social-' + name
        dest = os.path.join(ROOT, 'assets', sub, name)
        if fetch(url, dest):
            return 'url(%s../%s/%s%s)' % (m.group(1), sub, name, m.group(1))
        return m.group(0)
    css = re.sub(r'url\((["\']?)(https://(?:cdn\.webhero\.be|fonts\.gstatic\.com)[^"\')]+)\1\)', asset, css)
    css += open(os.path.join(ROOT, 'tools', 'overrides.css'), encoding='utf-8').read()
    with open(os.path.join(ROOT, 'assets', 'css', 'style.css'), 'w', encoding='utf-8') as f:
        f.write(css)


# ---------------------------------------------------------------- main

FORMS = json.load(open(FORMS, encoding='utf-8'))
EVENT_IDS = {}


FAMILIES = ['facilitair-bedrijf', 'facility-manager', 'industriele-schoonmaak', 'kuisbedrijf', 'poetsbedrijf',
            'poetshulp', 'projectcoordinator', 'schoonmaakbedrijf', 'schoonmaker-kantoren']


def city_name(slug):
    return '-'.join(p.capitalize() for p in slug.split('-'))


def generate_missing_city_pages():
    """City landing pages are one template per service with only the city swapped.
    Pages that could not be mirrored are generated from a mirrored page of the same family."""
    urls = [l.strip() for l in open(os.path.join(ROOT, 'tools', 'urls.txt')) if l.strip()]
    slugs = {u.replace(DOMAIN, '').strip('/').replace('/', '__') or 'index' for u in urls}
    have = {f[:-5] for f in os.listdir(SRC) if f.endswith('.html')}
    generated = []
    for fam in FAMILIES:
        members = sorted(s[len(fam) + 1:] for s in slugs if s.startswith(fam + '-') and s != 'schoonmaakbedrijf-kantoren')
        real = [c for c in members if fam + '-' + c in have]
        if not real:
            print('  !! no template for', fam, file=sys.stderr)
            continue
        tpl_city = 'aalst' if 'aalst' in real else real[0]
        tpl = open(os.path.join(SRC, '%s-%s.html' % (fam, tpl_city)), encoding='utf-8').read()
        for c in members:
            if fam + '-' + c in have:
                continue
            h = tpl.replace(city_name(tpl_city), city_name(c)).replace(tpl_city, c)
            GENERATED.add(fam + '-' + c)
            generated.append((fam + '-' + c, h))
    missing = sorted(s for s in slugs - have if not any(s.startswith(f + '-') for f in FAMILIES) or s == 'schoonmaakbedrijf-kantoren')
    if missing:
        print('  !! not mirrored (no template possible):', ', '.join(missing), file=sys.stderr)
    return generated


GENERATED = set()


def main():
    build_css()
    fetch('https://storage.googleapis.com/smooty-1220.appspot.com/uploads/7305/1743580594_shutterstock3752090841.mp4',
          os.path.join(ROOT, 'assets', 'video', 'hero.mp4'))
    pages = sorted(f[:-5] for f in os.listdir(SRC) if f.endswith('.html'))
    for slug in pages:
        h = open(os.path.join(SRC, slug + '.html'), encoding='utf-8').read()
        m = re.search(r'event_id:\s*(\d+)', h)
        if m:
            EVENT_IDS[slug] = m.group(1)
    built = []
    for slug in pages:
        if slug == '404':
            continue
        h = open(os.path.join(SRC, slug + '.html'), encoding='utf-8').read()
        built.append(build_page(slug, h))
    for slug, h in generate_missing_city_pages():
        built.append(build_page(slug, h))
    if GENERATED:
        print('generated %d city pages from a template: %s' % (len(GENERATED), ' '.join(sorted(GENERATED))))
    if '404' in pages:
        build_404(open(os.path.join(SRC, '404.html'), encoding='utf-8').read())
    write_sitemap(built)
    write_search_index(built)
    print('built %d pages, %d images' % (len(built), len(IMG_MAP)))


def build_404(h):
    """404 page: served for any unknown URL, so it uses root-absolute links."""
    build_page('404', h)
    src = os.path.join(ROOT, '404', 'index.html')
    t = open(src, encoding='utf-8').read()
    t = re.sub(r'\b(href|src|action)="(?:\.\./)+', r'\1="/', t)
    t = t.replace("url('../assets/", "url('/assets/")
    open(os.path.join(ROOT, '404.html'), 'w', encoding='utf-8').write(t)
    os.remove(src)
    os.rmdir(os.path.dirname(src))


SKIP_SITEMAP = {'search/', 'contact/contactformulier-homepage/', 'onze-diensten-homepage/'}


def write_sitemap(paths):
    urls = ''.join('  <url><loc>%s/%s</loc></url>\n' % (DOMAIN, p) for p in sorted(paths) if p not in SKIP_SITEMAP)
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n')


def write_search_index(paths):
    """Small JSON index used by the /search/ page."""
    # same order as the old Webhero search: the order of the sitemap page
    order = []
    sm = os.path.join(SRC, 'sitemap.html')
    if os.path.exists(sm):
        for u in re.findall(r'<li><a href="([^"]+)"', open(sm, encoding='utf-8').read()):
            r = rewrite_internal(u, '')
            if r is not None and r not in order:
                order.append('' if r == './' else r)
    rank = {p: i for i, p in enumerate(order)}
    items = []
    for p in sorted(paths, key=lambda p: (rank.get(p, len(rank)), p)):
        if p in SKIP_SITEMAP or p.startswith('search'):
            continue
        t = open(os.path.join(ROOT, p, 'index.html'), encoding='utf-8').read()
        title = html.unescape(re.search(r'<title>(.*?)</title>', t, flags=re.S).group(1)).strip()
        desc = re.search(r'<meta id="description" name="description" content="(.*?)"', t)
        body = t[t.find('<body'):]
        body = re.sub(r'<(script|style|svg|form)\b.*?</\1>', ' ', body, flags=re.S)
        i, j = body.find('class="page'), body.find('<div class="footer">')
        text = html.unescape(re.sub(r'<[^>]+>', ' ', body[i:j] if i > -1 else body))
        text = re.sub(r'\s+', ' ', text).strip()
        items.append({'u': p, 't': title, 'd': html.unescape(desc.group(1)) if desc else '', 'x': text[:1500]})
    with open(os.path.join(ROOT, 'assets', 'search-index.json'), 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    main()
