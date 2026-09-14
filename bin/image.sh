#!/bin/zsh
# image.sh "<visual subject>" <NNNN> [ws]   Pick one real landscape photo, save to $WS/lessons/assets/NNNN.jpg, print YAML lines.
# Sources: NASA (space subjects) → Openverse (no key) → Unsplash (UNSPLASH_KEY, hotlinked) → Wikimedia Commons.
set -e
SUBJ=$1; ID=$2; WS=${3:-$PWD}; [ -d "$WS/lessons" ] || WS=$WS/learn
OUT="$WS/lessons/assets"; mkdir -p "$OUT"
UA="blackboard-skill/1.0 (student study tool; contact: local)"
python3 - "$SUBJ" "$ID" "$OUT" "$UA" "${UNSPLASH_KEY:-}" <<'PY'
import json,os,re,sys,urllib.request,urllib.parse
subj,lid,out,ua,ukey=sys.argv[1:]
REJECT=re.compile(r"\b(people|person|man|woman|girl|boy|portrait|face|selfie|text|poster|screenshot|illustration|drawing|clipart|vector|logo|ai[- ]generated|render|3d)\b",re.I)
def get(url,headers=None):
    req=urllib.request.Request(url,headers={"User-Agent":ua,**(headers or {})})
    with urllib.request.urlopen(req,timeout=20) as r: return r.read()
def save(url,credit,hotlink=False):
    if hotlink:
        print(f"photo: {url}\ncredit: {credit}"); return True
    data=get(url); p=os.path.join(out,f"{lid}.jpg")
    open(p,"wb").write(data); print(f"photo: assets/{lid}.jpg\ncredit: {credit}"); return True
def ok(*texts): return not any(REJECT.search(t or "") for t in texts)
def clean(t): return re.sub(r"\.(jpe?g|png|tiff?)$","",(t or "Untitled").replace("_"," ")).strip()
q=urllib.parse.quote(subj)
# NASA for space subjects
if re.search(r"galaxy|nebula|planet|star|space|orbit|moon|solar|astronaut|rocket|telescope",subj,re.I):
    try:
        j=json.loads(get(f"https://images-api.nasa.gov/search?q={q}&media_type=image&page_size=10"))
        for it in j["collection"]["items"]:
            d=it["data"][0]
            if not ok(d.get("title",""),d.get("description","")): continue
            a=json.loads(get(f"https://images-api.nasa.gov/asset/{d['nasa_id']}"))
            urls=[x["href"] for x in a["collection"]["items"]]
            u=next((x for x in urls if "~large" in x),None) or next((x for x in urls if "~orig" in x),None)
            if u and save(u,f"{d.get('title','')} · NASA ({d.get('center','')})"): sys.exit(0)
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
    j={"results":openverse(query,strict)}
    for it in j.get("results",[]):
        tags=" ".join(t.get("name","") for t in it.get("tags",[]) or [])
        if not ok(it.get("title",""),tags): continue
        url=it.get("url"); thumb=it.get("thumbnail")
        credit=f"{clean(it.get('title'))}{' by '+it['creator'] if it.get('creator') else ''} ({it.get('license','').upper()} {it.get('license_version','')}, via Openverse/{it.get('source','')})".replace("  "," ")
        if strict is False and (it.get("width",0) or 0)<1200: continue
        for u in (url,thumb):
            try:
                if u and save(u,credit): sys.exit(0)
            except Exception: continue
except Exception as e: print("openverse failed:",e,file=sys.stderr)  # one failure (usually a timeout) ends the Openverse pass
# Unsplash (hotlink, per API terms)
if ukey:
    try:
        j=json.loads(get(f"https://api.unsplash.com/search/photos?query={q}&orientation=landscape&content_filter=high&per_page=10&client_id={ukey}"))
        for it in j.get("results",[]):
            if not ok(it.get("alt_description",""),it.get("description","")): continue
            try: get(it["links"]["download_location"]+("&" if "?" in it["links"]["download_location"] else "?")+f"client_id={ukey}")
            except Exception: pass
            u=it["urls"]["regular"]; name=it["user"]["name"]; link=it["user"]["links"]["html"]
            save(u,f"Photo by {name} on Unsplash ({link}?utm_source=blackboard&utm_medium=referral)",hotlink=True); sys.exit(0)
    except Exception as e: print("unsplash failed:",e,file=sys.stderr)
# Wikimedia Commons featured / quality
for cat in ("Featured pictures on Wikimedia Commons","Quality images"):
    try:
        s=urllib.parse.quote(f'{subj} incategory:"{cat}" filetype:bitmap fileres:>1600')
        j=json.loads(get(f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={s}&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600&format=json"))
        for pg in (j.get("query",{}).get("pages",{}) or {}).values():
            ii=pg["imageinfo"][0]; em=ii.get("extmetadata",{})
            desc=re.sub("<[^>]+>","",em.get("ImageDescription",{}).get("value",""))
            if not ok(pg.get("title",""),desc): continue
            u=ii.get("thumburl") or ii["url"]
            credit=f"{pg['title'].replace('File:','')} · {re.sub('<[^>]+>','',em.get('Artist',{}).get('value','unknown'))} ({em.get('LicenseShortName',{}).get('value','')}, Wikimedia Commons)"
            if save(u,credit): sys.exit(0)
    except Exception as e: print("commons failed:",e,file=sys.stderr)
# Wikimedia Commons plain search (any photo): landscape and at least 1200px wide, best first
for query in queries:
    try:
        s=urllib.parse.quote(f'{query} filetype:bitmap fileres:>1200')
        j=json.loads(get(f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={s}&gsrnamespace=6&gsrlimit=15&prop=imageinfo&iiprop=url|extmetadata|size|mime&iiurlwidth=1600&format=json"))
        cands=[]
        for pg in (j.get("query",{}).get("pages",{}) or {}).values():
            ii=pg["imageinfo"][0]; em=ii.get("extmetadata",{})
            if ii.get("mime") not in ("image/jpeg","image/png"): continue
            w,h=ii.get("width",0) or 0,ii.get("height",0) or 0
            if w<1200 or w<=h: continue
            desc=re.sub("<[^>]+>","",em.get("ImageDescription",{}).get("value",""))
            cats=em.get("Categories",{}).get("value","")
            if not ok(pg.get("title",""),desc): continue
            # relevance: how many subject words (4+ letters) show up in title, description or categories
            hay=(pg.get("title","")+" "+desc+" "+cats).lower()
            kw=[w.lower() for w in re.findall(r"[a-zA-Z]{4,}",subj)]
            score=sum(1 for w in kw if w in hay)
            if score==0: continue
            cands.append((-score,pg.get("index",99),pg,ii,em))
        for _,_,pg,ii,em in sorted(cands,key=lambda c:(c[0],c[1])):
            u=ii.get("thumburl") or ii["url"]
            credit=f"{clean(pg['title'].replace('File:',''))} · {re.sub('<[^>]+>','',em.get('Artist',{}).get('value','unknown'))} ({em.get('LicenseShortName',{}).get('value','')}, Wikimedia Commons)"
            try:
                if save(u,credit): sys.exit(0)
            except Exception: continue
    except Exception as e: print("commons plain failed:",e,file=sys.stderr)
print("no photo found",file=sys.stderr); sys.exit(1)
PY
