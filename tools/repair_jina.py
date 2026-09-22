#!/usr/bin/env python3
"""Repair pages fetched via r.jina.ai (X-Return-Format: html) so they match the
original server HTML: Jina drops the contents of inline <svg> icons and the doctype.

The icons are restored by matching the markup right before each <svg> against
pages that were mirrored directly (tools/source/*.html).

Usage: python3 tools/repair_jina.py <jina_dir> <out_dir>
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = re.compile(r'<svg\b[^>]*?(?:/>|>.*?</svg>)', re.S)


def norm(s):
    s = html.unescape(s)
    s = re.sub(r'<svg\b[^>]*?(?:/>|>.*?</svg>)', '<svg>', s, flags=re.S)
    s = s.replace('/>', '>')
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*=\s*""', '', s)
    s = re.sub(r'\s+(?=[">])', '', s)
    s = s.replace("'", '"')
    s = re.sub(r' aria-[a-z]+="[^"]*"', '', s)
    return s.strip()


def contexts(h, n=160):
    for m in SVG.finditer(h):
        pre = norm(h[max(0, m.start() - 600):m.start()])[-n:]
        yield m, pre


def build_corpus(src_dir):
    corpus = {}
    for f in os.listdir(src_dir):
        if not f.endswith('.html'):
            continue
        h = open(os.path.join(src_dir, f), encoding='utf-8').read()
        for m, pre in contexts(h):
            if '<path' in m.group(0) or '<circle' in m.group(0) or '<rect' in m.group(0):
                corpus.setdefault(pre, m.group(0))
    return corpus


# Icons that never occur on a directly mirrored page. The partner-link arrow on
# /referenties/ could not be mirrored exactly; this is the matching icon from the
# same icon set (stroke arrow, 24x24 viewBox).
KNOWN = [
    (re.compile(r'class="partner__link" title="[^"]*">$'),
     '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
     '<path d="M7 17L17 7M17 7H7M17 7V17" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
]


def repair(h, corpus):
    out, last, missing = [], 0, 0
    for m, pre in contexts(h):
        svg = corpus.get(pre)
        if svg is None:
            # fall back to a shorter context
            for n in (120, 80, 50, 30):
                keys = [k for k in corpus if k.endswith(pre[-n:])]
                vals = {corpus[k] for k in keys}
                if len(vals) == 1:
                    svg = vals.pop()
                    break
        if svg is None:
            for rx, known in KNOWN:
                if rx.search(pre):
                    svg = known
        if svg is None:
            missing += 1
            svg = m.group(0)
        out.append(h[last:m.start()])
        out.append(svg)
        last = m.end()
    out.append(h[last:])
    h = ''.join(out)
    if not h.lstrip().lower().startswith('<!doctype'):
        h = '<!DOCTYPE html>\n' + h
    return h, missing


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    corpus = build_corpus(os.path.join(ROOT, 'tools', 'source'))
    for f in sorted(os.listdir(src)):
        if not f.endswith('.html'):
            continue
        h = open(os.path.join(src, f), encoding='utf-8').read()
        if '</html>' not in h:
            print('incomplete', f)
            continue
        h, missing = repair(h, corpus)
        open(os.path.join(dst, f), 'w', encoding='utf-8').write(h)
        print('%-45s svg-unmatched=%d' % (f, missing))
