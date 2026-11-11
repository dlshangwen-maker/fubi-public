"""v9.51（用户 10-27）：① 主线的伏笔不只是默认打开，还要把伏笔卡片弹出来 ② 找书点结果：直接显示书的信息和介绍（不显示原文），下面列出几个下载来源，每个都能下载。
改前备份 Demo/模板_v66备份.html。每处替换断言只匹配 1 次。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
p=B+'Demo/模板.html'; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:80]); s=s.replace(a,b)

# ---- ① 主线的伏笔：发现时直接弹出伏笔卡片（不等读者点）；同时发现几处，弹第一处 ----
rep("""  if(fresh.length&&!quietFind) announceFound(fresh);""","""  if(fresh.length&&!quietFind){ announceFound(fresh);
    const mp=ML()&&fresh.find(s=>isPiece(s.id));   /* 2026-10-27 用户：主线的伏笔不只是默认打开，还要把内容弹出来 */
    if(mp) later(()=>{ if(!$('#sheet').classList.contains('show')&&S.inBook) openClue(mp.id); },calm()?0:700); }""")
# 主线伏笔卡片上标一下"主线"
rep("""    <div class="q" style="border:0;padding-top:0">${srcBlock(srcQuote(s,true))}<div class="qt">${esc(s['问题'])}</div></div>""","""    ${ML()&&isPiece(id)?`<div class="clmain"><span class="mltag">主线</span><span>${esc(D.main.q)}</span></div>`:''}
    <div class="q" style="border:0;padding-top:0">${srcBlock(srcQuote(s,true))}<div class="qt">${esc(s['问题'])}</div></div>""")
rep(""".libwait{margin-top:18px}""",""".libwait{margin-top:18px}
.clmain{display:flex;gap:8px;align-items:baseline;font-size:var(--t-aux);color:var(--mute);margin:0 0 12px;line-height:1.6}.clmain .mltag{flex:none}""")
# 第一次发现伏笔的说明提示条：主线伏笔已经弹出卡片了，就不再说"点击查看"
rep("""  if(tipOnce('tipFound')){""","""  if(!(ML()&&list.some(s=>isPiece(s.id)))&&tipOnce('tipFound')){""")

# ---- ② 找书：书的信息 + 介绍 + 下载来源（不显示原文） ----
i=s.index("/* 预览：书的信息 + 开头几段"); j=s.index("async function downloadBook(r,btn,fromPv){")
s=s[:i]+r"""/* 书的信息（2026-10-27 用户）：直接显示这本书的信息和介绍，不显示原文；下面列出几个下载来源，每个都能下载 */
function previewBook(r){
  const au=r['作者中文']&&r['语言']!=='zh'?`${esc(authorName(r['作者中文'],r['国籍']||''))}（${esc(r['作者'])}）`:esc(r['作者']||r['作者中文']||'');
  const info=[['作者',au?au+(r['生卒']?`，${esc(r['生卒'])}`:''):''],['语言',esc(r['语言名'])+(r['需翻译']?'，下载后由本应用翻译成中文':'')],['主题',(r['主题']||[]).map(esc).join('；')]].filter(x=>x[1]);
  const intro=r['简介']||r['摘要']||'';
  const have=SHELF.find(x=>ALL[x[0]]&&ALL[x[0]].meta&&(r['源']||[]).some(s=>ALL[x[0]].meta.link===s['链接']));
  const src=(r['源']||[{'来源':r['来源'],'编号':r['编号'],'名':r['来源名']}]).map((x,k)=>`<div class="pvsrc"><div><b>${esc(x['名']||x['来源'])}</b><small>${esc(x['说明']||'')}</small></div>${have?'':r['可下载']?`<button class="btn ${k?'ghost':''}" data-src="${k}">下载</button>`:''}</div>`).join('');
  openSheet(`<div class="shead"><span class="ttl">${esc(r['中文名']||r['书名'])}</span><button class="x" data-close aria-label="关闭">×</button></div>
    <div class="sbody">${r['中文名']?`<p class="pvorig">${esc(r['书名'])}</p>`:''}
      ${intro?`<p class="pvintro">${esc(intro)}</p>`:''}
      <dl class="meta">${info.map(([a,b])=>`<dt>${a}</dt><dd>${b}</dd>`).join('')}</dl>
      ${r['内容提要']?`<details class="pvsum"><summary>内容提要（英文，来自古登堡计划）</summary><p lang="en">${esc(r['内容提要'])}</p></details>`:''}
      ${r['说明']?`<p class="mini libwhy">${esc(r['说明'])}</p>`:''}
      <h3 class="pvh">${have?'已在书架上':'下载来源'}</h3>${have?`<button class="btn" id="pvOpen">去读</button>`:src}
      ${!have&&r['可下载']&&(r['源']||[]).length>1?'<p class="mini">一个来源下载不了，可以换另一个。</p>':''}</div>`,{tall:true});
  $('#pvOpen')?.addEventListener('click',()=>{ closeSheet(); openBook(have[0]); });
  document.querySelectorAll('#sheet [data-src]').forEach(b=>b.onclick=()=>{ const k=+b.dataset.src, list=r['源']||[]; downloadBook(r,b,true,[list[k],...list.filter((_,i)=>i!==k)]); });
}
"""+s[j:]
rep("""async function downloadBook(r,btn,fromPv){""","""async function downloadBook(r,btn,fromPv,order){""")
rep("""body:JSON.stringify({sources:r['源']||[{'来源':r['来源'],'编号':r['编号']}],title""","""body:JSON.stringify({sources:(order||r['源']||[{'来源':r['来源'],'编号':r['编号']}]).map(x=>({'来源':x['来源'],'编号':x['编号']})),title""")
rep("""    if(fromPv){ btn.className='btn'; btn.textContent='在书架上，去读'; paintFind(); }""","""    if(fromPv){ document.querySelectorAll('#sheet [data-src]').forEach(b2=>{ if(b2!==btn) b2.remove(); }); btn.className='btn'; btn.textContent='去读'; paintFind(); }""")
rep("""  }catch(e){ btn.disabled=false; btn.textContent='下载到书架'; toast(""","""  }catch(e){ btn.disabled=false; btn.textContent=fromPv?'下载':'下载到书架'; toast(""")
rep(""".pvorig{margin:-6px 0 10px;color:var(--faint);font-size:var(--t-aux)}""",""".pvorig{margin:-6px 0 10px;color:var(--faint);font-size:var(--t-aux)}
.pvintro{font-family:var(--serif);font-size:var(--t-body);line-height:1.8;margin:4px 0 14px}
.pvsum{margin:10px 0}.pvsum summary{font-size:var(--t-aux);color:var(--blue);cursor:pointer}.pvsum p{font-size:var(--t-aux);color:var(--ink2);line-height:1.7;margin:6px 0 0}
.pvh{font-family:var(--ui);font-size:var(--t-aux);font-weight:400;color:var(--mute);margin:20px 0 4px}
.pvsrc{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}.pvsrc>div{flex:1;display:flex;flex-direction:column;gap:2px}.pvsrc b{font-weight:600;font-size:var(--t-body)}.pvsrc small{font-size:var(--t-tag);color:var(--mute)}""")
open(p,'w',encoding='utf-8').write(s); print('ok')
# 第二轮（截图后手工）：作者行改为"中文名[国籍]　生卒"，英文名另起一行小字
