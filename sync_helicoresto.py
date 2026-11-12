#!/usr/bin/env python3
"""Synchronisation prudente des fiches publiques de HelicoResto.com.

Exécutable depuis GitHub Actions ou un PC connecté à Internet. N'invente jamais une
photo, une adresse ou des coordonnées. En cas d'échec, conserve l'existant.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, json, os, re, sys, time, unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, UnidentifiedImageError
from io import BytesIO
from xml.etree import ElementTree as ET

BASE='https://www.helicoresto.com/'
ROOT=Path(__file__).resolve().parents[1]
SEED=ROOT/'data'/'venues.json'
IMAGES=ROOT/'assets'/'venues'
REPORT=ROOT/'data'/'sync_report.json'
HEADERS={'User-Agent':'HelicoResto-DirectorySync/1.0 (+https://www.helicoresto.com/; moderate crawl)', 'Accept-Language':'fr-FR,fr;q=0.9,en;q=0.5'}
SITEMAPS=['wp-sitemap.xml','sitemap_index.xml','sitemap.xml','post-sitemap.xml','portfolio-sitemap.xml','avada_portfolio-sitemap.xml','page-sitemap.xml']
CATEGORIES=['','region-sud-est/','region-sud-ouest/','region-nord-est/','region-nord-ouest/','hotels/','restaurants/','golfs/','chateaux/','hotels-sud-est/','hotels-sud-ouest/','restaurants-sud-est/','restaurants-sud-ouest/','chateaux-sud-est/','chateaux-sud-ouest/','carte-des-restaurants/','non-classe/','category/non-classe/','portfolio_category/sud-est/','portfolio_category/sud-ouest/']
BADPATH=('/wp-admin/','/wp-json/','/wp-content/','/feed','/author/','/tag/','/comments/', '/cdn-cgi/')
BADIMAGE=('avatar','gravatar','logo','michelin','gault','badge','favicon','star','etoile','social','icon','facebook','instagram','tripadvisor','loading','placeholder','map-pin','signature','price','banner')
STOPWORDS=set('le la les de des du d un une chateau domaine restaurant hotel spa et aux au l mas fontenille verchant'.split())
MAX_PAGES=1300

def clean(s):return re.sub(r'\s+',' ',s or '').strip()
def slug(s):
 s=unicodedata.normalize('NFKD',str(s));s=''.join(c for c in s if not unicodedata.combining(c));return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')[:75] or 'fiche'
def canonical(url):
 p=urlsplit(urljoin(BASE,url));
 if p.hostname not in ('helicoresto.com','www.helicoresto.com') or p.scheme not in ('http','https'):return ''
 path=re.sub('/+','/',unquote(p.path));
 if any(x in path for x in BADPATH) or re.search(r'\.(?:jpe?g|png|webp|gif|css|js|pdf|mp4|ico|svg)$',path,re.I):return ''
 return BASE.rstrip('/')+path.rstrip('/')+'/'
def getgps(raw):
 # Exemples: 43.622N 5.32E, 44.731263N, 0.554077W, 43.6, 5.3, 43°37'19.7"N 3°55'15.1"E
 raw=clean(raw).replace('−','-').replace('’',"'").replace('′',"'").replace('″','"');
 dms=re.findall(r'(\d{1,3})\s*°\s*(\d{1,2})\s*[\'’′]\s*([\d.,]+)\s*["″]?\s*([NSEW])',raw,re.I)
 if len(dms)>=2:
  xy=[]
  for deg,mins,sec,d in dms[:2]:
   n=float(deg)+float(mins)/60+float(sec.replace(',','.'))/3600
   xy.append(-n if d.upper() in ('S','W') else n)
  return tuple(xy)
 signed=re.findall(r'(-?\d{1,3}(?:[.,]\d{4,}))\s*([NSEW])?',raw,re.I)
 if len(signed)>=2:
  xy=[]
  for num,dir in signed[:2]:
   n=float(num.replace(',','.'));xy.append(-abs(n) if dir.upper() in ('S','W') else n)
  return tuple(xy)
 return (None,None)

def find_section(lines,keys,stopkeys,maxlen=1900):
 start=next((i for i,x in enumerate(lines) if any(k in slug(x) for k in keys)),None)
 if start is None:return ''
 a=[]
 for s in lines[start+1:start+30]:
  if any(k in slug(s) for k in stopkeys):break
  if s and len(s)>28 and not any(x in slug(s) for x in ('pilote-helico','voir-tous-les-etablissement','revendiquer')):a.append(clean(s))
  if sum(map(len,a))>maxlen:break
 return ' '.join(a)[:maxlen]

def relevant_page(soup):
 main=soup.select_one('main') or soup.select_one('#main') or soup.select_one('article') or soup
 t=main.get_text(' ',strip=True)
 title=(main.find(['h1','h2']) or soup.find('h1'))
 if not title:return False
 head=clean(title.get_text(' ',strip=True))
 signals=sum(bool(re.search(p,t,re.I)) for p in (r'h[ée]lisurface',r'(?:GPS|coordonn[ée]es GPS)\s*:',r'informations pratiques|infos d[ée]taill[ée]es',r'manche\s*[àa]\s*air'))
 return signals>=2 and 4<len(head)<100 and len(t)>130

def classify(text):
 text=clean(text).upper()
 a=[]
 for key,label in [('HÔTEL','Hôtel'),('HOTEL','Hôtel'),('RESTAURANT','Restaurant'),('GOLF','Golf'),('CHÂTEAU','Château'),('CHATEAU','Château')]:
  if key in text and label not in a:a.append(label)
 return a or ['Restaurant']

def meta(soup,p):
 m=soup.find('meta',attrs={'property':p}) or soup.find('meta',attrs={'name':p})
 return (m.get('content') or '').strip() if m else ''

def image_candidates(soup,title):
 out=[];used=set();tokens=[x for x in slug(title).split('-') if len(x)>=4 and x not in STOPWORDS]
 def push(url,score=0):
  if not url or url.startswith('data:'):return
  u=urljoin(BASE,url.split(' ')[0]);p=urlsplit(u)
  if p.hostname not in ('www.helicoresto.com','helicoresto.com') or '/wp-content/uploads/' not in p.path:return
  if not re.search(r'\.(?:jpe?g|png|webp)(?:$|\?)',u,re.I):return
  path=unquote(p.path).lower()
  if any(b in path for b in BADIMAGE):return
  if u in used:return
  used.add(u)
  score+=sum(6 for tok in tokens if tok in slug(path))
  out.append((score,u))
 for key in ['og:image','twitter:image']:
  push(meta(soup,key),5)
 selectors=['.fusion-gallery img','.fusion-post-content img','.post-content img','.entry-content img','article img','.fusion-imageframe img','.portfolio-content img','.elementor-widget-container img']
 for selector in selectors:
  for im in soup.select(selector):
   score=6 if 'gallery' in selector else 3
   alt=slug(im.get('alt',''))
   score+=sum(3 for tok in tokens if tok in alt)
   w=int(re.sub(r'\D','',str(im.get('width','') or '0')) or '0')
   if w>700:score+=2
   for a in ['data-orig-src','data-src','data-lazy-src','src']:
    if im.get(a):push(im.get(a),score)
   if im.get('srcset'):
    for s in im['srcset'].split(','):push(s.strip().split(' ')[0],score)
 for a in soup.select('article a[href],.fusion-post-content a[href],.post-content a[href]'):
  if re.search(r'\.(jpg|jpeg|png|webp)$',urlsplit(a['href']).path,re.I):push(a['href'],3)
 return [u for _,u in sorted(out,key=lambda x:-x[0])]

def parse_page(soup,url):
 if not relevant_page(soup):return None
 body=soup.select_one('main') or soup.select_one('#main') or soup.select_one('article') or soup
 title=(body.find(['h1','h2']) or soup.find('h1'))
 title=clean(title.get_text(' ',strip=True))
 if len(title)<4:return None
 lines=[clean(s) for s in body.get_text('\n',strip=True).splitlines()]
 lines=[x for x in lines if x]
 gps='';loc=''
 for line in lines:
  if re.match(r'^(?:GPS|Coordonn[ée]es GPS)\s*:',line,re.I):gps=clean(line.split(':',1)[1])[:110];break
 lat,lon=getgps(gps)
 if not gps:
  for line in lines:
   if re.search(r'\bGPS\s*:',line,re.I):gps=clean(re.split(r'\bGPS\s*:',line,maxsplit=1,flags=re.I)[1])[:100];lat,lon=getgps(gps);break
 types=[];idx=next((i for i,l in enumerate(lines) if title.lower() in l.lower()),0)
 for line in lines[idx+1:idx+7]:
  if re.search(r'H[ÔO]TEL|RESTAURANT|CH[ÂA]TEAU|GOLF',line,re.I) and len(line)<85:
   types=classify(line);break
 if not types:types=['Restaurant']
 info=[]
 k=next((i for i,l in enumerate(lines) if slug(l).startswith('informations-pratiques') or slug(l).startswith('infos-detaillees')),None)
 if k is not None:info=lines[k+1:k+16]
 phone=next((re.search(r'(?<!\d)0[1-9](?:[ .-]?\d{2}){4}(?!\d)',x).group() for x in info if re.search(r'(?<!\d)0[1-9](?:[ .-]?\d{2}){4}(?!\d)',x)),None)
 def flag(key):
  m=next((re.search(key+r'[^:\n?]*[?:]\s*(OUI|NON)',x,re.I) for x in info if re.search(key+r'[^:\n?]*[?:]\s*(OUI|NON)',x,re.I)),None)
  return m.group(1).capitalize() if m else None
 windsock=flag('manche\\s*[àa]\\s*air')
 if not windsock:
  windsock=next((re.search(r'manche\s*[àa]\s*air\s*:\s*(oui|non)',x,re.I).group(1).capitalize() for x in info if re.search(r'manche\s*[àa]\s*air\s*:\s*(oui|non)',x,re.I)),None)
 h=next((re.search(r'\(?H\)?\s*visible\s*\??\s*:\s*(OUI|NON)',x,re.I).group(1).capitalize() for x in info if re.search(r'\(?H\)?\s*visible\s*\??\s*:\s*(OUI|NON)',x,re.I)),None)
 year=next((re.search(r'ouvert\s+toute\s+l.ann[ée]e\s*:\s*(OUI|NON)',x,re.I).group(1).capitalize() for x in info if re.search(r'ouvert\s+toute\s+l.ann[ée]e\s*:\s*(OUI|NON)',x,re.I)),None)
 addr=next((l for l in info if re.search(r'\b\d{5}\b',l) and 'GPS' not in l),None)
 if not addr:
  addr=next((l for l in info if l.lower().startswith('adresse')),None)
 if addr:addr=re.sub(r'^Adresse\s*:\s*','',addr,flags=re.I)
 city='';dept=''
 if addr:
  m=re.search(r'\b(\d{2})(\d{3})\s+(.+)',addr)
  if m:dept=m.group(1);city=m.group(3).split(',')[0]
 # Some pages have the name as H2 then opening labels — keep only content near the entry.
 desc=find_section(lines,['restaurant-gastronomique','restaurant-bistrot','restaurant'],['hotel','informations-pratiques','infos-detaillees','helisurface','mot-de-l-etablissement'],1100)
 approach=find_section(lines,['helisurface','approche-et-helisurface'],['restaurant','hotel','informations-pratiques','infos-detaillees'],1500)
 site=next((x for x in info if 'www.' in x or x.startswith('https://')),None)
 if site:
  site=re.search(r'(?:https?://)?(?:www\.)[\w.-]+(?:/[\w./-]+)?',site)
  site=('https://'+site.group().removeprefix('https://')) if site else None
 out={'id':slug(urlsplit(url).path.split('/')[-2]),'name':title,'city':city or 'France','department':dept,'region':'Sud-Ouest' if '/region-sud-ouest/' in url else 'Sud-Est' if '/region-sud-est/' in url else 'Non précisée','categories':types,'lat':lat,'lon':lon,'gps':gps,'phone':phone,'address':addr,'website':site,'source':url,'approach':approach,'description':desc,'windsock':windsock,'helipadMark':h,'openAllYear':year,'verified':bool(gps),'lastChecked':dt.date.today().isoformat()}
 return out

def media_files(session,urls,slugname,max_images=6):
 imgs=[]
 for url in urls[:max_images*4]:
  if len(imgs)>=max_images:break
  try:
   response=session.get(url,timeout=18,stream=False)
   if not response.ok or len(response.content)>8*1024*1024 or len(response.content)<7000:continue
   if not response.headers.get('content-type','').lower().startswith('image/'):continue
   raw=Image.open(BytesIO(response.content));raw=ImageOps.exif_transpose(raw).convert('RGB')
   if raw.width<500 or raw.height<290:continue
   raw.thumbnail((1600,1200),Image.Resampling.LANCZOS)
   IMAGES.mkdir(exist_ok=True,parents=True)
   path=IMAGES/f'{slugname}-{len(imgs)+1}.webp'
   raw.save(path,'WEBP',quality=83,method=5)
   imgs.append('assets/venues/'+path.name)
  except (requests.RequestException,OSError,ValueError,UnidentifiedImageError):continue
 return imgs

class Crawler:
 def __init__(self,limit,delay,dry):
  self.session=requests.Session();self.session.headers.update(HEADERS)
  self.limit=limit;self.delay=delay;self.dry=dry;self.pages=0;self.errors=[];self.robots=RobotFileParser();self.robots.set_url(BASE+'robots.txt')
  try:
   r=self.session.get(BASE+'robots.txt',timeout=12)
   if r.ok:self.robots.parse(r.text.splitlines());self.robots_ok=True
   else:self.robots_ok=False;self.errors.append(f'robots.txt HTTP {r.status_code}')
  except requests.RequestException as e:
   self.robots_ok=False;self.errors.append('robots.txt indisponible : '+str(e)[:130])
 def request(self,url):
  if self.pages>=self.limit:return None
  if self.robots_ok and not self.robots.can_fetch(HEADERS['User-Agent'].split('/')[0],url):return None
  try:
   response=self.session.get(url,timeout=17,allow_redirects=True)
   self.pages+=1
   if self.delay:time.sleep(self.delay)
   if response.ok:return response
   self.errors.append(f'{response.status_code} {url}')
  except requests.RequestException as e:self.errors.append(str(e)[:120]+' '+url)
  return None
 def sitemap(self):
  queue=collections.deque(urljoin(BASE,x) for x in SITEMAPS);seen=set();links=set()
  try:
   rr=self.session.get(BASE+'robots.txt',timeout=8)
   if rr.ok:
    for ln in rr.text.splitlines():
     if ln.lower().startswith('sitemap:'):
      sm=ln.split(':',1)[1].strip()
      if urlsplit(sm).hostname in ('www.helicoresto.com','helicoresto.com'):queue.append(sm)
  except requests.RequestException:pass
  while queue and len(seen)<55 and self.pages<self.limit:
   url=queue.popleft()
   if url in seen:continue
   seen.add(url);r=self.request(url)
   if r is None or not r.text.lstrip().startswith(('<?xml','<urlset','<sitemapindex')):continue
   try:xml=ET.fromstring(r.content)
   except ET.ParseError:continue
   for child in xml.iter():
    if not child.tag.endswith('loc') or not child.text:continue
    loc=child.text.strip()
    if re.search(r'\.xml(?:\?.*)?$',loc):
     if urlsplit(loc).hostname in ('www.helicoresto.com','helicoresto.com'):queue.append(loc)
    else:
     link=canonical(loc)
     if link:links.add(link)
  return links
 def all_links(self):
  found=self.sitemap();seed=set(canonical(urljoin(BASE,x)) for x in CATEGORIES)
  try:
   cur=json.loads(SEED.read_text(encoding='utf8'))
   found|={canonical(x['source']) for x in cur if x.get('source')}
  except Exception:pass
  queue=collections.deque(x for x in seed if x)
  seen=set()
  # Crawl navigation, archive pages, and pagination to discover pages absent from sitemap.
  while queue and len(seen)<110 and self.pages<self.limit//2:
   url=queue.popleft()
   if url in seen:continue
   seen.add(url);r=self.request(url)
   if r is None or 'html' not in r.headers.get('content-type',''):continue
   soup=BeautifulSoup(r.text,'html.parser')
   for anchor in soup.select('a[href]'):
    link=canonical(anchor.get('href',''))
    if not link:continue
    path=urlsplit(link).path
    if re.search(r'/page/\d+/?$',path):
     if link not in seen:queue.append(link)
    elif len(path.split('/'))>=3:found.add(link)
   for rel in soup.select('link[rel="next"][href]'):
    link=canonical(rel['href'])
    if link and link not in seen:queue.append(link)
  return sorted(x for x in found if x)
 def sync(self):
  previous=json.loads(SEED.read_text(encoding='utf8')) if SEED.exists() else []
  records={canonical(x['source']):x for x in previous if x.get('source') and canonical(x['source'])}
  before=len(records);new=0;withphotos=0
  discovered=self.all_links();print(f'Found {len(discovered)} links; {self.pages} requests for discovery')
  for i,url in enumerate(discovered):
   if self.pages>=self.limit:break
   r=self.request(url)
   if r is None or 'html' not in r.headers.get('content-type',''):continue
   soup=BeautifulSoup(r.text,'html.parser')
   parsed=parse_page(soup,url)
   if not parsed:continue
   old=records.get(url)
   if old:
    record={**old,**{k:v for k,v in parsed.items() if v not in ('',None,[])}}
    record['id']=old['id']
   else:
    record=parsed;new+=1
   if not self.dry:
    candidate=image_candidates(soup,parsed['name'])
    media=media_files(self.session,candidate,record['id']) if candidate else []
    if media:
     record['image']=media[0];record['images']=media;record['imageOrigin']='photographies extraites de la fiche HelicoResto.com';withphotos+=1
   records[url]=record
   if i%25==0:print(f'Processed {i+1}/{len(discovered)}; {new} new entries')
  merged=sorted(records.values(),key=lambda x:(not x.get('featured',False),x['name']))
  info={'lastSync':dt.datetime.now(dt.timezone.utc).isoformat(),'requests':self.pages,'linksFound':len(discovered),'entriesBefore':before,'entriesAfter':len(merged),'newEntries':new,'photosFetchedEntries':withphotos,'errors':self.errors[:50],'complete':self.pages<self.limit and len(self.errors)<10,'note':'Le compteur final correspond aux fiches réellement récupérées, sans garantie d’exhaustivité de tous les référencements du site.'}
  if not self.dry:
   SEED.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
   (ROOT/'data'/'fallback-data.js').write_text('window.HELICO_VENUES = '+json.dumps(merged,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
   REPORT.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(json.dumps(info,ensure_ascii=False,indent=2))
  if new==0 and self.pages<=2:print('AVERTISSEMENT : source inaccessible, données existantes préservées.')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=MAX_PAGES);parser.add_argument('--delay',type=float,default=.35);parser.add_argument('--dry-run',action='store_true')
 args=parser.parse_args();Crawler(args.limit,args.delay,args.dry_run).sync()
