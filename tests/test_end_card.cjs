// End card: the quote is picked deterministically from the pool, and the photo only ever comes from outside the skill.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const SKILL=path.join(__dirname,'..');
const source=fs.readFileSync(path.join(SKILL,'board/board.html.tmpl'),'utf8');
const a=source.indexOf('const ENDCARD_QUOTES='), b=source.indexOf('let endEl=');
assert(a>0&&b>a,'pool and picker present');
const ctx={TextEncoder};
vm.createContext(ctx); vm.runInContext(source.slice(a,b).replace(/^const /gm,'var '),ctx);
const pool=ctx.ENDCARD_QUOTES;
assert(pool.length>=25&&pool.length<=40,'about thirty quotes');
assert.equal(new Set(pool).size,pool.length,'no duplicates');
// Ultraman sounds only: every word is one of his battle cries or the color timer
const SOUND=/^(t?sa+h*|tsa+h+|ts?ah+|ning|nung|seya+h|hah|shuwatch|shuwa|dyuwa+h?|hmph|shea+h)$/i;
for(const q of pool) for(const w of q.split(/[\s.,!…]+/).filter(Boolean)) assert.match(w,SOUND,`"${w}" in "${q}" is not an Ultraman sound`);
// deterministic, from the pool, spread over it
const keys=[]; for(const ws of ['math1552','stem','ece2020']) for(let i=1;i<=40;i++) keys.push(ws+'/'+String(i).padStart(4,'0'));
for(const k of keys){ const q=ctx.endcardPick(k); assert(pool.includes(q)); assert.equal(ctx.endcardPick(k),q,'same lesson, same quote'); }
assert(new Set(keys.map(ctx.endcardPick)).size>=pool.length*0.6,'lessons get different quotes');
// the kindle converter uses the same pool and hash
const kindle=path.join(SKILL,'../kindle/scripts/lesson_to_epub.py');
if(fs.existsSync(kindle)){
  const py=`import importlib.util,json,os,sys,tempfile
spec=importlib.util.spec_from_file_location('l2e',sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
os.environ['BLACKBOARD_END_CARD']='/nonexistent.jpg'
d=tempfile.mkdtemp(); out={}
for k in json.loads(sys.argv[3]):
    ws,num=k.split('/'); ld=os.path.join(d,ws,'learn','lessons'); os.makedirs(ld,exist_ok=True)
    md,photo=m.end_card({},ld,num,sys.argv[2]); assert photo==''; out[k]=md
print(json.dumps(out))`;
  const got=JSON.parse(execFileSync('python3',['-c',py,kindle,SKILL,JSON.stringify(keys.slice(0,12))],{encoding:'utf8'}));
  for(const [k,md] of Object.entries(got)) assert(md.includes('“'+ctx.endcardPick(k)+'”'),`kindle quote for ${k}`);
}
// the photo: served only by the bridge route, never from the skill folder, and no image file for it in the skill
assert(source.includes('src="/end-card.jpg"'),'board loads the photo from the bridge route');
const bridge=fs.readFileSync(path.join(SKILL,'board/bridge.py'),'utf8');
assert(bridge.includes('if p.startswith(os.path.realpath(ROOT) + os.sep):'),'bridge refuses a photo inside the skill');
const walk=d=>fs.readdirSync(d,{withFileTypes:true}).flatMap(e=>e.name==='node_modules'||e.name.startsWith('.')?[]:e.isDirectory()?walk(path.join(d,e.name)):[path.join(d,e.name)]);
const files=walk(SKILL);
assert.deepEqual(files.filter(f=>/end-?card|ultraman|mebius/i.test(path.basename(f))&&!/\.(cjs|py|md)$/.test(f)),[],'no end-card image inside the skill');
for(const f of files.filter(f=>/\.(tmpl|py|js|mjs|cjs|md|sh|json)$/.test(f))){
  const t=fs.readFileSync(f,'utf8');
  assert(!/(?<![\w.-])(assets|board|fixtures|examples)\/[\w-]*(end-?card|ultraman|mebius)[\w-]*\.(jpe?g|png|webp)/i.test(t),`${path.relative(SKILL,f)} points at an end-card image inside the skill`);
}
console.log(`PASS: end card quote picked deterministically from ${pool.length} Ultraman sounds (board and kindle agree); photo only from outside the skill`);
