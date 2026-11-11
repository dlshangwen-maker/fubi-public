"""v9.48：书库页面 + 搜索、导入书封面、导入书手动调整分章（只在服务端模式出现）。每处替换断言只匹配 1 次。改前备份 Demo/模板_v63备份.html"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
p=B+'Demo/模板.html'; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:80]); s=s.replace(a,b)

# ---------- 1 书库：书架标题行右边"书库"入口（服务端才有）；整页书库 ----------
rep("""    <h1>书架</h1><p class="lede">点击继续阅读，长按查看书籍信息。</p>""","""    <div class="shh"><h1>书架</h1>${SRV?'<button class="linkbtn shlib" id="shLib">书库 ›</button>':''}</div><p class="lede">点击继续阅读，长按查看书籍信息。</p>""")
rep("""  wireImport();
  $('#shMe').onclick=()=>mePage();""","""  wireImport();
  $('#shLib')?.addEventListener('click',()=>libraryPage());
  $('#shMe').onclick=()=>mePage();""")
rep("""function shelf(){
  window.onscroll=null;""","""/* ---------- 书库（服务端）：精编书 + 公版书单，按书名/作者搜；书库的书"加入书架"后才在书架上 ---------- */
let LIB=null, libQ='';
async function libraryPage(){
  showPage(pageHTML('书库','书架',`<div class="lib"><label class="libsearch"><input id="libQ" type="search" placeholder="搜书名、作者" value="${esc(libQ)}" autocomplete="off" enterkeyhint="search"></label><div id="libList"><p class="mini">正在打开书库…</p></div></div>`),()=>shelf());
  const q=$('#libQ'); let tm=0;
  q.addEventListener('input',()=>{ clearTimeout(tm); tm=setTimeout(()=>{ libQ=q.value.trim(); paintLib(); },200); });
  try{ if(!LIB){ const r=await fetch('/api/library'); LIB=(await r.json()).books; } }catch(e){ $('#libList').innerHTML='<p class="mini">书库暂时打不开，请稍后再试。</p>'; return; }
  paintLib();
}
const libNorm=s=>String(s||'').toLowerCase().replace(/[\\s·・.\\-—_，,、：:（）()《》“”"']+/g,'');
function paintLib(){
  const el=$('#libList'); if(!el||!LIB) return;
  const nq=libNorm(libQ), hit=LIB.filter(b=>!nq||['书名','作者','原名'].some(k=>libNorm(b[k]).includes(nq)));
  if(!hit.length){ el.innerHTML=`<p class="libnone">书库里没有找到“${esc(libQ)}”。</p><p class="mini">书库只收作者去世满 50 年的公版书。手里有这本书的文件，可以在书架上“导入自己的书”。</p>`; return; }
  const GR=[['精编','精读版','有伏笔、主线和逐段解释'],['中文','中文公版书',''],['外文','外文公版书','由本应用从原文翻译']];
  el.innerHTML=GR.map(([g,t,sub])=>{ const L=hit.filter(b=>b['组']===g); if(!L.length) return '';
    return `<section class="libg"><h2>${t}${sub?`<small>${sub}</small>`:''}</h2>${L.map(libRow).join('')}</section>`; }).join('');
  el.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>libAdd(b.dataset.add,b));
  el.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>{ if(ALL[b.dataset.open]) openBook(b.dataset.open); });
}
function libRow(b){
  const au=b['作者']?esc(authorName(b['作者'],b['国籍']||'')):'';
  const act=b['组']==='精编'||b['在书架']?`<button class="btn ghost" data-open="${esc(b.book)}">${b['组']==='精编'?'阅读':'在书架上'}</button>`
    :b.book&&b['状态']==='ready'?`<button class="btn" data-add="${esc(b.book)}">加入书架</button>`:`<span class="libsoon">即将上架</span>`;
  return `<div class="librow"><div class="libt"><b>${esc(b['书名'])}</b>${b['原名']?`<i>${esc(b['原名'])}</i>`:''}<span>${au}</span>${b['简介']?`<p>${esc(b['简介'])}</p>`:''}</div>${act}</div>`;
}
async function libAdd(bid,btn){
  btn.disabled=true; btn.textContent='正在加入…';
  try{ const r=await fetch('/api/shelf/'+bid,{method:'POST'}); const d=await r.json(); if(!r.ok) throw new Error(d.error||'没加上');
    ALL[bid]=d; addShelfBook(bid,d); const it=LIB.find(x=>x.book===bid); if(it) it['在书架']=true; paintLib();
    toast(`<div class="tq">已加入书架：《${esc(d.meta.title)}》</div><button>去读</button>`,()=>openBook(bid),4000);
  }catch(e){ btn.disabled=false; btn.textContent='加入书架'; toast(`<div class="tq">${esc(e.message)}</div>`); }
}
function shelf(){
  window.onscroll=null;""")
# 书架接上书库/导入的书：抽成函数（加入书架时也用）
rep("""if(SRV){ Object.entries(ALL).forEach(([k,d],n)=>{ if(!d.meta) return; SHELF.push([k,'bi'+n,d.meta.title,d.meta.author||'',d.meta.nat||'']);
  const m=d.meta, g=m.gen||{}; BOOKS[k]={t:m.title,imported:true,cover:m.cover||'',rows:[['作者',esc(m.author||'（文件里没写）')],['来源',m.kind==='library'?'公版书库':'你导入的文件：'+esc(m.src||'')],""","""function addShelfBook(k,d){ if(SHELF.some(x=>x[0]===k)) return; SHELF.push([k,'bi'+SHELF.length,d.meta.title,d.meta.author||'',d.meta.nat||'']);
  const m=d.meta, g=m.gen||{}, lib=m.kind==='library';
  const genT=m.foreign&&d.untranslated?(g.total?`正在翻译（${g.done} / ${g.total}）`:'还没有翻译（需要服务器配置模型）'):g.total?(g.done>=g.total?'已生成':`正在生成（${g.done} / ${g.total}）`):'还没有生成（需要服务器配置模型）';
  BOOKS[k]={t:m.title,imported:true,lib,cover:m.cover||'',rows:[['作者',esc(m.author||'（文件里没写）')],...(m.intro?[['简介',esc(m.intro)]]:[]),['来源',lib?'公版书库'+(m.foreign?'，中文由本应用从原文翻译':''):'你导入的文件：'+esc(m.src||'')],""")
rep("""['伏笔','导入的书暂时没有书中伏笔；可以自己划线提问，记成"我发现的伏笔"']]}; }); }""","""['伏笔',(lib?'这本书':'导入的书')+'暂时没有书中伏笔；可以自己划线提问，记成"我发现的伏笔"']]}; }
if(SRV) Object.entries(ALL).forEach(([k,d])=>{ if(d.meta) addShelfBook(k,d); });""")
rep("""['解释与回顾',g.total?(g.done>=g.total?'已生成':`正在生成（${g.done} / ${g.total}）`):'还没有生成（需要服务器配置模型）'],""","""[m.foreign&&d.untranslated?'中文':'解释与回顾',genT],""")
# 书库的书：从书架移除不删记录
rep("""  $('#bDel')?.addEventListener('click',async()=>{ if(!confirm('从书架移除这本书？你在这本书里的划线、想法也会一起删除。')) return; await fetch('/api/books/'+k,{method:'DELETE'}); store.set(ALL[k].key,null); syncNow(); location.reload(); });""","""  $('#bDel')?.addEventListener('click',async()=>{ const lib=BOOKS[k].lib;
    if(!confirm(lib?'从书架移除这本书？你的划线和想法会保留，以后从书库加回来还在。':'从书架移除这本书？你在这本书里的划线、想法也会一起删除。')) return;
    await fetch('/api/books/'+k,{method:'DELETE'}); if(!lib){ store.set(ALL[k].key,null); syncNow(); }
    SHELF=SHELF.filter(x=>x[0]!==k); if(LIB){ const it=LIB.find(x=>x.book===k); if(it) it['在书架']=false; } closeSheet(); shelf(); });""")

# ---------- 2 外文书还没翻译：书里显示原文，顶部一句说明 ----------
# （阅读器照常显示 zh 字段——服务端在没译完时 zh 就是原文）

# ---------- 3 手动调整分章（导入的书、书库的书）：阅读设置里"调整章节" ----------
rep("""    <div class="setrow inline"><div class="lbl"><span>清空本书记录</span></div><button class="btn ghost" id="rs">清空</button></div>""","""    ${SRV&&D.imported?`<div class="setrow inline"><div class="lbl" style="display:block"><span>调整章节</span><br><small>改章名、拆分或合并章节</small></div><button class="btn ghost" id="chEdit">调整</button></div>`:''}
    <div class="setrow inline"><div class="lbl"><span>清空本书记录</span></div><button class="btn ghost" id="rs">清空</button></div>""")
rep("""  $('#rs').onclick=()=>{""","""  $('#chEdit')?.addEventListener('click',()=>chapterEditor());
  $('#rs').onclick=()=>{""")
rep("""/* ---------- 书库（服务端）""","""/* ---------- 调整章节（导入的书）：章名可改；"和上一章合并"；点某一段"从这里分出新的一章"。改完服务器重排，已经生成的解释和回顾跟着走 ---------- */
let chOps=[];
function chapterEditor(split){
  chOps=chOps||[];
  const U=HUI.map((h,k)=>({n:h.n,t:h.t,first:h.first,end:(HUI[k+1]||{first:P.length}).first}));
  openSheet(`<div class="shead"><span class="ttl">调整章节</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody"><p class="mini" style="margin:0 0 10px">改完点“保存”。要在某一段前分出新的一章：先关掉这里，长按那一段，选“从这里分章”。</p>
    ${U.map((u,k)=>`<div class="chrow" data-n="${u.n}"><input class="chname" value="${esc(u.t)}" aria-label="第 ${k+1} 章章名"><small>${u.end-u.first} 段 · ${esc(firstLine(P[u.first].zh,14))}</small>${k?`<button class="linkbtn" data-merge="${u.n}">并入上一章</button>`:''}</div>`).join('')}
  </div><div class="sfoot"><button class="btn ghost" data-close>取消</button><button class="btn" id="chSave" style="margin-left:auto">保存</button></div>`,{tall:true});
  document.querySelectorAll('#sheet [data-merge]').forEach(b=>b.onclick=()=>{ const row=b.closest('.chrow'); row.classList.toggle('merged'); b.textContent=row.classList.contains('merged')?'取消合并':'并入上一章'; });
  $('#chSave').onclick=async()=>{
    const ops=[];
    document.querySelectorAll('#sheet .chrow').forEach(r=>{ const n=+r.dataset.n, h=HUI.find(x=>x.n===n), v=r.querySelector('.chname').value.trim();
      if(r.classList.contains('merged')) ops.push({op:'merge',ch:n}); else if(v&&v!==h.t) ops.push({op:'rename',ch:n,title:v}); });
    if(!ops.length){ closeSheet(); return; }
    await saveChapters(ops);
  };
}
async function saveChapters(ops){
  try{ const r=await fetch('/api/books/'+BK+'/chapters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ops})}); const d=await r.json();
    if(!r.ok) throw new Error(d.error||'没保存上');
    const keep=S.current>=0?P[S.current].n:null; /* 段的顺序不变，只是章号变了：按"第几段"对回去 */
    ALL[BK]=d; setBook(BK); closeSheet(); reader(false); toast(`<div class="tq">章节已调整。${d.meta&&d.meta.gen&&d.meta.gen.todo?'改动的章节会重新生成解释。':''}</div>`,null,3000);
  }catch(e){ toast(`<div class="tq">${esc(e.message)}</div>`); }
}
/* ---------- 书库（服务端）""")
# 长按某一段：服务端导入的书多一个"从这里分章"
rep("""/* ---------- 书库（服务端）""","""function splitHere(i){
  const h=huiOf(i); if(h.first===i){ toast('<div class="tq">这一段已经是一章的开头。</div>',null,2500); return; }
  const t=prompt('新一章的章名',firstLine(P[i].zh,12)); if(t===null) return;
  saveChapters([{op:'split',at:P[i].n,title:t.trim()||firstLine(P[i].zh,12)}]);
}
/* ---------- 书库（服务端）""")

# ---------- 4 样式 ----------
rep(""".impbox{margin-top:0;""",""".shh{display:flex;align-items:baseline;gap:12px}.shh .shlib{margin-left:auto;font-size:var(--t-aux)}
.lib{font-family:var(--ui)}
.libsearch{display:block;position:sticky;top:0;z-index:2;background:var(--paper);padding:6px 0 10px}
.libsearch input{width:100%;box-sizing:border-box;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:transparent;color:var(--ink);font:inherit;font-size:var(--t-body)}
.libg h2{font-family:var(--serif);font-size:var(--t-key);font-weight:600;margin:22px 0 4px;display:flex;align-items:baseline;gap:10px}
.libg h2 small{font-family:var(--ui);font-weight:400;font-size:var(--t-tag);color:var(--mute)}
.librow{display:flex;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}
.libt{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.libt b{font-family:var(--serif);font-size:var(--t-body);font-weight:600}
.libt i{font-style:normal;font-size:var(--t-tag);color:var(--faint)}
.libt span{font-size:var(--t-aux);color:var(--mute)}
.libt p{margin:2px 0 0;font-size:var(--t-aux);color:var(--ink2);line-height:1.5}
.librow .btn{flex:none;white-space:nowrap}
.libsoon{flex:none;font-size:var(--t-tag);color:var(--faint)}
.libnone{font-size:var(--t-body);margin:24px 0 8px}
.chrow{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;padding:10px 0;border-bottom:1px solid var(--line)}
.chrow .chname{flex:1 1 100%;font:inherit;font-family:var(--serif);font-size:var(--t-body);padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:transparent;color:var(--ink)}
.chrow small{color:var(--mute);font-size:var(--t-tag)}
.chrow .linkbtn{margin-left:auto;font-size:var(--t-aux)}
.chrow.merged{opacity:.5}.chrow.merged .chname{text-decoration:line-through}
.impbox{margin-top:0;""")
open(p,'w',encoding='utf-8').write(s); print('ok')
# 第二轮（手工）：解释卡片底部（含"还没有生成"那张）加"从这里分章"，调整章节说明文字改为"点开那一段，在底部选"
