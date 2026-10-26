#!/bin/zsh
# image.sh "<visual subject>" <NNNN> [ws]   Pick one real landscape photo, save to a unique asset in $WS/lessons/assets, print YAML lines.
# Sources: NASA (space subjects) → Openverse (no key) → Unsplash (UNSPLASH_KEY, hotlinked) → Wikimedia Commons.
set -e
SUBJ=$1; ID=$2; WS=${3:-$PWD}; [ -d "$WS/lessons" ] || WS=$WS/learn
BIN=${0:A:h}
OUT="$WS/lessons/assets"; mkdir -p "$OUT"
UA="blackboard-skill/1.0 (student study tool; contact: local)"
python3 - "$SUBJ" "$ID" "$OUT" "$UA" "${UNSPLASH_KEY:-}" "$BIN" <<'PY'
import json,os,re,sys,urllib.request,urllib.parse
subj,lid,out,ua,ukey,bin_dir=sys.argv[1:]
sys.path.insert(0,bin_dir)
from pathlib import Path
from banner_guard import claim
from relevance import score, terms, rank_key
owners=list(Path(out).parent.glob(f"{lid}-*.md"))
# Inline lesson photos are not banners and have their own IDs (NNNN-pN).
owner=owners[0] if len(owners)==1 else None
if re.fullmatch(r"[0-9]{4}",lid) and owner is None:
    sys.exit("Create exactly one NNNN-*.md lesson before selecting its banner")
REJECT=re.compile(r"\b(people|person|man|woman|girl|boy|portrait|face|selfie|text|poster|screenshot|illustration|drawing|clipart|vector|logo|ai[- ]generated|render|3d)\b",re.I)
def get(url,headers=None):
    req=urllib.request.Request(url,headers={"User-Agent":ua,**(headers or {})})
    with urllib.request.urlopen(req,timeout=20) as r: return r.read()
