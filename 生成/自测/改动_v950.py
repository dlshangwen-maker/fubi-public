"""v9.50（用户 10-27 三条）：① 主线拼图卡去掉按钮；主线的伏笔不用点开，发现即打开（其它伏笔照旧要点）② 找书预览 + 多个下载源 ③ 导入和找书并列、去掉大按钮。
改前备份 Demo/模板_v65备份.html。每处替换断言只匹配 1 次。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
p=B+'Demo/模板.html'; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:80]); s=s.replace(a,b)

# ---- ① 主线 ----
rep("""  let fresh=reachedClues().filter(s=>!S.found[s.id]);
  fresh.forEach(s=>S.found[s.id]=Date.now()); if(fresh.length) save();""","""  let fresh=reachedClues().filter(s=>!S.found[s.id]);
  fresh.forEach(s=>S.found[s.id]=Date.now()); if(fresh.length) save();
  /* 主线的伏笔（2026-10-27 用户）：不用读者点开，发现就是打开的；其它伏笔照旧要点 */
  if(ML()){ let ch=false; reachedClues().forEach(s=>{ if(isPiece(s.id)&&!S.seen[s.id]){ S.seen[s.id]=S.found[s.id]||Date.now(); ch=true; } }); if(ch) save(); }""")
rep("""    /* 主线的碎片（2026-10-26 用户：没打开过怎么办）：只要读者发现过（页边亮过），读到答案就照样拼上，不要求点开过 */
    if(ML()&&isPiece(s.id)&&S.found[s.id]&&!S.seen[s.id]&&s['揭晓']&&atAns(IDX[s['揭晓']],cur)&&ansPassed(IDX[s['揭晓']],s['揭晓锚句'])){ S.seen[s.id]=Date.now(); S.mlLate=S.mlLate||{}; S.mlLate[s.id]=1; }
