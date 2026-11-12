#!/usr/bin/env python3
"""Collecte de fiches publiques HelicoResto, pour revue humaine avant publication.
Usage: python scripts/sync_catalog.py
Ne télécharge pas les photos : conserve les URLs de la page source et leur provenance.
"""
import json, re, time, pathlib, urllib.parse, urllib.robotparser, xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='https://www.helicoresto.com'
HEAD={'User-Agent':'HelicoRestoCatalogImporter/1.0 (+review-only; contact site owner)'}
s=requests.Session();s.headers.update(HEAD)
robots=urllib.robotparser.RobotFileParser(BASE+'/robots.txt')
try: robots.read()
except Exception: pass

def get(url):
    if not url.startswith(BASE+'/') or not robots.can_fetch(HEAD['User-Agent'],url): return None
    try:
        r=s.get(url,timeout=18);r.raise_for_status();time.sleep(.65);return r
    except requests.RequestException as e:
        print('Ignoré:',url,str(e)[:90]);return None

def sitemap_urls():
    pending=[BASE+'/wp-sitemap.xml',BASE+'/sitemap_index.xml',BASE+'/post-sitemap.xml'];seen=set();pages=set()
    while pending and len(seen)<70:
        url=pending.pop(0)
        if url in seen:continue
        seen.add(url);r=get(url)
        if r is None:continue
        try:root=ET.fromstring(r.content)
        except ET.ParseError:continue
        for e in root.iter():
            if e.tag.endswith('loc') and e.text:
                link=e.text.strip()
                if link.endswith('.xml') and link.startswith(BASE):pending.append(link)
                elif re.search(r'/region-(sud-est|sud-ouest|nord-est|nord-ouest)/[^/]+/$',link):pages.add(link)
    return sorted(pages)

def txt(el):return el.get_text(' ',strip=True) if el else ''
def meta(soup,key):
    t=soup.find('meta',attrs={'property':key}) or soup.find('meta',attrs={'name':key})
    return t.get('content','').strip() if t else ''
def image_url(src,url):
    if not src:return ''
    u=urllib.parse.urljoin(url,src)
    return u if u.startswith('https://') or u.startswith('http://') else ''
def parse(url):
    r=get(url)
    if r is None:return None
    soup=BeautifulSoup(r.text,'html.parser')
    title=txt(soup.find('h1')) or meta(soup,'og:title').split(' - ')[0]
    if not title:return None
    body=txt(soup)
    region=re.search(r'/region-([^/]+)/',url)
    regions={'sud-est':'Sud-Est','sud-ouest':'Sud-Ouest','nord-est':'Nord-Est','nord-ouest':'Nord-Ouest'}
    category=[]
    for key in ('Hôtel','Restaurant','Golf','Château'):
        if key.lower() in body[:1500].lower():category.append(key)
    img=image_url(meta(soup,'og:image'),url)
    # Les photos sont strictement celles déclarées par la fiche elle-même.
    images=[]
    if img:images.append(img)
    for node in soup.select('article img, .entry-content img, .elementor-widget-image img'):
        src=node.get('data-src') or node.get('src') or ''
        u=image_url(src,url)
        if u and u not in images and not any(x in u.lower() for x in ('logo','avatar','icon','badge')):images.append(u)
        if len(images)>=12:break
    gps=re.search(r'GPS\s*:\s*([^\n]{8,65}?)(?=\s*(?:Ouvert toute|\(H\)|Manche à air|Téléphone|$))',body,re.I)
    # Ne pas transformer automatiquement une coordonnée non validée en point de navigation.
    section=soup.find(string=re.compile(r'H[ÉE]LISURFACE',re.I))
    approach=''
    if section:
        par=section.parent
        chunks=[]
        for nxt in par.next_elements:
            if getattr(nxt,'name',None) in ('h2','h3','h4') and nxt is not par:break
            if getattr(nxt,'name',None)=='p':chunks.append(txt(nxt))
            if len(chunks)>=8:break
        approach=' '.join(chunks)[:3500]
    slug=urllib.parse.urlparse(url).path.strip('/').split('/')[-1]
    return {'id':slug,'name':title,'city':'','department':'','region':regions.get(region.group(1),'') if region else '',
      'categories':category or ['Restaurant'],'lat':None,'lon':None,'gps':gps.group(1).strip() if gps else '',
      'phone':'','address':'','source':url,'approach':approach,'description':meta(soup,'description') or meta(soup,'og:description'),
      'image':img,'images':images,'imageOrigin':'HelicoResto.com — fiche source','windsock':'Non renseigné',
      'helipadMark':'Non renseigné','openAllYear':'Non renseigné','website':'','featured':False,
      'verified':False,'reviewRequired':True,'lastChecked':time.strftime('%Y-%m-%d')}

def main():
    urls=sitemap_urls();print('Fiches découvertes:',len(urls))
    previous=json.loads((ROOT/'data/venues.json').read_text())
    existing={x['source'].rstrip('/'):x for x in previous if x.get('source')}
    collected=[]
    for i,url in enumerate(urls,1):
        print(i,'/',len(urls),url)
        rec=parse(url)
        if rec:
            old=existing.get(url.rstrip('/'))
            if old:
                # Conserver les informations déjà contrôlées; enrichir uniquement les photos manquantes.
                if not old.get('image') and rec['image']:old['image']=rec['image'];old['images']=rec['images'];old['imageOrigin']=rec['imageOrigin']
                collected.append(old)
            else:collected.append(rec)
    out=ROOT/'data/import-review.json'
    out.write_text(json.dumps(collected,ensure_ascii=False,indent=2)+'\n')
    print('Prévisualisation:',out,'—',len(collected),'fiches. Revue manuelle requise avant publication.')
if __name__=='__main__':main()
