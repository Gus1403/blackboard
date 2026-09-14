// Before/after T-accounts for lesson 0001, chalk look via Rough.js. Emits SVG on stdout.
import rough from 'roughjs/bundled/rough.esm.js';
const FONT = process.argv[2] || "'Crimson Pro', Georgia, serif";
const CH='#e9e6df', ACC='#9b3a4a', DIM='#8a8a84';
const g = rough.generator();
const o = {stroke:CH, strokeWidth:1.8, roughness:1.3, bowing:1.1, seed:11};
const out=[];
const P=d=>g.toPaths(d).forEach(p=>out.push(`<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill||'none'}" stroke-linecap="round" stroke-linejoin="round"/>`));
const T=(x,y,s,a='start',f=CH,sz=20,extra='')=>out.push(`<text x="${x}" y="${y}" font-family="${FONT}" font-size="${sz}" fill="${f}" text-anchor="${a}" ${extra}>${s}</text>`);
const money=n=>'$'+n.toLocaleString();
function tacc(x,y,title,left,right,hi=[]){
  const w=300,h=150,m=x+w/2,row=32,top=y+26;
  T(m,y,title,'middle',CH,24);
  P(g.line(x,top,x+w,top,o)); P(g.line(m,top,m,top+h,o));
  T(x+w/4,top+22,'owns / is owed','middle',DIM,15); T(x+3*w/4,top+22,'owes','middle',DIM,15);
  const col=(items,x0,x1)=>items.forEach(([l,v],i)=>{const f=hi.includes(l)?ACC:CH;T(x0,top+58+row*i,l,'start',f);T(x1,top+58+row*i,money(v),'end',f);});
  col(left,x+10,m-12); col(right,m+12,x+w-10);
  const sum=a=>a.reduce((s,r)=>s+r[1],0);
  P(g.line(x+10,top+h-14,m-12,top+h-14,o)); P(g.line(m+12,top+h-14,x+w-10,top+h-14,o));
  T(m-12,top+h+10,money(sum(left)),'end',DIM,18); T(x+w-10,top+h+10,money(sum(right)),'end',DIM,18);
}
tacc(20,30,'Before the loan',[['Cash',110]],[['Deposits',100],['Owners',10]]);
tacc(400,30,'After the loan',[['Cash',110],['Loan',80]],[['Deposits',180],['Owners',10]],['Loan','Deposits']);
// arrow
P(g.line(330,120,390,120,{...o,stroke:ACC,strokeWidth:2.2}));
P(g.polygon([[392,120],[380,113],[380,127]],{...o,stroke:ACC,fill:ACC,fillStyle:'solid'}));
T(360,105,'+$80 both sides','middle',ACC,15);
console.log(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" width="720" height="230">${out.join('')}</svg>`);
