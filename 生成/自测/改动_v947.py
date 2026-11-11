"""v9.47：阅读器接服务端（window.FUBI 存在时才生效；单文件 demo 行为不变）。每处替换断言只匹配 1 次。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
p=B+'Demo/模板.html'; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:80]); s=s.replace(a,b)

# 1 记录：服务端模式下，先用服务器上的记录，改动后 1.5 秒内同步回去
rep("""let mem={};
const store={get(k){try{return JSON.parse(localStorage.getItem(k))||null}catch(e){return mem[k]||null}},
             set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){mem[k]=v}}};""",
"""let mem={};
const SRV=window.FUBI&&window.FUBI.server?window.FUBI:null;   /* 有服务端：记录同步到服务器（按设备）；没有：只存浏览器（单文件 demo） */
const store={get(k){ if(SRV&&SRV.state&&k in SRV.state) return SRV.state[k]; try{return JSON.parse(localStorage.getItem(k))||null}catch(e){return mem[k]||null}},
             set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){mem[k]=v} if(SRV){ SRV.state[k]=v; syncQ[k]=v; clearTimeout(syncT); syncT=setTimeout(syncNow,1500); }}};
let syncQ={}, syncT=0;
function syncNow(beacon){
  if(!SRV) return; const q=syncQ; if(!Object.keys(q).length) return; syncQ={};
  const body=JSON.stringify(q);
  if(beacon&&navigator.sendBeacon){ navigator.sendBeacon('/api/state?m=put',new Blob([body],{type:'application/json'})); return; }
  fetch('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body,keepalive:true}).catch(()=>{ Object.assign(syncQ,q,syncQ); clearTimeout(syncT); syncT=setTimeout(syncNow,8000); });
}
if(SRV) addEventListener('pagehide',()=>syncNow(true));""")

# 2 书架：精编书 + 导入的书；导入入口；导入中/失败的书
rep("""const SHELF=[['hlm','bH','红楼梦','曹雪芹',''],""","""let SHELF=[['hlm','bH','红楼梦','曹雪芹',''],""")
rep("""function shelf(){
  window.onscroll=null;""","""/* 服务端模式：导入的书接在精编书后面（数据里带 meta），书的详情从 meta 生成 */
if(SRV){ Object.entries(ALL).forEach(([k,d],n)=>{ if(!d.meta) return; SHELF.push([k,'bi'+n,d.meta.title,d.meta.author||'',d.meta.nat||'']);
  const m=d.meta, g=m.gen||{}; BOOKS[k]={t:m.title,imported:true,rows:[['作者',esc(m.author||'（文件里没写）')],['来源',m.kind==='library'?'公版书库':'你导入的文件：'+esc(m.src||'')],['篇幅',`${m.chapters} 章，约 ${m.chars>=1e4?(m.chars/1e4).toFixed(1).replace(/\\.0$/,'')+' 万':m.chars} 字`],['解释与回顾',g.total?(g.done>=g.total?'已生成':`正在生成（${g.done} / ${g.total}）`):'还没有生成（需要服务器配置模型）'],['伏笔','导入的书暂时没有书中伏笔；可以自己划线提问，记成"我发现的伏笔"']]}; }); }
function importBox(){
  if(!SRV) return '';
  const pend=(SRV.pending||[]).map(b=>`<div class="impend ${b.status}" data-id="${esc(b.id)}"><b>${esc(b.title)}</b><span>${b.status==='failed'?esc(b.err||'导入失败')+' <button class="linkbtn" data-del="'+esc(b.id)+'">移除</button>':'正在导入…'}</span></div>`).join('');
  return `<div class="impbox">${pend}<label class="btn ghost wide" id="impBtn">导入自己的书<input type="file" id="impFile" hidden accept="${SRV.formats.map(x=>'.'+x).join(',')}"></label>
    <p class="mini">支持 ${SRV.formats.filter(x=>['epub','txt','pdf','docx','mobi','azw3'].includes(x)).join('、')} 等格式，单个不超过 ${SRV.maxMB}MB。导入的书只有你自己能看到。</p></div>`;
}
function wireImport(){
  if(!SRV) return;
  const f=$('#impFile'); if(f) f.onchange=async()=>{ const file=f.files[0]; if(!file) return;
    if(file.size>SRV.maxMB*1048576){ toast(`<div class="tq">文件太大（上限 ${SRV.maxMB}MB）。</div>`); return; }
    toast(`<div class="tq">正在导入《${esc(file.name.replace(/\\.[^.]+$/,''))}》…</div>`,null,60000);
    try{ const r=await fetch('/api/import',{method:'POST',headers:{'X-Filename':encodeURIComponent(file.name)},body:file}); const j=await r.json();
      if(!r.ok) throw new Error(j.error||'导入失败');
      for(let k=0;k<120;k++){ const st=await (await fetch('/api/books/'+j.id+'/status')).json(); if(st.status!=='parsing'){ if(st.status==='failed') throw new Error(st.err||'导入失败'); break; } await new Promise(r=>setTimeout(r,1000)); }
      syncNow(); location.reload();
    }catch(e){ toast(`<div class="tq">${esc(e.message)}</div>`,null,8000); } };
  document.querySelectorAll('[data-del]').forEach(b=>b.onclick=async()=>{ await fetch('/api/books/'+b.dataset.del,{method:'DELETE'}); location.reload(); });
}
function shelf(){
  window.onscroll=null;""")
rep("""    <p class="foot">测试版。书架上的书都是公有领域版本，来源见书的详情（长按）。阅读记录仅保存在本设备。</p>
  </div>`;""","""    ${importBox()}
    <p class="foot">${SRV?'测试版。精编书都是公有领域版本，来源见书的详情（长按）。阅读记录保存在服务器上（按这台设备）。':'测试版。书架上的书都是公有领域版本，来源见书的详情（长按）。阅读记录仅保存在本设备。'}</p>
  </div>`;
  wireImport();""")
rep("""const BOOKS={
  hlm:""","""var BOOKS={
  hlm:""")
# 书的详情里的说明：导入的书
rep("""  <p class="mini" style="margin-top:18px">${BOOKS[k].rows.some(r=>r[1].includes('切换只看中文'))||k==='tractatus'?""","""  ${b.imported?`<p class="mini" style="margin-top:18px">解释和回顾都以你的阅读进度为界。</p><div class="sfoot"><button class="btn ghost danger" id="bDel">从书架移除</button><button class="btn" id="bOpen" style="margin-left:auto">阅读</button></div>`:''}
  <p class="mini" style="margin-top:18px" ${b.imported?'hidden':''}>${BOOKS[k].rows.some(r=>r[1].includes('切换只看中文'))||k==='tractatus'?""")
rep("""  $('#bOpen')?.addEventListener('click',()=>{closeSheet();openBook(k);});""","""  $('#bOpen')?.addEventListener('click',()=>{closeSheet();openBook(k);});
  $('#bDel')?.addEventListener('click',async()=>{ if(!confirm('从书架移除这本书？你在这本书里的划线、想法也会一起删除。')) return; await fetch('/api/books/'+k,{method:'DELETE'}); store.set(ALL[k].key,null); syncNow(); location.reload(); });""")
# 书的详情：导入的书有两个"阅读"按钮时，隐藏原来那排
rep("""  <div class="sfoot"><button class="btn ghost" data-close>关闭</button><button class="btn" id="bOpen" style="margin-left:auto">阅读</button></div>`);
  $('#bOpen')""","""  ${b.imported?'':`<div class="sfoot"><button class="btn ghost" data-close>关闭</button><button class="btn" id="bOpen" style="margin-left:auto">阅读</button></div>`}`);
  $('#bOpen')""")

# 3 没有解释卡片的段落（导入的书还没生成）：点段落给一句说明，不报错
rep("""function openCard(i,opt={}){
  cardBack=""","""function openCard(i,opt={}){
  if(!CARDS[P[i].n]){ if(markRd(i,i)){paintMarks();save();}
    openSheet(`<div class="shead"><span class="n ${NOVEL?'nv':''}">${NOVEL?lab(P[i].n):P[i].n}</span><button class="x" data-close aria-label="关闭">×</button></div><div class="sbody"><p class="plain">这一段的解释${D.imported?'还没有生成':'暂时没有'}。</p><p class="mini">${D.imported?'导入的书在服务器配好模型后自动生成解释和回顾；现在可以照常阅读、划线、写想法和提问。':''}</p></div>`); return; }
  cardBack=""")
# 回目标题只有一段时（导入的书章名不一定有空格）照常

# 4 自由提问：没有预先写好的回答时，服务端模式下问模型
rep("""  const later=!!q, rvOk=later&&IDX[q['回收']]!==undefined;""","""  if(!q && SRV && opt.ai!==false){ askServer(hl,text,at,u); return; }
  const later=!!q, rvOk=later&&IDX[q['回收']]!==undefined;""")
rep("""const QA_TITLE={""","""/* 服务端：自由提问交给模型（按阅读位置、不剧透）。回答存成一条"预先写好的回答"，之后和示范问答走同一套显示 */
async function askServer(hl,text,at,u){
  const pos=P[Math.max(0,Math.max(at??-1,rdMax()))].n;
  toast(`<div class="tq">正在想……</div>`,null,30000);
  try{
    const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({book:BK,q:text,pos,hl:u?u.text:''})}); const j=await r.json();
    $('#toast').classList.remove('show');
    if(!r.ok) throw new Error(j.error||'没问成');
    const id='ai'+Date.now(); const q={id,'锚点':P[Math.max(at??0,0)].n,'问题':text,'类型':j['类型'],'回答':j['回答'],'引用':j['引用']||[],'回收':j['回收']||'','回收说明':j['回收说明']||'','回收锚句':j['回收锚句']||'',ai:true};
    (D.qa=D.qa||[]).push(q); QA=D.qa; S.aiqa=(S.aiqa||[]).concat([q]); save();
    askQuestion(hl,text,{at,qa:id});
  }catch(e){ toast(`<div class="tq">${esc(e.message)}。已先记为疑问。</div>`,null,5000); askQuestion(hl,text,{at,ai:false}); }
}
const QA_TITLE={""")
rep("""    <p class="mini">测试版的回答为预先撰写。</p>""","""    <p class="mini">${q.ai?'由模型按你的阅读进度回答，可能有错。':'测试版的回答为预先撰写。'}</p>""")
# 打开书时把以前问模型得到的回答放回 QA
rep("""  S=loadState(k); if(S.lang==='both') S.lang='zh';""","""  S=loadState(k); if(S.lang==='both') S.lang='zh';
  if(S.aiqa&&S.aiqa.length){ const have=new Set((D.qa||[]).map(x=>x.id)); D.qa=(D.qa||[]).concat(S.aiqa.filter(x=>!have.has(x.id))); QA=D.qa; }""")

# 5 样式
rep(""".shelf .foot{""",""".impbox{margin-top:28px;padding-top:18px;border-top:1px solid var(--line)}
.impbox .mini{margin-top:8px}
.impbox label.btn{display:block;text-align:center;cursor:pointer}
.impend{display:flex;flex-direction:column;gap:2px;padding:10px 0;font-size:var(--t-aux)}
.impend span{color:var(--mute)}
.impend.failed span{color:#A33A2A}
.shelf .foot{""")
# 第二轮（同一版）：SRV 书架块挪到 BOOKS 定义之后；书详情按钮排一行；导入的书用章名本身当"第几章"
open(p,'w',encoding='utf-8').write(s); print('ok')
# 第三轮（截图后）：没有作者的书不留空行；导入框顶部只留一条分隔线（手工改，见交接 v9.47）
