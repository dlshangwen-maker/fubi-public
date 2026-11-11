"""v9.49：书库改成"找书"（用户 10-27：书库只要搜索 + 热门搜索；我们不存书，读者从搜索结果下载到书架，我们再处理）。改前备份 Demo/模板_v64备份.html。每处替换断言只匹配 1 次。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
p=B+'Demo/模板.html'; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:80]); s=s.replace(a,b)

# 1 整段书库页面换成找书页面
i=s.index("/* ---------- 书库（服务端）"); j=s.index("function shelf(){\n  window.onscroll=null;")
s=s[:i]+r"""/* ---------- 找书（服务端）：只做搜索。搜古登堡计划和维基文库（公版书），读者点"下载到书架"，服务器下载后和导入的书一样处理；我们不存书库 ---------- */
let findQ='', HOT=null, FOUND=null, findSeq=0;
async function findPage(){
  showPage(pageHTML('找书','书架',`<div class="lib"><form class="libsearch" id="libF"><input id="libQ" type="search" placeholder="搜书名或作者" value="${esc(findQ)}" autocomplete="off" enterkeyhint="search"></form><div id="libList"></div></div>`),()=>shelf());
  $('#libF').onsubmit=e=>{ e.preventDefault(); $('#libQ').blur(); runFind($('#libQ').value); };
  $('#libQ').addEventListener('input',()=>{ if(!$('#libQ').value.trim()){ findQ=''; FOUND=null; paintFind(); } });
  if(findQ&&FOUND) paintFind(); else { FOUND=null; paintFind(); }
  if(!HOT){ try{ HOT=(await (await fetch('/api/hot')).json()).hot; }catch(e){ HOT=[]; } if(!findQ) paintFind(); }
}
async function runFind(q){
  q=q.trim(); if(!q) return; findQ=q; $('#libQ').value=q; const my=++findSeq;
  $('#libList').innerHTML='<p class="mini libwait">正在搜索…</p>';
  try{ const r=await fetch('/api/search?q='+encodeURIComponent(q)); const d=await r.json(); if(my!==findSeq) return; if(!r.ok) throw new Error(d.error||'没搜成'); FOUND=d; }
  catch(e){ if(my!==findSeq) return; FOUND={results:[],builtin:[],errors:[e.message||'暂时搜不了']}; }
  paintFind();
}
function paintFind(){
  const el=$('#libList'); if(!el) return;
  if(!findQ||!FOUND){
    el.innerHTML=HOT&&HOT.length?`<h2 class="libh">热门搜索</h2><div class="hotw">${HOT.map(w=>`<button data-hot="${esc(w)}">${esc(w)}</button>`).join('')}</div>`:'';
    el.querySelectorAll('[data-hot]').forEach(b=>b.onclick=()=>runFind(b.dataset.hot)); return;
  }
  const B=FOUND.builtin||[], R=FOUND.results||[];
  let h='';
  if(B.length) h+=B.map(b=>`<div class="librow"><div class="libt"><b>${esc(b['书名'])}</b><span>${esc(authorName(b['作者'],b['国籍']||''))} · 精读版</span><p>${esc(b['简介'])}</p></div><button class="btn ghost" data-open="${esc(b['编号'])}">在书架上</button></div>`).join('');
  h+=R.map(r=>{ const have=SHELF.find(x=>ALL[x[0]]&&ALL[x[0]].meta&&ALL[x[0]].meta.link===r['链接']);
    const act=have?`<button class="btn ghost" data-open="${esc(have[0])}">在书架上</button>`:r['可下载']?`<button class="btn" data-dl="${esc(r['来源'])}|${esc(r['编号'])}">下载到书架</button>`:'';
    const sub=[r['作者']?esc(r['作者']):'',r['语言名']+(r['需翻译']?'（下载后翻译成中文）':''),r['来源']==='gutenberg'?'古登堡计划':'维基文库'].filter(Boolean).join(' · ');
    return `<div class="librow ${r['可下载']?'':'off'}"><div class="libt"><b>${esc(r['中文名']||r['书名'])}</b>${r['中文名']?`<i>${esc(r['书名'])}</i>`:''}<span>${sub}</span>${r['摘要']?`<p>${esc(r['摘要'])}</p>`:''}${r['说明']?`<p class="libwhy">${esc(r['说明'])}</p>`:''}</div>${act}</div>`; }).join('');
  if(!B.length&&!R.length) h=`<p class="libnone">没有找到“${esc(findQ)}”。</p><p class="mini">这里能搜到的是古登堡计划和维基文库里的公版书。手里有这本书的文件，可以回书架“导入自己的书”。</p>`;
  if((FOUND.errors||[]).length) h+=`<p class="mini libwhy">${esc(FOUND.errors.join('，'))}，结果可能不全。</p>`;
  if(R.length) h+=`<p class="mini" style="margin-top:16px">书来自古登堡计划和维基文库，都是公版书；下载的书只在你自己的书架上。</p>`;
  el.innerHTML=h;
  el.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>{ if(ALL[b.dataset.open]) openBook(b.dataset.open); });
  el.querySelectorAll('[data-dl]').forEach(b=>b.onclick=()=>{ const [src,...ref]=b.dataset.dl.split('|'); const r=R.find(x=>x['来源']===src&&x['编号']===ref.join('|')); downloadBook(r,b); });
}
async function downloadBook(r,btn){
  btn.disabled=true; btn.textContent='正在下载…';
  try{
    const res=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:r['来源'],ref:r['编号'],title:r['中文名']||r['书名'],author:r['作者']})}); const j=await res.json();
    if(!res.ok) throw new Error(j.error||'没下载成');
    btn.textContent='正在整理…';
    for(let k=0;k<180;k++){ const st=await (await fetch('/api/books/'+j.id+'/status')).json(); if(st.status!=='parsing'){ if(st.status==='failed') throw new Error(st.err||'这本书整理不了'); break; } await new Promise(z=>setTimeout(z,1000)); }
    const d=await (await fetch('/api/books/'+j.id)).json(); ALL[j.id]=d; addShelfBook(j.id,d);
    btn.className='btn ghost'; btn.textContent='在书架上'; btn.disabled=false; btn.onclick=()=>openBook(j.id);
    toast(`<div class="tq">已下载到书架：《${esc(d.meta.title)}》</div><button>去读</button>`,()=>openBook(j.id),4000);
  }catch(e){ btn.disabled=false; btn.textContent='下载到书架'; toast(`<div class="tq">${esc(e.message)}</div>`,null,5000); }
}
"""+s[j:]
rep("""${SRV?'<button class="linkbtn shlib" id="shLib">书库 ›</button>':''}""","""${SRV?'<button class="linkbtn shlib" id="shLib">找书 ›</button>':''}""")
rep("""  $('#shLib')?.addEventListener('click',()=>libraryPage());""","""  $('#shLib')?.addEventListener('click',()=>findPage());""")

# 2 书的详情：来源写清楚；去掉"书库的书"那套
rep("""  const m=d.meta, g=m.gen||{}, lib=m.kind==='library';""","""  const m=d.meta, g=m.gen||{}, src=m.from==='gutenberg'?'古登堡计划':m.from==='wikisource'?'维基文库':'';""")
rep("""  BOOKS[k]={t:m.title,imported:true,lib,cover:m.cover||'',rows:[['作者',esc(m.author||'（文件里没写）')],...(m.intro?[['简介',esc(m.intro)]]:[]),['来源',lib?'公版书库'+(m.foreign?'，中文由本应用从原文翻译':''):'你导入的文件：'+esc(m.src||'')],""","""  BOOKS[k]={t:m.title,imported:true,cover:m.cover||'',rows:[['作者',esc(m.author||'（文件里没写）')],['来源',src?`从${src}下载（公版）${m.foreign?'，中文由本应用从原文翻译':''}`:'你导入的文件：'+esc(m.src||'')],""")
rep("""['伏笔',(lib?'这本书':'导入的书')+'暂时没有书中伏笔；""","""['伏笔','这本书暂时没有书中伏笔；""")
rep("""  $('#bDel')?.addEventListener('click',async()=>{ const lib=BOOKS[k].lib;
    if(!confirm(lib?'从书架移除这本书？你的划线和想法会保留，以后从书库加回来还在。':'从书架移除这本书？你在这本书里的划线、想法也会一起删除。')) return;
    await fetch('/api/books/'+k,{method:'DELETE'}); if(!lib){ store.set(ALL[k].key,null); syncNow(); }
    SHELF=SHELF.filter(x=>x[0]!==k); if(LIB){ const it=LIB.find(x=>x.book===k); if(it) it['在书架']=false; } closeSheet(); shelf(); });""","""  $('#bDel')?.addEventListener('click',async()=>{
    if(!confirm('从书架移除这本书？你在这本书里的划线、想法也会一起删除。')) return;
    await fetch('/api/books/'+k,{method:'DELETE'}); store.set(ALL[k].key,null); syncNow();
    SHELF=SHELF.filter(x=>x[0]!==k); delete ALL[k]; closeSheet(); shelf(); });""")
# 3 调整章节：读者自己的书都能调（导入的、下载的）
rep("""const CANEDIT=()=>!!(SRV&&D.imported&&D.meta&&D.meta.kind==='import');   /* 只有自己导入的书能调整；书库的书是大家共用的 */""","""const CANEDIT=()=>!!(SRV&&D.imported);   /* 读者自己的书（导入的、找书下载的）都能调整章节；精编书不能 */""")
# 4 样式
rep(""".libnone{font-size:var(--t-body);margin:24px 0 8px}""",""".libnone{font-size:var(--t-body);margin:24px 0 8px}
.libh{font-family:var(--ui);font-size:var(--t-aux);font-weight:400;color:var(--mute);margin:14px 0 10px}
.hotw{display:flex;flex-wrap:wrap;gap:8px}
.hotw button{padding:6px 12px;border-radius:16px;box-shadow:inset 0 0 0 1px var(--line);font-size:var(--t-aux);color:var(--ink)}
.librow.off .libt b{color:var(--mute)}
.libwhy{color:var(--mute);font-size:var(--t-tag)!important}
.libwait{margin-top:18px}""")
open(p,'w',encoding='utf-8').write(s); print('ok')
# 第二轮（截图后手工）：不能下载的原因用浅色；hot.json 中外文交替排
