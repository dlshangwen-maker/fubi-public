"""v9.60（10-28）第三阶段收尾（用户："都做好"）：
① 横屏右侧批注栏（规范 v2 第六节 3）：最上面主线（问题 + 拼图格），下面按顺序列出这一屏附近的伏笔（朱）、想法和疑问（黛），点一下打开对应面板；随正文滚动更新。竖屏不显示。
② 双击段落 = 打开解释（单击仍然可用）；双击不留下选中的文字。
③ 全局撤销（规范 v2 第七节）：从书架移除书（单本、整理多选）、删除笔记编辑页里的记录，都不再弹系统确认框，改成"已移除 · 撤销"，5 秒后才真正删除。
备份 Demo/模板_v75备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)

# ---------- ③ 撤销：移除书 ----------
rep("""  $('#bDel')?.addEventListener('click',async()=>{
    if(!confirm('从书架移除这本书？你在这本书里的划线、想法也会一起删除。')) return;
    await fetch('/api/books/'+k,{method:'DELETE'}); store.set(ALL[k].key,null); syncNow();
    SHELF=SHELF.filter(x=>x[0]!==k); delete ALL[k]; closeSheet(); shelf(); });""",
"""  $('#bDel')?.addEventListener('click',()=>{ closeSheet(); removeBooks([k]); });""")
rep("""  $('#shDel')?.addEventListener('click',async()=>{
    if(!confirm(`从书架移除这 ${shSel.size} 本书？书里的划线、想法也会一起删除。`)) return;
    for(const k of shSel){ try{ await fetch('/api/books/'+k,{method:'DELETE'}); }catch(e){} store.set(ALL[k].key,null); SHELF=SHELF.filter(x=>x[0]!==k); delete ALL[k]; }
    const n=shSel.size; shSel=new Set(); syncNow&&syncNow(); shelf(); toast(`<div class="tq">已移除 ${n} 本。</div>`,null,3000); });""",
"""  $('#shDel')?.addEventListener('click',()=>{ const ks=[...shSel]; shSel=new Set(); removeBooks(ks); });""")
rep("/* 整理：按住书拖动换位置","""/* 移除书（规范 v2：操作后可撤销）：先从书架拿下来，提示条"撤销"；5 秒后才真正删除（服务器上的书、这本书的划线和想法） */
function removeBooks(ks){
  const rows=SHELF.filter(x=>ks.includes(x[0])); if(!rows.length) return;
  SHELF=SHELF.filter(x=>!ks.includes(x[0])); shelf();
  let undone=false; clearTimeout(removeBooks.t);
  toast(`<div class="tq">已移除${rows.length>1?` ${rows.length} 本`:'《'+esc(rows[0][2])+'》'}</div><button>撤销</button>`,()=>{ undone=true; clearTimeout(removeBooks.t); rows.forEach(r=>{ if(!SHELF.some(x=>x[0]===r[0])) SHELF.push(r); }); shelf(); },5000);
  removeBooks.t=setTimeout(async()=>{ if(undone) return;
    for(const k of ks){ try{ await fetch('/api/books/'+k,{method:'DELETE'}); }catch(e){} if(ALL[k]) store.set(ALL[k].key,null); delete ALL[k]; }
    try{ syncNow(); }catch(e){} },5200);
}
/* 整理：按住书拖动换位置""")
# ---------- ③ 撤销：笔记编辑页的"删除" ----------
rep("""  $('#cdel').onclick=()=>{if(!confirm('确定删除这条记录？原文上的线会一起删除。'))return; S.notes=S.notes.filter(n=>n.id!==ed.id); if(ed.hl) S.ul=S.ul.filter(u=>u.id!==ed.hl); ed.hl=null; after();};""",
"""  $('#cdel').onclick=()=>{ const ul=ed.hl&&S.ul.find(u=>u.id===ed.hl), hl0=ed.hl; S.notes=S.notes.filter(n=>n.id!==ed.id); if(ul) S.ul=S.ul.filter(u=>u!==ul); after();
    toast(`<div class="tq">已删除</div><button>撤销</button>`,()=>{ ed.hl=hl0; S.notes.push(ed); if(ul) S.ul.push(ul); save(); paintUL(); paintMarks(); },4000); };""")

# ---------- ② 双击段落开解释 ----------
rep("""  els.forEach(e=>{e.onkeydown=ev=>{if(ev.key==='Enter'&&ev.target===e)openCard(+e.dataset.i)}});""",
"""  els.forEach(e=>{e.onkeydown=ev=>{if(ev.key==='Enter'&&ev.target===e)openCard(+e.dataset.i)}});
  /* 双击段落 = 打开解释（规范 v2 第七节；单击仍然可用）。双击不留下选中的文字 */
  $('#text').addEventListener('dblclick',e=>{ const p=e.target.closest('.prop'); if(!p||e.target.closest('.mk,.pn,mark,.dochd,button')) return;
    try{ getSelection().removeAllRanges(); }catch(_){} hideMenu(); openCard(+p.dataset.i); });""")

# ---------- ① 横屏批注栏 ----------
rep("""  h+=`<div class="endmark" id="endMark">${endHTML()}</div></div>""","""  h+=`<div class="endmark" id="endMark">${endHTML()}</div></div><aside class="side" id="side" aria-label="批注"></aside>""")
rep("""    $('#bar')?.classList.toggle('scrolled',scrollY>4); tickRead(); chromeTick(); lastLineTick();""",
"""    $('#bar')?.classList.toggle('scrolled',scrollY>4); tickRead(); chromeTick(); lastLineTick(); sideTick();""")
rep("function paintDots(){","""/* 横屏右侧批注栏：主线 + 这一屏附近（前后各约一屏）的伏笔、想法、疑问，按书里的先后排。竖屏时整栏隐藏（CSS），不计算 */
const sideOn=()=>matchMedia('(orientation:landscape) and (max-height:520px)').matches;
let sideKey='';
function sideTick(force){
  const el=$('#side'); if(!el||!sideOn()) return;
  const a=Math.max(0,(S.current>=0?S.current:0)-3), b=Math.min(P.length-1,Math.max(S.vis??-1,S.current??-1,0)+3);   /* 刚打开书时 vis 还没算出来，用当前位置 */
  const clues=reachedClues().filter(x=>{ const p=posOf(x['提出']); return p>=a-12&&p<=b; }).map(x=>({p:posOf(x['提出']),h:`<button class="pz ${S.doneS[x.id]?'done':''}" data-sc="${x.id}"><small>${S.doneS[x.id]?'已揭晓':'伏笔'}　${esc(label(posOf(x['提出'])))}</small>${esc(x['问题'])}</button>`}));
  const notes=S.notes.filter(n=>n.at>=a-12&&n.at<=b).map(n=>({p:n.at,h:`<button class="pz d" data-sn="${n.id}"><small>${n.type==='note'?'我的想法':isFb(n)?'我发现的伏笔':'我的疑问'}　${esc(label(n.at))}</small>${esc(firstLine(n.text,60))}</button>`}));
  const L=[...clues,...notes].sort((x,y)=>x.p-y.p);
  const key=a+'|'+b+'|'+L.map(x=>x.h.length).join(',')+'|'+Object.keys(S.doneS).length;
  if(!force&&key===sideKey) return; sideKey=key;
  el.innerHTML=`${ML()?mainHTML(false):''}${L.length?L.map(x=>x.h).join(''):'<p class="sidee">这一屏附近没有批注。</p>'}`;
  el.querySelectorAll('[data-sc]').forEach(x=>x.onclick=()=>{ const id=x.dataset.sc; S.doneS[id]?reveal(id):openClue(id); });
  el.querySelectorAll('[data-sn]').forEach(x=>x.onclick=()=>noteSheet(+x.dataset.sn));
}
addEventListener('resize',()=>{ sideKey=''; sideTick(true); });
function paintDots(){""")
rep("""  paintDots();
  reachedClues().forEach(s=>{""","""  paintDots(); sideKey=''; setTimeout(()=>sideTick(true),0);
  reachedClues().forEach(s=>{""")

CSS=r'''
/* ===== v9.60 横屏右侧批注栏（规范 v2 第六节 3） ===== */
.side{display:none}
@media (orientation:landscape) and (max-height:520px){
  .side{display:block;position:fixed;z-index:15;top:44px;right:0;bottom:0;width:calc(220px + var(--safe-r));padding:16px calc(20px + var(--safe-r)) calc(16px + var(--safe-b)) 20px;border-left:1px solid var(--line);background:var(--paper);overflow-y:auto;font-family:var(--ui);scrollbar-width:none;transition:top .28s var(--ease)}
  .side::-webkit-scrollbar{display:none}
  .calmread .side{top:0}
  .text{margin-right:calc(220px + var(--safe-r));margin-left:0;max-width:none;padding-right:calc(var(--pad) + 32px)}
  .text>*{max-width:28em;margin-left:auto;margin-right:auto}
  .side .mainl{margin:0 0 16px;padding:0 0 16px;background:none;border-radius:0;border-bottom:1px solid var(--line)}
  .side .mlq{font-size:13px;line-height:1.7;margin:8px 0 10px}
  .side .mlp i{width:14px;height:14px}
  .side .mlnotes{display:none}
  .pz{display:block;width:100%;margin:0 0 16px;padding:0 0 0 12px;border-left:2px solid var(--hl);font-family:var(--kai);font-size:14px;line-height:1.7;color:var(--hl);text-align:left}
  .pz small{display:block;font-family:var(--ui);font-size:var(--t-tag);color:var(--mute);margin-bottom:2px;letter-spacing:.02em}
  .pz.done{opacity:.6}
  .pz.d{border-left-color:var(--blue);color:var(--blue)}
  .sidee{font-size:var(--t-aux);color:var(--faint);line-height:1.7;margin:0}
}
'''
rep('</style>',CSS+'</style>')
rep("if(window.__TEST) setTimeout(()=>window.__TEST({","if(window.__TEST) setTimeout(()=>window.__TEST({removeBooks,sideTick,")
open(P,'w',encoding='utf-8').write(s); print('ok')