""","")
rep("""    ${(S.mlLate||{})[id]?`<p class="mlfx-src">这一块来自之前没打开的伏笔：${esc((SUS.find(x=>x.id===id)||{})['问题']||'')}</p>`:''}
""","")
rep("""    <p class="mlfx-n">${esc(note)}</p>
    <div class="mlfx-a"><button id="mlfxAns">看这处伏笔</button><button id="mlfxMain">${last?'看完整的回答':'看主线'}</button></div><button class="tx" id="mlfxX" aria-label="关闭">×</button>`;""","""    <p class="mlfx-n">${esc(note)}</p><button class="tx" id="mlfxX" aria-label="关闭">×</button>`;   /* 2026-10-27 用户：不要"看这处伏笔/看主线"按钮，只是一个惊喜时刻 */""")
rep("""  $('#mlfxX').onclick=hide; $('#mlfxAns').onclick=()=>{ hide(); reveal(id,true); }; $('#mlfxMain').onclick=()=>{ hide(); cluePanel('done'); };""","""  $('#mlfxX').onclick=hide;""")
rep("  for(const s of SUS){\n    if(S.seen[s.id] && !S.doneS[s.id] && s['揭晓'] && !atAns(","  for(const s of SUS){\n    if(ML()&&isPiece(s.id)&&S.found[s.id]&&!S.seen[s.id]) S.seen[s.id]=S.found[s.id];   /* 主线的伏笔发现即打开（保险：页边还没重画时） */\n    if(S.seen[s.id] && !S.doneS[s.id] && s['揭晓'] && !atAns(")

# ---- ② 找书：点结果看预览；同一本书几个来源，下载按顺序试 ----
rep("""    const act=have?`<button class="btn ghost" data-open="${esc(have[0])}">在书架上</button>`:r['可下载']?`<button class="btn" data-dl="${esc(r['来源'])}|${esc(r['编号'])}">下载到书架</button>`:'';
    const sub=[r['作者']?esc(r['作者']):'',r['语言名']+(r['需翻译']?'（下载后翻译成中文）':''),r['来源']==='gutenberg'?'古登堡计划':'维基文库'].filter(Boolean).join(' · ');
    return `<div class="librow ${r['可下载']?'':'off'}"><div class="libt"><b>""","""    const act=have?`<button class="btn ghost" data-open="${esc(have[0])}">在书架上</button>`:r['可下载']?`<button class="btn" data-dl="${R.indexOf(r)}">下载到书架</button>`:'';
    const sub=[r['作者']?esc(r['作者']):'',r['语言名']+(r['需翻译']?'（下载后翻译成中文）':''),r['来源名']||(r['来源']==='gutenberg'?'古登堡计划':'维基文库')].filter(Boolean).join(' · ');
    return `<div class="librow ${r['可下载']?'':'off'}" data-pv="${R.indexOf(r)}"><div class="libt"><b>""")
rep("""  el.querySelectorAll('[data-dl]').forEach(b=>b.onclick=()=>{ const [src,...ref]=b.dataset.dl.split('|'); const r=R.find(x=>x['来源']===src&&x['编号']===ref.join('|')); downloadBook(r,b); });""","""  el.querySelectorAll('[data-dl]').forEach(b=>b.onclick=e=>{ e.stopPropagation(); downloadBook(R[+b.dataset.dl],b); });
  el.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',e=>e.stopPropagation()));
  el.querySelectorAll('.librow[data-pv]').forEach(row=>row.onclick=()=>previewBook(R[+row.dataset.pv]));""")
rep("""    const res=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:r['来源'],ref:r['编号'],title:r['中文名']||r['书名'],author:r['作者']})}); const j=await res.json();""","""    const res=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sources:r['源']||[{'来源':r['来源'],'编号':r['编号']}],title:r['中文名']||r['书名'],author:r['作者']})}); const j=await res.json();""")
rep("""async function downloadBook(r,btn){""","""/* 预览：书的信息 + 开头几段（服务器先把书取下来解析；预览过的书再下载就很快）。底部"下载到书架" */
async function previewBook(r){
  const info=[['作者',r['作者']?esc(r['作者'])+(r['生卒']?`（${esc(r['生卒'])}）`:''):''],['语言',esc(r['语言名'])+(r['需翻译']?'，下载后由本应用翻译成中文':'')],['来源',esc(r['来源名']||'')],
    ['主题',(r['主题']||[]).map(esc).join('；')],['简介',esc(r['简介']||r['摘要']||'')]].filter(x=>x[1]);
  const have=SHELF.find(x=>ALL[x[0]]&&ALL[x[0]].meta&&ALL[x[0]].meta.link===r['链接']);
  const foot=()=>`<div class="sfoot"><button class="btn ghost" data-close>返回</button>${have?`<button class="btn" id="pvOpen" style="margin-left:auto">在书架上，去读</button>`:r['可下载']?`<button class="btn" id="pvDl" style="margin-left:auto">下载到书架</button>`:''}</div>`;
  openSheet(`<div class="shead"><span class="ttl">${esc(r['中文名']||r['书名'])}</span><button class="x" data-close aria-label="关闭">×</button></div>
    <div class="sbody">${r['中文名']?`<p class="pvorig">${esc(r['书名'])}</p>`:''}<dl class="meta">${info.map(([a,b])=>`<dt>${a}</dt><dd>${b}</dd>`).join('')}</dl>
    ${r['说明']?`<p class="mini libwhy">${esc(r['说明'])}</p>`:''}<div id="pvBody">${r['可下载']?'<p class="mini">正在取开头几页……</p>':''}</div></div>${foot()}`,{tall:true});
  $('#pvOpen')?.addEventListener('click',()=>{ closeSheet(); openBook(have[0]); });
  $('#pvDl')?.addEventListener('click',()=>downloadBook(r,$('#pvDl'),true));
  if(!r['可下载']) return;
  try{ const res=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sources:r['源']||[{'来源':r['来源'],'编号':r['编号']}]})}); const p=await res.json();
    if(!res.ok) throw new Error(p.error||'取不到');
    const el=$('#pvBody'); if(!el) return;
    el.innerHTML=`<p class="pvsz">${p['章数']} 章，约 ${p['字数']>=1e4?(p['字数']/1e4).toFixed(1).replace(/\\.0$/,'')+' 万':p['字数']} ${r['语言']==='zh'?'字':'个字符'}</p>
      <details class="pvtoc"><summary>目录</summary><ol>${p['目录'].map(t=>`<li>${esc(t)}</li>`).join('')}${p['章数']>p['目录'].length?'<li>……</li>':''}</ol></details>
      <div class="pvtext" lang="${esc(r['语言'])}"><h3>${esc(p['开头章'])}</h3>${p['开头'].map(x=>`<p>${esc(x)}</p>`).join('')}</div>`;
  }catch(e){ const el=$('#pvBody'); if(el) el.innerHTML=`<p class="mini libwhy">${esc(e.message)}。可以直接下载到书架试试。</p>`; }
}
async function downloadBook(r,btn,fromPv){""")
rep("""    btn.className='btn ghost'; btn.textContent='在书架上'; btn.disabled=false; btn.onclick=()=>openBook(j.id);""","""    btn.className='btn ghost'; btn.textContent='在书架上'; btn.disabled=false; btn.onclick=()=>{ closeSheet(); openBook(j.id); };
    if(fromPv){ btn.className='btn'; btn.textContent='在书架上，去读'; paintFind(); }""")

# ---- ③ 导入和找书并列：书架标题右边两个小字入口；去掉底部大按钮 ----
rep("""${SRV?'<button class="linkbtn shlib" id="shLib">找书 ›</button>':''}""","""${SRV?`<span class="shacts"><button class="linkbtn" id="shLib">找书</button><span class="shdot">·</span><label class="linkbtn" id="impBtn">导入<input type="file" id="impFile" hidden accept="${SRV.formats.map(x=>'.'+x).join(',')}"></label></span>`:''}""")
rep("""  return `<div class="impbox">${pend}<label class="btn ghost wide" id="impBtn">导入自己的书<input type="file" id="impFile" hidden accept="${SRV.formats.map(x=>'.'+x).join(',')}"></label>
    <p class="mini">支持 ${SRV.formats.filter(x=>['epub','txt','pdf','docx','mobi','azw3'].includes(x)).join('、')} 等格式，单个不超过 ${SRV.maxMB}MB。导入的书只有你自己能看到。</p></div>`;""","""  return pend?`<div class="impbox">${pend}</div>`:'';   /* 2026-10-27 用户：不要大按钮——"导入"和"找书"并列在书架标题右边；这里只列导入中、导入失败的书 */""")
rep(""".shh{display:flex;align-items:baseline;gap:12px}.shh .shlib{margin-left:auto;font-size:var(--t-aux)}""",""".shh{display:flex;align-items:baseline;gap:12px}.shh .shacts{margin-left:auto;display:flex;align-items:baseline;gap:8px;font-size:var(--t-aux)}.shh .shacts .linkbtn{cursor:pointer}.shdot{color:var(--faint)}""")
rep(""".impbox{margin-top:0;padding-top:20px;border-top:1px solid var(--line)}""",""".impbox{margin-top:0;padding-top:8px}""")
rep("""这里能搜到的是古登堡计划和维基文库里的公版书。手里有这本书的文件，可以回书架“导入自己的书”。""","""这里能搜到的是古登堡计划和维基文库里的公版书。手里有这本书的文件，可以在书架上点“导入”。""")
rep(""".libwait{margin-top:18px}""",""".libwait{margin-top:18px}
.librow[data-pv]{cursor:pointer}
.pvorig{margin:-6px 0 10px;color:var(--faint);font-size:var(--t-aux)}
.pvsz{font-size:var(--t-aux);color:var(--mute);margin:16px 0 6px}
.pvtoc summary{font-size:var(--t-aux);color:var(--blue);cursor:pointer}.pvtoc ol{margin:6px 0 0;padding-left:20px;font-size:var(--t-aux);color:var(--ink2);line-height:1.8}
.pvtext{margin-top:14px;padding-top:12px;border-top:1px solid var(--line);font-family:var(--serif);font-size:var(--t-body);line-height:1.8;color:var(--ink)}
.pvtext h3{font-size:var(--t-key);font-weight:600;margin:0 0 8px}.pvtext p{margin:0 0 10px;text-indent:2em}""")

open(p,'w',encoding='utf-8').write(s); print('ok')
