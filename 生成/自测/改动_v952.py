"""v9.52（用户 10-27）：① 找书：书的信息和下载来源直接显示在搜索结果里，不用点开 ② 主线伏笔：卡片里"主线"那一行做成有颜色的框；伏笔页列表里主线的伏笔也带颜色。
改前备份 Demo/模板_v67备份.html。每处替换断言只匹配 1 次。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
p=B+'Demo/模板.html'; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:80]); s=s.replace(a,b)

# ---- ① 搜索结果一条 = 书的信息卡：书名、原名、介绍、作者、语言、下载来源（各自有"下载"） ----
i=s.index("  h+=R.map(r=>{ const have="); j=s.index("  if(!B.length&&!R.length) h=")
s=s[:i]+r"""  h+=R.map((r,ri)=>{ const L=r['源']||[{'来源':r['来源'],'编号':r['编号'],'名':r['来源名']||r['来源']}];
    const have=SHELF.find(x=>ALL[x[0]]&&ALL[x[0]].meta&&L.some(y=>ALL[x[0]].meta.link===y['链接']));
    const zhA=r['作者中文']?authorName(r['作者中文'],r['国籍']||''):'', enA=r['作者']&&r['作者']!==r['作者中文']?r['作者']:'';
    const meta=[zhA||enA?esc(zhA||enA)+(r['生卒']?` ${esc(r['生卒'])}`:''):'',esc(r['语言名'])+(r['需翻译']?'，下载后翻译成中文':'')].filter(Boolean).join(' · ');
    const intro=r['简介']||r['摘要']||'';
    const srcs=have?`<div class="fsrc"><span>已在书架上</span><button class="btn ghost" data-open="${esc(have[0])}">去读</button></div>`
      :r['可下载']?L.map((x,k)=>`<div class="fsrc"><span>${esc(x['名']||x['来源'])}<small>${esc(x['说明']||'')}</small></span><button class="btn ${k?'ghost':''}" data-dl="${ri}" data-k="${k}">下载</button></div>`).join('')
      :`<p class="libwhy">${esc(r['说明']||'暂时不能下载')}</p>`;
    return `<div class="fbook ${r['可下载']?'':'off'}"><b class="ft">${esc(r['中文名']||r['书名'])}</b>${r['中文名']?`<i class="fo">${esc(r['书名'])}</i>`:''}
      ${intro?`<p class="fi">${esc(intro)}</p>`:''}<p class="fm">${meta}${zhA&&enA?`<br><span class="fen">${esc(enA)}</span>`:''}</p>
      ${r['内容提要']?`<details class="pvsum"><summary>内容提要（英文）</summary><p lang="en">${esc(r['内容提要'])}</p></details>`:''}
      <div class="fsrcs">${!have&&r['可下载']?'<span class="fsh">下载来源</span>':''}${srcs}</div></div>`; }).join('');
