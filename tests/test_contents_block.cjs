const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const a=source.indexOf('function container(raw)'),b=source.indexOf('\nfunction ',a+10);
const context={md:s=>s,mdInline:s=>s,esc:s=>s};vm.createContext(context);vm.runInContext(source.slice(a,b),context);
const list='1. [Chapter 1 · Parts](#s-chapter-1-parts) · pick u.\n2. [Chapter 2 · Trig](#s-chapter-2-trig) · the cases.';
const html=context.container('::: contents\n'+list+'\n:::');
assert.match(html,/^<details class="prerequisites contents"><summary>Contents<\/summary><div>/);
assert(!/<details[^>]*\bopen\b/.test(html),'Contents starts collapsed');
assert(html.includes('#s-chapter-1-parts')&&html.includes('#s-chapter-2-trig'),'chapter links kept');
// old lessons: a bold **Contents** line over a list renders as the same drop-down
const r=source.indexOf('function renderSegment(seg)');assert(r>0);
assert(source.slice(r,r+900).includes("\\*\\*Contents\\*\\*"),'renderSegment converts the old bold Contents line');
// a hash link into a closed drop-down opens it
assert(source.includes("const d=t.closest('details'); if(d) d.open=true;"));
console.log('PASS: ::: contents renders as a collapsed drop-down like Prerequisites; old **Contents** lists convert; hash targets open it');
