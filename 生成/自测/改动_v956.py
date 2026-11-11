"""v9.56（10-28）第三阶段 B 书架：顶部"继续阅读"；书格（默认，一行 3 本，只有封面 + 书名）/ 列表 / 简表；排序 最近阅读 / 加入时间 / 书名 / 手动；
"整理"：拖动调整顺序（拖过自动变"手动"），自己的书可多选移除；线装书封面（左侧订线、左上题签）。设置记在 PROF.shelf（不分书）。
备份 Demo/模板_v71备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)

# ---------- bookStat：多给"上次打开时间、百分比、读到哪" ----------
rep("""  const ur=unresolved(), fin=!!S.finished; setBook(keep); return {prog,ur,fin};""",
"""  const where=RD.size&&!S.finished?(NOVEL?`读至${lab(P[Math.min(c,P.length-1)].n)}`:`读至 ${P[Math.min(c,P.length-1)].n}`):'';
  const ur=unresolved(), fin=!!S.finished, last=Math.max(S.lastClose||0,S.lastOpen||0), started=RD.size>0; setBook(keep); return {prog,ur,fin,pct,where,last,started};""")

# ---------- 线装书封面：左侧订线、左上题签（书名竖排）；书自带封面照旧用图 ----------
i=s.index('function coverHTML(title,img){'); j=s.index('\n}\n',i)+3
s=s[:i]+'''function coverHTML(title,img){
  if(img) return `<div class="cover img"><img src="${img}" alt=""></div>`;
  let h=0; [...title].forEach((c,i)=>h+=c.charCodeAt(0)*(i*3+1));
  const n=[...title].length, v=n<=4;   /* 题签：4 个字以内一列，更长的两列小字（类名 v / h 沿用） */
  return `<div class="cover gen ${v?'v':'h'}" style="background:${COVER_C[h%COVER_C.length]}"><span class="ct">${esc(title)}</span></div>`;
}
'''+s[j:]

# ---------- 书架 ----------
i=s.index('function shelf(){'); j=s.index('/* 点一下 = 打开；按住约半秒')
s=s[:i]+r'''/* 书架（规范 v2 第六节 2）：继续阅读 → 标题行（找书 · 导入）→ 工具行（排序 / 三种排列 / 整理）→ 书。
   书格只放封面和书名（用户 10-27：一排横线和红点给人压力）；进度和"N 处伏笔待揭晓"只在列表、书的详情、继续阅读里 */
const SH_SORT=[['recent','最近阅读'],['added','加入时间'],['title','书名'],['manual','手动']];
const SH_LAY={grid:['书格','<path d="M4 4h6v7H4zM14 4h6v7h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>'],list:['列表','<path d="M4 5h4v6H4zM11 6h9M11 9h6M4 14h4v6H4zM11 15h9M11 18h6"/>'],rows:['简表','<path d="M4 6h16M4 12h16M4 18h16"/>']};
const shv=()=>PROF.shelf=Object.assign({lay:'grid',sort:'recent',order:[]},PROF.shelf||{});
let shEdit=false, shMenu=false, shSel=new Set();
function shelfOrder(st){
  const v=shv(), idx=k=>SHELF.findIndex(x=>x[0]===k), L=SHELF.slice();
  if(v.sort==='recent') L.sort((a,b)=>(st[b[0]].last-st[a[0]].last)||idx(a[0])-idx(b[0]));
  else if(v.sort==='added') L.sort((a,b)=>idx(b[0])-idx(a[0]));
  else if(v.sort==='title') L.sort((a,b)=>a[2].localeCompare(b[2],'zh-Hans-CN'));
  else { const o=v.order; L.sort((a,b)=>((o.indexOf(a[0])+1||1e4+idx(a[0]))-(o.indexOf(b[0])+1||1e4+idx(b[0])))); }
  return L;
}
function shelf(){
  window.onscroll=null; closeSheet(); dropBookTips(); lastAct=0; saveProf(true);
  if(S&&S.inBook){S.lastClose=Date.now();S.inBook=false;save();}
  const v=shv(), st=Object.fromEntries(SHELF.map(([k])=>[k,bookStat(k)])), L=shelfOrder(st);
  const fbt=ur=>`${ur.n} 处伏笔待揭晓`;
  const fb=ur=>ur.n?`<div class="fb" role="button" tabindex="0" aria-label="${fbt(ur)}，查看"><span class="dia"></span>${fbt(ur)}</div>`:'';
  const pbar=x=>x.started&&!x.fin?`<span class="pbar"><i style="width:${x.pct}%"></i></span>`:'';
  const cur=SHELF.map(r=>r[0]).filter(k=>st[k].started&&!st[k].fin&&st[k].last).sort((a,b)=>st[b].last-st[a].last)[0];
  const own=k=>!!(BOOKS[k]&&BOOKS[k].imported);
  const item=([k,id,t,au,cn])=>{ const x=st[k], grip=shEdit?`<span class="grip" aria-hidden="true"><i></i><i></i><i></i></span>`:'', sel=shEdit&&own(k)?`<span class="sel ${shSel.has(k)?'on':''}" aria-hidden="true"></span>`:'';
    const pct=x.fin?'读完':x.started?x.pct+'%':'未读';
    if(v.lay==='rows') return `<button class="book lb" id="${id}" data-k="${k}" aria-describedby="${id}p">${sel}<span class="t">${esc(t)}</span><span class="a">${esc(au)}</span><span class="lp" id="${id}p">${pct}</span>${grip}</button>`;
    if(v.lay==='grid') return `<button class="book gb" id="${id}" data-k="${k}" aria-describedby="${id}p">${coverHTML(t,BOOKS[k].cover)}<span class="t">${esc(t)}</span><span class="vh" id="${id}p">${x.prog}</span>${sel}${grip}</button>`;
    return `<button class="book" id="${id}" data-k="${k}" aria-describedby="${id}p">${coverHTML(t,BOOKS[k].cover)}
      <div class="binfo"><div class="t">${esc(t)}</div>${au?`<div class="a">${esc(authorName(au,cn))}</div>`:''}<div class="p" id="${id}p">${x.prog}</div>${pbar(x)}${fb(x.ur)}</div>${sel}${grip}</button>`; };
  const nSel=shSel.size;
  $('#app').innerHTML=`<div class="shelf ${shEdit?'editing':''}">
    <div class="brand" aria-label="伏笔">${LOGO}<b>伏笔</b><button class="shme" id="shMe" aria-label="我的">${avatarHTML(curUser())}</button></div>
    ${cur&&!shEdit?`<button class="cont" id="shCont"><span class="ck">继续阅读</span>${coverHTML(BOOKS[cur].t,BOOKS[cur].cover)}<span class="ci"><span class="t">${esc(BOOKS[cur].t)}</span><span class="p">${st[cur].where}　${st[cur].pct}%</span>${pbar(st[cur])}</span><span class="chev" aria-hidden="true">›</span></button>`:''}
    <div class="shh"><h1>书架</h1>${shEdit?'<span class="shacts"><button class="linkbtn" id="shDone">完成</button></span>':SRV?`<span class="shacts"><button class="linkbtn" id="shLib">找书</button><span class="shdot">·</span><label class="linkbtn" id="impBtn">导入<input type="file" id="impFile" hidden accept="${SRV.formats.map(x=>'.'+x).join(',')}"></label></span>`:''}</div>
    <div class="shtools">${shEdit?`<span class="etip">${SHELF.some(r=>own(r[0]))?'拖动调整顺序；点选自己导入的书可移除':'拖动调整顺序'}</span>`:`<button class="sortb" id="sortB" aria-haspopup="true" aria-expanded="${shMenu}">${SH_SORT.find(x=>x[0]===v.sort)[1]}<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5L6 8l3.5-3.5"/></svg></button>
      ${shMenu?`<div class="shmenu" role="menu">${SH_SORT.map(([k,l])=>`<button role="menuitemradio" aria-checked="${v.sort===k}" data-sort="${k}">${l}</button>`).join('')}</div>`:''}
      <span class="lays">${Object.entries(SH_LAY).map(([k,[l,d]])=>`<button data-lay="${k}" aria-pressed="${v.lay===k}" aria-label="${l}"><svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg></button>`).join('')}<button class="linkbtn" id="shEdit">整理</button></span>`}</div>
    <div class="books lay-${v.lay}" id="bookList">${L.map(item).join('')}</div>
    ${shEdit&&nSel?`<div class="shbar"><span>已选 ${nSel} 本</span><button class="btn ghost danger" id="shDel">移除</button></div>`:''}
    ${importBox()}
    <p class="foot">${SRV?'阅读记录保存在服务器上。':'阅读记录保存在本设备。'}长按书籍可查看详情。</p>
  </div>`;
  wireImport();
  $('#shLib')?.addEventListener('click',()=>findPage());
  $('#shMe').onclick=()=>mePage();
  $('#shCont')?.addEventListener('click',()=>openBook(cur));
  $('#sortB')?.addEventListener('click',e=>{ e.stopPropagation(); shMenu=!shMenu; shelf(); });
  document.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{ v.sort=b.dataset.sort; shMenu=false; saveProf(true); shelf(); });
  if(shMenu) setTimeout(()=>document.addEventListener('click',function off(e){ if(!e.target.closest('.shmenu')){ shMenu=false; document.removeEventListener('click',off); if($('.shmenu')) shelf(); } }),0);
  document.querySelectorAll('[data-lay]').forEach(b=>b.onclick=()=>{ v.lay=b.dataset.lay; saveProf(true); shelf(); });
  $('#shEdit')?.addEventListener('click',()=>{ shEdit=true; shMenu=false; shSel=new Set(); shelf(); });
  $('#shDone')?.addEventListener('click',()=>{ shEdit=false; shSel=new Set(); shelf(); });
  $('#shDel')?.addEventListener('click',async()=>{
    if(!confirm(`从书架移除这 ${shSel.size} 本书？书里的划线、想法也会一起删除。`)) return;
    for(const k of shSel){ try{ await fetch('/api/books/'+k,{method:'DELETE'}); }catch(e){} store.set(ALL[k].key,null); SHELF=SHELF.filter(x=>x[0]!==k); delete ALL[k]; }
    const n=shSel.size; shSel=new Set(); syncNow&&syncNow(); shelf(); toast(`<div class="tq">已移除 ${n} 本。</div>`,null,3000); });
  if(shEdit){ wireShelfDrag(own); return; }
  SHELF.forEach(([k,id])=>{ const el=$('#'+id); if(el) longPress(el,e=>e&&e.target.closest('.fb')?unresolvedSheet(k):openBook(k),()=>bookInfo(k,st[k].prog)); });
  document.querySelectorAll('.book .fb').forEach(f=>f.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();unresolvedSheet(f.closest('.book').dataset.k);}}));
}
/* 整理：按住书拖动换位置（书格左右、列表上下），松手后排序变"手动"；点一下自己导入的书 = 选中 / 取消 */
function wireShelfDrag(own){
  const box=$('#bookList'), v=shv(); let drag=null;
  box.querySelectorAll('.book').forEach(el=>{
    el.addEventListener('pointerdown',e=>{ if(e.button>0) return; drag={el,x:e.clientX,y:e.clientY,moved:false}; el.setPointerCapture(e.pointerId); });
    el.addEventListener('pointermove',e=>{ if(!drag||drag.el!==el) return;
      if(!drag.moved&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<6) return; drag.moved=true; el.classList.add('drag'); e.preventDefault();
      const over=document.elementsFromPoint(e.clientX,e.clientY).map(x=>x.closest&&x.closest('.book')).find(x=>x&&x!==el&&box.contains(x));
      if(over){ const r=over.getBoundingClientRect(), after=v.lay==='grid'?(e.clientX>r.left+r.width/2):(e.clientY>r.top+r.height/2); box.insertBefore(el,after?over.nextSibling:over); } });
    const end=()=>{ if(!drag||drag.el!==el) return; el.classList.remove('drag');
      if(drag.moved){ v.order=[...box.querySelectorAll('.book')].map(x=>x.dataset.k); v.sort='manual'; saveProf(true); }
      else { const k=el.dataset.k; if(own(k)){ shSel.has(k)?shSel.delete(k):shSel.add(k); drag=null; shelf(); return; } }
      drag=null; };
    el.addEventListener('pointerup',end); el.addEventListener('pointercancel',end);
  });
}
'''+s[j:]

CSS=r'''
/* ===== v9.56 书架（规范 v2 第六节 2） ===== */
.shelf{padding:calc(var(--safe-t) + 16px) 24px calc(var(--safe-b) + 32px)}
.brand{margin:0;height:40px;gap:10px}
.brand b{font-size:20px;letter-spacing:.2em}
.brand .logo{width:32px;height:32px}
.shme{margin-left:auto}
.cont{display:grid;grid-template-columns:auto 1fr auto;column-gap:16px;align-items:center;width:100%;margin-top:24px;padding:12px 16px;border-radius:6px;background:var(--paper2);text-align:left}
.cont .ck{grid-column:1/4;font-size:var(--t-tag);color:var(--mute);margin-bottom:12px;line-height:1}
.cont .cover{width:44px}
.cont .ci{display:flex;flex-direction:column;gap:4px;min-width:0}
.cont .t{font-family:var(--serif);font-size:var(--t-key);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cont .p{font-size:var(--t-aux);color:var(--ink2)}
.cont .chev{color:var(--faint);font-size:20px}
.pbar{display:block;height:2px;background:var(--line);border-radius:1px;overflow:hidden;margin-top:4px;max-width:200px}.pbar i{display:block;height:2px;background:var(--ink)}
.shh{margin-top:32px}
.shelf h1{margin:0}
.shtools{position:relative;display:flex;align-items:center;margin-top:12px;height:32px;font-size:var(--t-aux)}
.sortb{display:inline-flex;align-items:center;gap:4px;height:32px;color:var(--ink2)}
.sortb svg{width:10px;height:10px;fill:none;stroke:currentColor;stroke-width:1.4}
.shmenu{position:absolute;z-index:6;top:34px;left:0;min-width:132px;padding:4px;border-radius:6px;background:var(--sheet);box-shadow:0 8px 24px rgba(0,0,0,.14)}
.shmenu button{display:flex;align-items:center;width:100%;height:36px;padding:0 12px;text-align:left;font-size:14px;border-radius:4px}
.shmenu button[aria-checked=true]{color:var(--blue)}.shmenu button[aria-checked=true]::after{content:"✓";margin-left:auto}
.lays{margin-left:auto;display:flex;align-items:center;gap:4px}
.lays button[data-lay]{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:6px;color:var(--faint)}
.lays button[data-lay][aria-pressed=true]{color:var(--ink);background:var(--paper2)}
.lays svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linejoin:round}
.lays #shEdit{margin-left:8px;padding:0;height:32px}
.etip{color:var(--mute)}
.books{margin-top:16px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
/* 线装书封面：左侧订线，左上题签 */
.cover.gen{position:relative;display:block;padding:0;border-radius:2px;box-shadow:inset -1px 0 0 rgba(0,0,0,.15);color:#2A2A2A}
.cover.gen::before{content:"";position:absolute;left:9%;top:9%;bottom:9%;width:2px;background:repeating-linear-gradient(to bottom,rgba(255,255,255,.5) 0 4px,transparent 4px 18px)}
.cover.gen .ct{position:absolute;left:22%;top:9%;width:26%;min-height:48%;max-height:84%;padding:5px 0;background:#F1EEE6;border:1px solid rgba(0,0,0,.08);writing-mode:vertical-rl;font-family:var(--serif);font-weight:400;font-size:12px;line-height:1.6;letter-spacing:.12em;color:#2A2A2A;text-align:center;overflow:hidden;max-width:none}
.cover.gen.h .ct{font-size:10px;line-height:1.35;letter-spacing:0}
.cover.img{border-radius:2px;overflow:hidden}
.cont .cover.gen .ct{font-size:8px;padding:2px 0;line-height:1.5}.cont .cover.gen.h .ct{font-size:7px}
/* 列表 */
.books.lay-list .book{align-items:center;padding:16px 0}
.books.lay-list .cover{width:72px}
.book .binfo{gap:4px}
.book .binfo .p{color:var(--ink2);margin-top:4px}
.binfo .fb{color:var(--hl);font-size:var(--t-aux)}
.binfo .fb .dia{width:6px;height:6px;border-radius:0}
/* 书格：一行 3 本，只有封面 + 书名 */
.books.lay-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px 16px;align-items:start}
.book.gb{position:relative;display:flex;flex-direction:column;align-items:center;gap:8px;padding:0;border:0;min-width:0;text-align:center}
.book.gb .cover{width:100%}
.book.gb .t{width:100%;font-family:var(--serif);font-size:var(--t-aux);line-height:1.4;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.book.gb .cover.gen .ct{font-size:13px}.book.gb .cover.gen.h .ct{font-size:10.5px}
/* 简表：一行一本 */
.book.lb{display:flex;align-items:center;gap:12px;height:48px;padding:0;border-top:0;border-bottom:1px solid var(--line)}
.books.lay-rows .book.lb:first-child{border-top:1px solid var(--line)}
.book.lb .t{font-family:var(--serif);font-size:15px;font-weight:600;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.book.lb .a{font-size:var(--t-aux);color:var(--mute);white-space:nowrap}
.book.lb .lp{min-width:36px;text-align:right;font-size:var(--t-aux);color:var(--ink2);font-variant-numeric:tabular-nums}
/* 整理 */
.grip{display:flex;flex-direction:column;gap:3px;padding:6px;margin-left:8px;cursor:grab;flex:none}.grip i{display:block;width:14px;height:1.5px;background:var(--faint);border-radius:1px}
.book.gb .grip{position:absolute;top:6px;right:6px;margin:0;background:var(--sheet);border-radius:4px}
.editing .book{touch-action:none;cursor:grab}
.editing .book.drag{opacity:.9;box-shadow:0 8px 24px rgba(0,0,0,.18);background:var(--paper);z-index:3}
.editing .book.gb .cover{animation:wig .32s ease-in-out infinite alternate}
@keyframes wig{from{transform:rotate(-.6deg)}to{transform:rotate(.6deg)}}
.sel{flex:none;width:20px;height:20px;border-radius:50%;box-shadow:inset 0 0 0 1.5px var(--faint);margin-left:8px;position:relative}
.sel.on{background:var(--ink);box-shadow:none}.sel.on::after{content:"";position:absolute;left:7px;top:4px;width:5px;height:9px;border:solid var(--paper);border-width:0 2px 2px 0;transform:rotate(45deg)}
.book.gb .sel{position:absolute;top:6px;left:6px;margin:0;background:var(--sheet)}.book.gb .sel.on{background:var(--ink)}
.shbar{position:sticky;bottom:calc(var(--safe-b) + 12px);display:flex;align-items:center;gap:12px;margin-top:24px;padding:8px 8px 8px 16px;border-radius:6px;background:var(--sheet);box-shadow:0 0 0 1px var(--line);font-size:var(--t-aux)}
.shbar .btn{margin-left:auto}
.shelf .foot{margin-top:32px}
@media (prefers-reduced-motion:reduce){.editing .book.gb .cover{animation:none}}
/* 横屏：书格一行 6 本，列表和简表两栏 */
@media (orientation:landscape) and (min-width:700px){
  .app:has(.shelf){max-width:960px}
  .shelf{padding-left:calc(var(--safe-l,0px) + 24px);padding-right:calc(var(--safe-r,0px) + 24px)}
  .books.lay-grid{grid-template-columns:repeat(6,minmax(0,1fr))}
  .books.lay-list,.books.lay-rows{display:grid;grid-template-columns:1fr 1fr;column-gap:40px}
  .books.lay-rows .book.lb:nth-child(2){border-top:1px solid var(--line)}
}
'''
rep('</style>',CSS+'</style>')
rep('  --safe-b:env(safe-area-inset-bottom,0px); --safe-t:env(safe-area-inset-top,0px);','  --safe-b:env(safe-area-inset-bottom,0px); --safe-t:env(safe-area-inset-top,0px); --safe-l:env(safe-area-inset-left,0px); --safe-r:env(safe-area-inset-right,0px);')
# 测试钩子
rep("if(window.__TEST) setTimeout(()=>window.__TEST({","if(window.__TEST) setTimeout(()=>window.__TEST({shv,shelfOrder,setShEdit:x=>{shEdit=x;shSel=new Set();},")
open(P,'w',encoding='utf-8').write(s); print('ok')
