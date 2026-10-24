#!/usr/bin/env python3
"""Inspect generated pages, local resources, anchors, metadata and release state."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import json
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
config=json.loads((ROOT/'site.config.json').read_text())
errors=[]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.refs=[];self.h1=0;self.in_title=False;self.title='';self.meta={};self.canonical=[];self.jsonld=[];self.in_schema=False;self.labels=[];self.inputs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='label' and a.get('for'):self.labels.append(a['for'])
        if tag in ['input','select','textarea'] and a.get('id'):self.inputs.append(a['id'])
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href',''))
        for attr in ['href','src']:
            if a.get(attr):self.refs.append(a[attr])
        if tag=='script' and a.get('type')=='application/ld+json':self.in_schema=True
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='script':self.in_schema=False
    def handle_data(self,data):
        if self.in_title:self.title+=data
        if self.in_schema:self.jsonld.append(data)

pages={}
for p in DIST.rglob('*.html'):
    parser=PageParser();parser.feed(p.read_text());pages[p]=parser
    if parser.h1!=1:errors.append(f'{p.relative_to(DIST)}: expected one H1, got {parser.h1}')
    if not parser.title:errors.append(f'{p}: missing title')
    if not parser.meta.get('description'):errors.append(f'{p}: missing description')
    duplicates=[s for s,n in Counter(parser.ids).items() if n>1]
    if duplicates:errors.append(f'{p}: duplicate IDs {duplicates}')
    for field in parser.inputs:
        if field not in parser.labels:errors.append(f'{p}: input {field} has no label')
    if config['public'] and p.name!='404.html' and not parser.canonical:errors.append(f'{p}: missing production canonical')
    if not config['public'] and 'noindex' not in parser.meta.get('robots',''):errors.append(f'{p}: preview can be indexed')
    for node in parser.jsonld:
        try:json.loads(node)
        except json.JSONDecodeError:errors.append(f'{p}: invalid JSON-LD')

for p,parser in pages.items():
    for ref in parser.refs:
        u=urlsplit(ref)
        if u.scheme or u.netloc:continue
        raw=unquote(u.path)
        if raw.startswith('/'):
            basepath=urlsplit(config.get('site_url','')).path.rstrip('/')
            if basepath and raw.startswith(basepath+'/'):raw=raw[len(basepath):]
            target=(DIST/raw.lstrip('/')).resolve()
        else:target=(p.parent/raw).resolve() if raw else p
        if target.is_dir():target=target/'index.html'
        if not target.exists():errors.append(f'{p.relative_to(DIST)}: missing target {ref}')
        elif u.fragment and target in pages and u.fragment not in pages[target].ids:
            errors.append(f'{p.relative_to(DIST)}: missing anchor {ref}')

titles=Counter(p.title for p in pages.values())
if any(n>1 for n in titles.values()):errors.append('Duplicate page titles')
css=(DIST/'assets/styles.css').read_text()
if 'mmg-sans.woff2' in css:errors.append('Unresolved font resource')
manifest=json.loads((DIST/'site.webmanifest').read_text())
for i in manifest['icons']:
    if not (DIST/i['src']).exists():errors.append(f'Missing manifest icon: {i["src"]}')
if config['public']:
    tree=ET.parse(DIST/'sitemap.xml');ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for loc in tree.findall('.//s:loc',ns):
        if not loc.text.startswith(config['site_url'].rstrip('/')+'/'):errors.append('Invalid sitemap origin')
    if 'Disallow: /' in (DIST/'robots.txt').read_text():errors.append('Public robots blocks crawling')
else:
    if 'Disallow: /' not in (DIST/'robots.txt').read_text():errors.append('Preview robots must block crawling')

if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'PASS: {len(pages)} HTML pages; links, fragments, page titles, descriptions, labels, icons and release state.')
