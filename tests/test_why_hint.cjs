// \why{math}{rule}: the math renders with a hint index, the rule is kept aside, every plain-text view sees the math only.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const a=source.indexOf('const WHY_RULES='), b=source.indexOf('function mathify(src)');
let rendered=[];
const ctx={katex:{renderToString:(t,o)=>{rendered.push({t,o});return `<span class="katex"><annotation encoding="application/x-tex">${t}</annotation>${t}</span>`;}},esc:s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;')};
vm.createContext(ctx); vm.runInContext(source.slice(a,b).replace(/^const /gm,'var '),ctx);
const tex=String.raw`du = \why{5\,dx}{\tfrac{d}{dx}(kx) = k},\ v = \why[Table row]{\tfrac{1}{3}\tan(3x)}{\int\sec^{2}(ax)\,dx = \tfrac{1}{a}\tan(ax)}`;
assert.equal(ctx.stripWhy(tex),String.raw`du = 5\,dx,\ v = \tfrac{1}{3}\tan(3x)`,'stripping leaves the plain math');
const html=ctx.ktx(tex,false);
assert.match(rendered[0].t,/\\htmlData\{why=0\}\{5\\,dx\}/,'the math carries the rule index');
assert.match(rendered[0].t,/\\htmlData\{why=1\}\{\\tfrac\{1\}\{3\}\\tan\(3x\)\}/);
assert(rendered[0].o.trust({command:'\\htmlData'})&&!rendered[0].o.trust({command:'\\href'}),'trust is limited to htmlClass/htmlData');
assert.equal(ctx.WHY_RULES[0].rule,String.raw`\tfrac{d}{dx}(kx) = k`);
assert.equal(ctx.WHY_RULES[1].name,'Table row');
assert(html.includes(String.raw`<annotation encoding="application/x-tex">du = 5\,dx,\ v = \tfrac{1}{3}\tan(3x)</annotation>`),'copy / Explain read the plain math');
assert.equal(ctx.stripWhy(String.raw`\whyever{x}`),String.raw`\whyever{x}`,'a longer command name is left alone');
// popup: opens on click / Enter, a second tap or Esc or an outside click closes it, one at a time
for(const s of ["if(whyAt===el){ whyHide(); return; }","if(e.key==='Escape'&&whyAt)","if(whyAt&&!whyPop.contains(e.target))whyHide();","whyHide(); hideDefine(); whyAt=el;","(e.key==='Enter'||e.key===' ')"])assert(source.includes(s),s);
// lint, search and kindle strip the hint
assert(fs.readFileSync(path.join(__dirname,'../bin/lint.py'),'utf8').includes('s = strip_why(open('));
assert(fs.readFileSync(path.join(__dirname,'../board/bridge.py'),'utf8').includes('strip_why(line)'));
console.log('PASS: \\why renders the math with a rule index, keeps the rule aside, strips cleanly; popup open/close wired');
