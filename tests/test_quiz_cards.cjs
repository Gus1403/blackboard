const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../board/board.html.tmpl'),'utf8');
const a=source.indexOf('function container(raw)'),b=source.indexOf('\nfunction ',a+10);
const context={md:s=>s,mdInline:s=>s,esc:s=>s};vm.createContext(context);vm.runInContext(source.slice(a,b),context);
const container=context.container;
for(const n of [3,4,8]){const raw='::: mcq test '+ 'abcdefgh'[n-1]+'\nQuestion\n'+Array.from({length:n},(_,i)=>'- Option '+i).join('\n')+'\nwhy: Explanation\n:::';const html=container(raw);assert.equal((html.match(/type="radio"/g)||[]).length,n);assert.equal((html.match(/answer-icon/g)||[]).length,n);assert(html.includes('value="'+'abcdefgh'[n-1]+'"'));assert(html.includes('role="radiogroup"'));assert(!html.includes('undefined'));if(n>=4)assert(html.includes('■'));}console.log('PASS: card rendering, shapes, option keys and radio groups for 3/4/8 choices');
