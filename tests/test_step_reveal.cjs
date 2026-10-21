// Step-by-step reveal: a worked solution starts at one step, Next step adds the next one, Show all opens everything.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const grab=name=>{const a=source.indexOf('function '+name+'(');assert(a>0,name);const b=source.indexOf('\nfunction ',a+10);return source.slice(a,b);};
const ctx={rvRows:(el,max)=>{el.max=max;},rvFade:()=>{},rvCtl:()=>{}};vm.createContext(ctx);
for(const f of ['stepPlan','rvApply','rvGo'])vm.runInContext(grab(f),ctx);
// a fake element with a class list
const el=()=>{const c=new Set();return {classList:{toggle:(k,on)=>on?c.add(k):c.delete(k),contains:k=>c.has(k)},dataset:{}};};
// lead sentence, boxed setup grid, a 4-row derivation, a trailing sentence
const items=[{kind:'prose',el:el()},{kind:'math',el:el()},{kind:'rows',n:4,el:el()},{kind:'prose',el:el()}];
const plan=ctx.stepPlan(items);
assert.equal(plan.steps.length,5,'grid + 4 rows = 5 steps');
assert.equal(JSON.stringify(plan.lead.map(e=>e.i)),"[0]",'the lead sentence is always shown');
assert(plan.steps[4].some(e=>e.i===3),'trailing prose arrives with the last step');
const box={_rv:{items,plan,k:1}};
const on=i=>!items[i].el.classList.contains('rv-off');
ctx.rvApply(box,false);
assert(on(0)&&on(1)&&!on(2)&&!on(3),'starts at one step: lead + setup grid');
ctx.rvGo(box,2); assert(on(2)&&items[2].el.max===0&&!on(3),'Next step reveals row 1 of the derivation');
ctx.rvGo(box,3); assert.equal(items[2].el.max,1,'then row 2');
ctx.rvGo(box,plan.steps.length); assert(on(3)&&items[2].el.max===3,'Show all reveals everything');
ctx.rvGo(box,0); assert(on(0)&&!on(1),'a wrong pick starts at zero steps: hint only');
// no derivation, nothing to step
assert.equal(ctx.stepPlan([{kind:'prose'}]).steps.length,0);
// wiring: check-in answers step when opened, mcq feedback steps, re-fit math keeps the state
assert(source.includes("if(box._rv)rvApply(box,false); else rvSetup(box,1);"));
assert(source.includes("rvSetup(fbb,ok?1:0)"));
assert(/fitMath\); rvReapply\(\);/.test(source));
assert(source.includes('@media print{.rv .rv-off{display:revert!important}'),'print shows every step');
console.log('PASS: step reveal starts at one step, Next adds one row, Show all opens all, wrong picks start at the hint');
