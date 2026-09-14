#!/bin/zsh
# lms-pull.sh <course-url> [ws]   Token path only (Canvas personal token or Moodle mobile token in $WS/.lms-token).
# Browser paths (Canvas without token, Blackboard, Brightspace) are driven by the agent per LMS.md and write the same layout.
set -e
URL=$1; WS=${2:-$PWD}; [ -d "$WS/lessons" ] || [ -f "$WS/MISSION.md" ] || WS=$WS/learn
mkdir -p "$WS/sources"
python3 - "$URL" "$WS" <<'PY'
import json,os,re,sys,urllib.request,urllib.parse,time
url,ws=sys.argv[1:]
src=os.path.join(ws,"sources"); tokf=os.path.join(ws,".lms-token")
tok=open(tokf).read().strip() if os.path.exists(tokf) else ""
def lms(u):
    if "instructure.com" in u or "/api/v1/" in u or re.search(r"/courses/\d+",u): return "canvas"
    if "/course/view.php?id=" in u: return "moodle"
    if "/ultra/courses/" in u or "/webapps/" in u: return "blackboard"
    if "/d2l/" in u: return "brightspace"
    return "unknown"
kind=lms(url)
if kind=="unknown":
    print("Unknown LMS. Drop the files in this folder, or paste the link to a Canvas/Moodle/Blackboard/Brightspace course."); sys.exit(0)
if kind in ("blackboard","brightspace"):
    print(f"{kind}: no student tokens. The agent pulls it through your logged-in browser (see LMS.md)."); sys.exit(0)
if not tok:
    print(f"{kind}: no token in {tokf}. Either create one (Canvas: Account → Settings → New Access Token; Moodle: login/token.php) and save it there, or let the agent pull through your logged-in browser (LMS.md)."); sys.exit(0)
def tier_of(name,kind_):
    n=name.lower()
    if kind_=="assignment": return "hw",5
    if re.search(r"practice|sample",n) and re.search(r"exam|test|midterm|final|quiz",n): return "practice-exam",3
    if re.search(r"exam|test|midterm|final",n): return "past-exam",4
    if kind_=="announcement" and re.search(r"exam|test|quiz|topics",n): return "professor-notes",2
    if re.search(r"topics|syllabus|review|study guide",n): return "topic-list",1
    if kind_ in ("page","slides") or re.search(r"lecture|week|slides|notes",n): return "slides",6
    return "supplementary",7
manifest=[]
def add(kind_,title,path,source_url):
    k,t=tier_of(title,kind_); manifest.append({"kind":k,"tier":t,"title":title,"path":os.path.relpath(path,ws),"source_url":source_url,"pulled_at":time.strftime("%Y-%m-%d")})
def get(u,headers=None):
    req=urllib.request.Request(u,headers=headers or {})
    with urllib.request.urlopen(req,timeout=30) as r: return r.read(),r.headers
if kind=="canvas":
    host=re.match(r"https?://[^/]+",url).group(0); cid=re.search(r"/courses/(\d+)",url).group(1)
    H={"Authorization":f"Bearer {tok}"}
    def pages(path):
        u=f"{host}/api/v1{path}{'&' if '?' in path else '?'}per_page=100"; out=[]
        while u:
            b,h=get(u,H); out+=json.loads(b); u=None
            for part in (h.get("Link") or "").split(","):
                if 'rel="next"' in part: u=part.split(";")[0].strip("<> ")
        return out
    for f in pages(f"/courses/{cid}/files"):
        d=os.path.join(src,"files"); os.makedirs(d,exist_ok=True); p=os.path.join(d,f["display_name"])
        try: open(p,"wb").write(get(f["url"],H)[0]); add("file",f["display_name"],p,f.get("url",""))
        except Exception as e: print("skip",f["display_name"],e,file=sys.stderr)
    for a in pages(f"/courses/{cid}/assignments?order_by=due_at"):
        d=os.path.join(src,"hw"); os.makedirs(d,exist_ok=True); p=os.path.join(d,re.sub(r"[^\w.-]+","-",a["name"])+".md")
        open(p,"w").write(f"# {a['name']}\n\ndue: {a.get('due_at')}\npoints: {a.get('points_possible')}\n\n{a.get('description') or ''}\n"); add("assignment",a["name"],p,a.get("html_url",""))
    for pg in pages(f"/courses/{cid}/pages"):
        try:
            b,_=get(f"{host}/api/v1/courses/{cid}/pages/{pg['url']}",H); body=json.loads(b).get("body") or ""
            d=os.path.join(src,"pages"); os.makedirs(d,exist_ok=True); p=os.path.join(d,pg["url"]+".md")
            open(p,"w").write(f"# {pg['title']}\n\n{body}\n"); add("page",pg["title"],p,pg.get("html_url",""))
        except Exception as e: print("skip page",pg.get("title"),e,file=sys.stderr)
    for an in pages(f"/announcements?context_codes[]=course_{cid}&start_date=2000-01-01"):
        d=os.path.join(src,"announcements"); os.makedirs(d,exist_ok=True); p=os.path.join(d,re.sub(r"[^\w.-]+","-",an["title"])+".md")
        open(p,"w").write(f"# {an['title']}\n\n{an.get('posted_at')}\n\n{an.get('message') or ''}\n"); add("announcement",an["title"],p,an.get("html_url",""))
elif kind=="moodle":
    host=re.match(r"https?://[^/]+",url).group(0); cid=re.search(r"id=(\d+)",url).group(1)
    b,_=get(f"{host}/webservice/rest/server.php?wstoken={tok}&moodlewsrestformat=json&wsfunction=core_course_get_contents&courseid={cid}")
    for sec in json.loads(b):
        for mod in sec.get("modules",[]):
            for c in mod.get("contents",[]) or []:
                if c.get("type")!="file": continue
                d=os.path.join(src,"files"); os.makedirs(d,exist_ok=True); p=os.path.join(d,c["filename"])
                try: open(p,"wb").write(get(c["fileurl"]+("&" if "?" in c["fileurl"] else "?")+f"token={tok}")[0]); add("assignment" if mod.get("modname")=="assign" else "file",c["filename"],p,c["fileurl"])
                except Exception as e: print("skip",c["filename"],e,file=sys.stderr)
# text extraction for pdf
for m in manifest:
    p=os.path.join(ws,m["path"])
    if p.lower().endswith(".pdf"):
        os.system(f'pdftotext -layout "{p}" "{p}.txt" 2>/dev/null')
json.dump(manifest,open(os.path.join(src,"manifest.json"),"w"),indent=1)
print(f"{kind}: pulled {len(manifest)} items into {src}. Tiers: "+", ".join(f"{m['title']} (tier {m['tier']})" for m in manifest[:12])+(" …" if len(manifest)>12 else ""))
PY