"""+s[j:]
rep("""  el.querySelectorAll('[data-dl]').forEach(b=>b.onclick=e=>{ e.stopPropagation(); downloadBook(R[+b.dataset.dl],b); });
  el.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',e=>e.stopPropagation()));
  el.querySelectorAll('.librow[data-pv]').forEach(row=>row.onclick=()=>previewBook(R[+row.dataset.pv]));""","""  el.querySelectorAll('[data-dl]').forEach(b=>b.onclick=()=>{ const r=R[+b.dataset.dl], k=+b.dataset.k, L=r['源']||[]; downloadBook(r,b,'row',L.length?[L[k],...L.filter((_,i)=>i!==k)]:null); });""")
rep("""    if(fromPv){ document.querySelectorAll('#sheet [data-src]').forEach(b2=>{ if(b2!==btn) b2.remove(); }); btn.className='btn'; btn.textContent='去读'; paintFind(); }""","""    if(fromPv){ paintFind(); }""")
rep("""  }catch(e){ btn.disabled=false; btn.textContent=fromPv?'下载':'下载到书架'; toast(""","""  }catch(e){ btn.disabled=false; btn.textContent='下载'; toast(""")
rep("""    btn.textContent='正在整理…';""","""    btn.textContent='正在整理…'; document.querySelectorAll('[data-dl]').forEach(b2=>{ if(b2!==btn&&b2.dataset.dl===btn.dataset.dl) b2.disabled=true; });""")
# 精编书命中也用同样的卡片样式
rep("""  if(B.length) h+=B.map(b=>`<div class="librow"><div class="libt"><b>${esc(b['书名'])}</b><span>${esc(authorName(b['作者'],b['国籍']||''))} · 精读版</span><p>${esc(b['简介'])}</p></div><button class="btn ghost" data-open="${esc(b['编号'])}">在书架上</button></div>`).join('');""",
"""  if(B.length) h+=B.map(b=>`<div class="fbook"><b class="ft">${esc(b['书名'])}</b><p class="fi">${esc(b['简介'])}</p><p class="fm">${esc(authorName(b['作者'],b['国籍']||''))} · 精读版（有伏笔、主线和逐段解释）</p><div class="fsrcs"><div class="fsrc"><span>已在书架上</span><button class="btn ghost" data-open="${esc(b['编号'])}">去读</button></div></div></div>`).join('');""")
rep(""".pvorig{margin:-6px 0 10px;color:var(--faint);font-size:var(--t-aux)}""",""".pvorig{margin:-6px 0 10px;color:var(--faint);font-size:var(--t-aux)}
.fbook{padding:16px 0 14px;border-bottom:1px solid var(--line)}
.fbook .ft{display:block;font-family:var(--serif);font-size:var(--t-key);font-weight:600}
.fbook .fo{display:block;font-style:normal;font-size:var(--t-tag);color:var(--faint);margin-top:2px}
.fbook .fi{font-family:var(--serif);font-size:var(--t-body);line-height:1.75;margin:8px 0 6px;color:var(--ink)}
.fbook .fm{font-size:var(--t-aux);color:var(--mute);margin:0 0 4px;line-height:1.6}.fbook .fen{color:var(--faint);font-size:var(--t-tag)}
.fbook.off .ft{color:var(--mute)}
.fsrcs{margin-top:8px}.fsh{display:block;font-size:var(--t-tag);color:var(--faint);margin-bottom:2px}
.fsrc{display:flex;align-items:center;gap:10px;padding:7px 0}.fsrc>span{flex:1;display:flex;flex-direction:column;font-size:var(--t-aux);color:var(--ink)}.fsrc small{font-size:var(--t-tag);color:var(--faint)}.fsrc .btn{flex:none;padding:6px 14px}""")

# ---- ② 主线伏笔：卡片里"主线"一行 = 有颜色的框；伏笔页里主线的伏笔整条带底色 ----
rep(""".clmain{display:flex;gap:8px;align-items:baseline;font-size:var(--t-aux);color:var(--mute);margin:0 0 12px;line-height:1.6}.clmain .mltag{flex:none}""",
""".clmain{display:flex;gap:8px;align-items:baseline;font-size:var(--t-aux);color:var(--ink2);margin:0 0 12px;line-height:1.6;padding:10px 12px;border-radius:10px;background:var(--mark);box-shadow:inset 0 0 0 1px var(--hl-soft)}.clmain .mltag{flex:none;background:var(--hl);color:#1F2A26}
.q.fbook.ismain{background:var(--mark);margin:6px -12px;padding:12px;border-radius:10px;border-bottom:0;box-shadow:inset 0 0 0 1px var(--hl-soft)}
.q.fbook.ismain .tag.t-main{background:var(--hl);color:#1F2A26}""")
rep("""    return `<div class="q fbook ${d?'done':''}"><div class="from">""","""    return `<div class="q fbook ${d?'done':''} ${ML()&&isPiece(s.id)?'ismain':''}"><div class="from">""")
open(p,'w',encoding='utf-8').write(s); print('ok')
# 第二轮（手工）：下载完把书 id 记在这条结果上（r._bk），重画时显示"已在书架上 · 去读"