def save(url,credit,hit,hotlink=False):
    credit=" ".join(credit.split())  # Artist HTML can carry newlines that would break the front matter
    data=None if hotlink else get(url)
    if data is not None and not (data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG\r\n\x1a\n")):
        return False  # reject HTML error pages and non-raster responses
    if owner:
        photo=claim(owner,data,url,credit,out,lid)
        if not photo: return False
    elif hotlink: photo=url
    else:
        p=os.path.join(out,f"{lid}.jpg"); open(p,"wb").write(data); photo=f"assets/{lid}.jpg"
    print(f"photo: {photo}\ncredit: {credit}\nphoto_source: {url}")
    print(f"image.sh: chose \"{credit.split(' · ')[0].split(' by ')[0]}\" for \"{subj}\" (matched: {', '.join(hit)}); open {photo} and confirm it shows the subject",file=sys.stderr)
    return True
def ok(*texts):
    # a reject word the subject itself names ("Java code on a screen" vs "text") does not reject
    named=set(re.findall(r"[a-z0-9]+",subj.lower()))
    return not any(m.lower() not in named for t in texts for m in REJECT.findall(t or ""))
DESC=300  # only the opening of a description counts: long museum records name every word somewhere
def ranked(cands):
    # cands: (texts tuple, payload); keep on-topic ones, most subject terms matched first, source order second
    out=[]
    for i,(texts,payload) in enumerate(cands):
        if not ok(*texts): continue
        hit=score(subj,*texts)
        if hit: out.append((rank_key(subj,texts[0],hit),i,hit,payload))
    return [(hit,payload) for _,_,hit,payload in sorted(out,key=lambda c:c[:2])]
print(f"image.sh: subject terms {terms(subj)}",file=sys.stderr)
def clean(t): return re.sub(r"\.(jpe?g|png|tiff?)$","",(t or "Untitled").replace("_"," ")).strip()
q=urllib.parse.quote(subj)
# NASA for space subjects
if re.search(r"galaxy|nebula|planet|star|space|orbit|moon|solar|astronaut|rocket|telescope",subj,re.I):
    try:
        j=json.loads(get(f"https://images-api.nasa.gov/search?q={q}&media_type=image&page_size=10"))
        items=[((d.get("title",""),d.get("description","")[:DESC]," ".join(d.get("keywords",[]) or [])),d) for d in (it["data"][0] for it in j["collection"]["items"])]
        for hit,d in ranked(items):
            a=json.loads(get(f"https://images-api.nasa.gov/asset/{d['nasa_id']}"))
            urls=[x["href"] for x in a["collection"]["items"]]
            u=next((x for x in urls if "~large" in x),None) or next((x for x in urls if "~orig" in x),None)
            if u and save(u,f"{d.get('title','')} · NASA ({d.get('center','')})",hit): sys.exit(0)
    except Exception as e: print("nasa failed:",e,file=sys.stderr)
# Openverse: full query with strict filters, then progressively simpler queries and looser filters
words=subj.split()
queries=[subj]+[" ".join(words[i:]) for i in range(1,len(words))]+[" ".join(words[:-i]) for i in range(1,len(words))]
seen=set(); queries=[x for x in queries if x and not (x in seen or seen.add(x))]
def get_fast(url):
    req=urllib.request.Request(url,headers={"User-Agent":ua})
    with urllib.request.urlopen(req,timeout=8) as r: return r.read()
def openverse(query,strict):
    qq=urllib.parse.quote(query)
    f="&aspect_ratio=wide&size=large" if strict else ""
    return json.loads(get_fast(f"https://api.openverse.org/v1/images/?q={qq}&category=photograph&license_type=commercial{f}&page_size=20")).get("results",[])
try:
  for query in queries:
   for strict in (True,False):
    results=openverse(query,strict)
    items=[((it.get("title",""),it.get("description","")," ".join(t.get("name","") for t in it.get("tags",[]) or [])),it) for it in results]
    for hit,it in ranked(items):
        url=it.get("url"); thumb=it.get("thumbnail")
        credit=f"{clean(it.get('title'))}{' by '+it['creator'] if it.get('creator') else ''} ({it.get('license','').upper()} {it.get('license_version','')}, via Openverse/{it.get('source','')})".replace("  "," ")
        if strict is False and (it.get("width",0) or 0)<1200: continue
        for u in (url,thumb):
            try:
                if u and save(u,credit,hit): sys.exit(0)
            except Exception: continue
except Exception as e: print("openverse failed:",e,file=sys.stderr)  # one failure (usually a timeout) ends the Openverse pass
# Unsplash (hotlink, per API terms)
if ukey:
    try:
        j=json.loads(get(f"https://api.unsplash.com/search/photos?query={q}&orientation=landscape&content_filter=high&per_page=10&client_id={ukey}"))
        items=[((it.get("alt_description",""),it.get("description",""),it.get("slug","")," ".join(t.get("title","") for t in it.get("tags",[]) or [])),it) for it in j.get("results",[])]
        for hit,it in ranked(items):
            try: get(it["links"]["download_location"]+("&" if "?" in it["links"]["download_location"] else "?")+f"client_id={ukey}")
            except Exception: pass
            u=it["urls"]["regular"]; name=it["user"]["name"]; link=it["user"]["links"]["html"]
            if save(u,f"Photo by {name} on Unsplash ({link}?utm_source=blackboard&utm_medium=referral)",hit,hotlink=True): sys.exit(0)
    except Exception as e: print("unsplash failed:",e,file=sys.stderr)
# Wikimedia Commons featured / quality
for cat in ("Featured pictures on Wikimedia Commons","Quality images"):
    try:
        s=urllib.parse.quote(f'{subj} incategory:"{cat}" filetype:bitmap fileres:>1600')
        j=json.loads(get(f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={s}&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600&format=json"))
        items=[]
        for pg in sorted((j.get("query",{}).get("pages",{}) or {}).values(),key=lambda p:p.get("index",99)):
            ii=pg["imageinfo"][0]; em=ii.get("extmetadata",{})
            desc=re.sub("<[^>]+>","",em.get("ImageDescription",{}).get("value",""))[:DESC]
            items.append(((pg.get("title",""),desc,em.get("Categories",{}).get("value","")),(pg,ii,em)))
        for hit,(pg,ii,em) in ranked(items):
            u=ii.get("thumburl") or ii["url"]
            credit=f"{clean(pg['title'].replace('File:',''))} · {re.sub('<[^>]+>','',em.get('Artist',{}).get('value','unknown'))} ({em.get('LicenseShortName',{}).get('value','')}, Wikimedia Commons)"
            try:
                if save(u,credit,hit): sys.exit(0)
            except Exception: continue
    except Exception as e: print("commons failed:",e,file=sys.stderr)
# Wikimedia Commons plain search (any photo): landscape and at least 1200px wide, best first
for query in queries:
    try:
        s=urllib.parse.quote(f'{query} filetype:bitmap fileres:>1200')
        j=json.loads(get(f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={s}&gsrnamespace=6&gsrlimit=15&prop=imageinfo&iiprop=url|extmetadata|size|mime&iiurlwidth=1600&format=json"))
        items=[]
        for pg in sorted((j.get("query",{}).get("pages",{}) or {}).values(),key=lambda p:p.get("index",99)):
            ii=pg["imageinfo"][0]; em=ii.get("extmetadata",{})
            if ii.get("mime") not in ("image/jpeg","image/png"): continue
            w,h=ii.get("width",0) or 0,ii.get("height",0) or 0
            if w<1200 or w<=h: continue
            desc=re.sub("<[^>]+>","",em.get("ImageDescription",{}).get("value",""))[:DESC]
            cats=em.get("Categories",{}).get("value","")
            items.append(((pg.get("title",""),desc,cats),(pg,ii,em)))
        for hit,(pg,ii,em) in ranked(items):
            u=ii.get("thumburl") or ii["url"]
            credit=f"{clean(pg['title'].replace('File:',''))} · {re.sub('<[^>]+>','',em.get('Artist',{}).get('value','unknown'))} ({em.get('LicenseShortName',{}).get('value','')}, Wikimedia Commons)"
            try:
                if save(u,credit,hit): sys.exit(0)
            except Exception: continue
    except Exception as e: print("commons plain failed:",e,file=sys.stderr)
print(f"no on-topic photo found for {subj!r}: candidates must name enough of {terms(subj)}; try concrete nouns",file=sys.stderr); sys.exit(1)
PY
