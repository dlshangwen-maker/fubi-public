"""v9.46 模板改动（2026-10-26，用户七条）。用法：python3 -I 生成/自测/改动_v946.py Demo/模板.html"""
import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
def R(a,b,cnt=1):
    global s
    n=s.count(a)
    if n!=cnt: raise SystemExit(f'找到 {n} 次（应 {cnt}）：{a[:90]}')
    s=s.replace(a,b)
def CUT(a,b,new):
    global s
    i=s.index(a); j=s.index(b,i); s=s[:i]+new+s[j:]

# ===== 1. 两步：只留两段进度条，不写字 =====
R("""  const L=['账号','问卷'];   /* 2026-10-26 用户：整体只两个节点，三道题是"问卷"里面的事 */
  return `<div class="pg flow"><div class="flbar">${back?'<button class="back" id="flBack" aria-label="上一步">‹</button>':'<span></span>'}<ol class="flsteps" aria-label="第 ${step} 步，共 ${total} 步">${L.slice(0,total).map((l,i)=>`<li class="${i<step?'on':''} ${i===step-1?'cur':''}"><i>${i+1}</i>${l}</li>`).join('<li class="ln" aria-hidden="true"></li>')}</ol><span></span></div><div class="flbody">${body}</div></div>`; }""",
  """  /* 2026-10-26 用户：两步就是两段进度条，不用写每一步干什么 */
  return `<div class="pg flow"><div class="flbar">${back?'<button class="back" id="flBack" aria-label="上一步">‹</button>':'<span></span>'}<div class="fldots" aria-label="第 ${step} 步，共 ${total} 步">${[...Array(total)].map((_,i)=>`<i class="${i<step?'on':''}"></i>`).join('')}</div><span></span></div><div class="flbody">${body}</div></div>`; }""")

# ===== 2. 问卷：三张卡一屏摊开，答完一张翻到下一张，答过的随时点回去改；结果随答案实时变 =====
CUT("function quizPage(opt={},step=0,keep=false){","/* ================= 我的：",r'''/* 问卷（2026-10-26 用户：要更有趣、能当场回去改）：三张卡叠在一屏里——当前那张展开，答过的收成一行"平时：常读到一半放下 ✎"，点一下就展开重改；
   底下一块"伏笔会这样陪你"随答案实时变（轻/重），三题都答完就能"开始读书" */
function quizPage(opt={},step=null){
  const A=quizPage.a=step!=null&&quizPage.a?quizPage.a:structuredClone(PROF.qz&&!PROF.qz.skipped?PROF.qz:{q1:null,q2:[],q3:null});
  const done=q=>q.m?(A[q.k]||[]).length>0:!!A[q.k];
  const cur=step!=null?step:Math.max(0,QZ.findIndex(q=>!done(q))), all=QZ.every(done), u=curUser(), first=opt.first;
  const ans=q=>q.m?(A[q.k]||[]).map(v=>q.o.find(o=>o[0]===v)[1]).join('、'):(q.o.find(o=>o[0]===A[q.k])||[])[1];
  const SHORT={q1:'平时',q2:'常卡在',q3:'希望'};
  const card=(q,i)=>{ const open=i===cur&&!(all&&step==null);
    if(!open&&done(q)) return `<button class="qzc done" data-edit="${i}"><span class="qzk">${SHORT[q.k]}</span><span class="qzv">${esc(ans(q))}</span><span class="qze" aria-hidden="true">改</span></button>`;
    if(!open) return `<div class="qzc wait"><span class="qzk">${SHORT[q.k]}</span><span class="qzv">…</span></div>`;
    return `<div class="qzc open"><h2 class="qzt">${q.t}</h2>${q.m?'<p class="mini">可以多选，选好点“好了”</p>':''}
      <div class="qzchips">${q.o.map(([v,l])=>`<button data-v="${v}" aria-pressed="${q.m?(A[q.k]||[]).includes(v):A[q.k]===v}">${l}</button>`).join('')}</div>
      ${q.m?`<div class="qzok"><button class="btn" id="qzNext" ${done(q)?'':'disabled'}>好了</button></div>`:''}</div>`; };
  const m=quizMode(A);
  const body=`<div class="qz">
    ${first?`<p class="qzhi">${u?esc(u.name)+'，':''}聊三句，伏笔就知道怎么陪你读了。</p>`:''}
    <div class="qzcards">${QZ.map(card).join('')}</div>
    ${all?`<div class="qzres"><div class="qzrh">伏笔会以 <b>${MODE_T[m]}</b> 的方式陪你读</div><p>${MODE_D[m]}${PROF.lv===0||(A.q2||[]).includes('words')?'解释默认从“入门”开始。':''}</p></div>`:''}
    <div class="qzfoot">${first?'<button class="linkbtn" id="qzSkip">跳过</button>':''}${all?`<button class="btn" id="qrOk">${first?'开始读书':'保存'}</button>`:''}</div></div>`;
  showPage(first?flowHTML(2,2,body,true):pageHTML('阅读习惯','阅读偏好',body),first?null:()=>prefPage());
  const q=QZ[cur], go=n=>quizPage(opt,n);
  const nextOpen=()=>{ const n=QZ.findIndex((x,i)=>i!==cur&&!done(x)); go(n<0?null:n); };
  $('#flBack')?.addEventListener('click',()=>authPage('reg'));
  document.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>go(+b.dataset.edit));
  document.querySelectorAll('.qzchips button').forEach(b=>b.onclick=()=>{ const v=b.dataset.v;
    if(q.m){ const a=A[q.k]=A[q.k]||[]; const i=a.indexOf(v); i<0?a.push(v):a.splice(i,1); b.setAttribute('aria-pressed',i<0); $('#qzNext').disabled=!a.length; return; }
    A[q.k]=v; document.querySelectorAll('.qzchips button').forEach(x=>x.setAttribute('aria-pressed',x===b)); b.classList.add('pop'); setTimeout(nextOpen,260); });
  $('#qzNext')?.addEventListener('click',nextOpen);
  $('#qzSkip')?.addEventListener('click',()=>{ PROF.qz={skipped:true,t:Date.now()}; setMode('light'); shelf(); });
  $('#qrOk')?.addEventListener('click',()=>{ A.t=Date.now(); PROF.qz=A; PROF.lv=(A.q2||[]).includes('words')?0:null; setMode(quizMode(A)); first?shelf():prefPage(); });
}
function quizResult(m,first){ quizPage({first}); }
''')

# ===== 3. 退出这本书：和这本书有关的提示立刻消失 =====
R("function showPage(html,backFn){ window.onscroll=null; closeSheet();","function showPage(html,backFn){ window.onscroll=null; closeSheet(); dropBookTips();")
R("function shelf(){\n  window.onscroll=null; closeSheet();","function shelf(){\n  window.onscroll=null; closeSheet(); dropBookTips();")
R("function toast(html,act,ms=6000){","""/* 书里的提示（揭晓、主线、答案快到了、第一次发现……）都记在一张单子上：离开这本书就全部撤掉，免得带到下一本书 */
const bookTimers=new Set();
const later=(fn,ms)=>{ const id=setTimeout(()=>{ bookTimers.delete(id); fn(); },ms); bookTimers.add(id); return id; };
function dropBookTips(){ bookTimers.forEach(clearTimeout); bookTimers.clear(); clearTimeout(toast._t); clearTimeout(mainReveal.t);
  $('#toast')?.classList.remove('show'); $('#mlfx')?.classList.remove('show'); }
function toast(html,act,ms=6000){""")
R("function openBook(k){ setBook(k); reader(true); }","function openBook(k){ dropBookTips(); setBook(k); reader(true); }")
for a in ["      if(q) setTimeout(()=>toast(`<div class=\"tq\">答案快到了：",
          "      setTimeout(()=>toast(`<div class=\"tq\">伏笔揭晓：${esc(n.text)}</div>"]:
    R(a,a.replace("setTimeout(","later(",1))
R("const tip=()=>{ if($('#toast').classList.contains('show')) return setTimeout(tip,3000);","const tip=()=>{ if($('#toast').classList.contains('show')) return later(tip,3000);")
R("setTimeout(tip,2600);}","later(tip,2600);}")
R("setTimeout(()=>mainReveal(s.id),calm()?0:600); break; }","later(()=>mainReveal(s.id),calm()?0:600); break; }")
R("      if(ML()&&isPiece(s.id)) setTimeout(()=>mainReveal(s.id),calm()?0:900);","      if(ML()&&isPiece(s.id)) later(()=>mainReveal(s.id),calm()?0:900);")
R("      else setTimeout(()=>toast(`<div class=\"tq\">伏笔揭晓：${esc(s['问题'])}</div>","      else later(()=>toast(`<div class=\"tq\">伏笔揭晓：${esc(s['问题'])}</div>")
R("  const go=()=>{ if($('#toast').classList.contains('show')) return setTimeout(go,3500);","  const go=()=>{ if($('#toast').classList.contains('show')) return later(go,3500);")
R("  setTimeout(go,1200); }","  later(go,1200); }")
R("  if(RD.size && fromShelf && !S.finished && (heavy()||gap==null||gap>DAY)) setTimeout(()=>recap(gap),250);\n  else if(!RD.size && fromShelf && heavy() && !S.guided){ S.guided=Date.now(); setTimeout(bookGuide,250); }",
  "  if(RD.size && fromShelf && !S.finished && (heavy()||gap==null||gap>DAY)) later(()=>recap(gap),250);\n  else if(!RD.size && fromShelf && heavy() && !S.guided){ S.guided=Date.now(); later(bookGuide,250); }")

# ===== 4. 主线的伏笔没打开过：答案读到了照样拼上（不要求打开），拼图卡里先给出这处伏笔的问题 =====
R("""      const j=IDX[s['揭晓']], u=unitAt(cur); if(ML()&&isPiece(s.id)&&u&&j>=u.first&&j<=cur){""","""      const j=IDX[s['揭晓']], u=unitAt(cur); if(ML()&&isPiece(s.id)&&u&&j>=u.first&&j<=cur){""")
R("  for(const s of SUS){\n    if(S.seen[s.id] && !S.doneS[s.id] && s['揭晓'] && !atAns(","""  for(const s of SUS){
    /* 主线的碎片（2026-10-26 用户：没打开过怎么办）：只要读者发现过（页边亮过），读到答案就照样拼上，不要求点开过 */
    if(ML()&&isPiece(s.id)&&S.found[s.id]&&!S.seen[s.id]&&s['揭晓']&&atAns(IDX[s['揭晓']],cur)&&ansPassed(IDX[s['揭晓']],s['揭晓锚句'])){ S.seen[s.id]=Date.now(); S.mlLate=S.mlLate||{}; S.mlLate[s.id]=1; }
    if(S.seen[s.id] && !S.doneS[s.id] && s['揭晓'] && !atAns(""")
R("""    <div class="mlfx-q">${esc(m.q)}</div>""","""    <div class="mlfx-q">${esc(m.q)}</div>
    ${(S.mlLate||{})[id]?`<p class="mlfx-src">这一块来自之前没打开的伏笔：${esc((SUS.find(x=>x.id===id)||{})['问题']||'')}</p>`:''}""")

# ===== 5. 每个提示条都有 × =====
R("""function toast(html,act,ms=6000){
  const t=$('#toast'); t.innerHTML=html; t.classList.add('show');""","""function toast(html,act,ms=6000){
  const t=$('#toast'); t.innerHTML=html+'<button class="tx" aria-label="关闭提示">×</button>'; t.classList.add('show');
  t.querySelector('.tx').onclick=()=>{ clearTimeout(toast._t); t.classList.remove('show'); };""")
R("  const b=t.querySelector('button'); if(b&&act) b.onclick=()=>{t.classList.remove('show');act();};","  const b=t.querySelector('button:not(.tx)'); if(b&&act) b.onclick=()=>{t.classList.remove('show');act();};")
R("""    <div class="mlfx-a"><button id="mlfxAns">看这处伏笔</button><button id="mlfxMain">${last?'看完整的回答':'看主线'}</button></div>`;""",
  """    <div class="mlfx-a"><button id="mlfxAns">看这处伏笔</button><button id="mlfxMain">${last?'看完整的回答':'看主线'}</button></div><button class="tx" id="mlfxX" aria-label="关闭">×</button>`;""")
R("  $('#mlfxAns').onclick=()=>{ hide(); reveal(id,true); };","  $('#mlfxX').onclick=hide; $('#mlfxAns').onclick=()=>{ hide(); reveal(id,true); };")

# ===== 6. 轻度不显示章末"回顾这一节" =====
R("  e.hidden=!on; if(on&&!e.innerHTML)","  e.hidden=!on||!heavy(); if(on&&heavy()&&!e.innerHTML)")
R("function setMode(m){ PROF.mode=m; saveProf(true); if(S){ SUS=buildSUS();","function setMode(m){ PROF.mode=m; saveProf(true); if(S){ SUS=buildSUS(); if(typeof paintUEnd==='function'&&els.length) paintUEnd();")

# ===== 7. 阅读回顾固定在导览底部，只滚目录 =====
R("""      body+=`<div class="fog">可以跳到任何一${UNIT}；没翻过的内容不算已读。</div>${RD.size?'<button class="btn ghost" id="olRecap" style="margin-top:4px">阅读回顾</button>':''}`;""",
  """      body+=`<div class="fog">可以跳到任何一${UNIT}；没翻过的内容不算已读。</div>`;""")
R("""  <div class="sbody"><div class="ol" id="olBody">${body}</div></div>`,{tall:true});
  const sh=$('#sheet');""","""  <div class="sbody"><div class="ol" id="olBody">${body}</div></div>
  ${tab==='hui'&&RD.size?`<div class="sfoot olfoot"><button class="btn ghost wide" id="olRecap">${ic('toc','')}阅读回顾</button></div>`:''}`,{tall:true});
  const sh=$('#sheet');""")
R("""  <div class="ol"><details><summary><span class="on" style="font-size:16px">序</span><span class="ot">前言</span></summary><div class="kids"><button id="goPre"><span>前言</span></button></div></details>${h}</div></div></div>`,{tall:true});""",
  """  <div class="ol"><details><summary><span class="on" style="font-size:16px">序</span><span class="ot">前言</span></summary><div class="kids"><button id="goPre"><span>前言</span></button></div></details>${h}</div></div></div>
  ${RD.size?`<div class="sfoot olfoot"><button class="btn ghost wide" id="olRecap">${ic('toc','')}阅读回顾</button></div>`:''}`,{tall:true});
  $('#olRecap')?.addEventListener('click',()=>propRecap(true));""")
R("function propRecap(){","function propRecap(manual){")
R("""  openSheet(`<div class="shead"><span class="ttl">继续阅读</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">
    <p class="plain">上次读到 <span style="font-family:var(--num)">${last.n}</span>。</p>""","""  openSheet(`<div class="shead">${manual?'<button class="x back" id="rcBack" aria-label="返回导览">‹</button>':''}<span class="ttl">${manual?'阅读回顾':'继续阅读'}</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">
    <p class="plain">上次读到 <span style="font-family:var(--num)">${last.n}</span>。</p>""")
R("""  <div class="sfoot"><button class="btn" data-close style="margin-left:auto">继续阅读</button></div>`);
}

""","""  <div class="sfoot"><button class="btn" data-close style="margin-left:auto">继续阅读</button></div>`);
  $('#rcBack')?.addEventListener('click',()=>propOutline());
}

""")
R("  $('#olRecap')?.addEventListener('click',()=>novelRecap(Infinity,true));","  $('#olRecap')?.addEventListener('click',()=>novelRecap(Infinity,true,true));")
R("function novelRecap(gap,manual){","function novelRecap(gap,manual,fromOl){")
R("""  openSheet(`<div class="shead"><span class="ttl">${manual?'阅读回顾':'继续阅读'}</span><button class="x" data-close aria-label="关闭">×</button></div>""",
  """  openSheet(`<div class="shead">${fromOl?'<button class="x back" id="rcBack" aria-label="返回导览">‹</button>':''}<span class="ttl">${manual?'阅读回顾':'继续阅读'}</span><button class="x" data-close aria-label="关闭">×</button></div>""")
R("  $('#rcMore')?.addEventListener('click',()=>novelRecap(Infinity,true));","  $('#rcMore')?.addEventListener('click',()=>novelRecap(Infinity,true));\n  $('#rcBack')?.addEventListener('click',()=>novelOutline('hui'));")

R("</style>",""".flow .fldots i{width:40px}
.qzhi{font-family:var(--serif);font-size:var(--t-key);color:var(--ink2);margin:0 0 22px;line-height:1.7}
.qzcards{display:flex;flex-direction:column;gap:10px}
.qzc{display:flex;align-items:center;gap:10px;width:100%;text-align:left;padding:14px 16px;border-radius:14px;background:var(--sheet);box-shadow:0 0 0 1px var(--line);font-size:var(--t-body);transition:transform .25s,box-shadow .25s}
.qzc .qzk{color:var(--mute);font-size:var(--t-aux);min-width:3.5em}
.qzc .qzv{flex:1;color:var(--ink)}
.qzc .qze{font-size:var(--t-tag);color:var(--blue)}
.qzc.wait{opacity:.5}
.qzc.done{animation:cardIn .35s ease-out}
@keyframes cardIn{from{transform:scale(.97);opacity:.6}to{transform:none;opacity:1}}
.qzc.open{display:block;padding:18px 16px 16px;box-shadow:0 0 0 1.5px var(--ink),0 8px 24px rgba(0,0,0,.06)}
.qzc.open .qzt{font-family:var(--serif);font-size:var(--t-panel);font-weight:600;margin:0 0 4px;line-height:1.5}
.qzchips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.qzchips button{padding:10px 14px;border-radius:20px;box-shadow:inset 0 0 0 1px var(--line);font-size:var(--t-body);color:var(--ink2);background:var(--field);transition:background .2s,color .2s,transform .2s}
.qzchips button[aria-pressed=true]{background:var(--ink);color:var(--paper);box-shadow:none}
.qzchips button.pop{transform:scale(1.06)}
.qzok{display:flex;justify-content:flex-end;margin-top:14px}
.qzok .btn:disabled{opacity:.35}
.qzres{margin-top:18px;padding:16px;border-radius:14px;background:var(--paper2);animation:cardIn .4s ease-out}
.qzrh{font-family:var(--serif);font-size:var(--t-key);margin-bottom:6px}
.qzrh b{color:var(--blue)}
.qzres p{margin:0;font-size:var(--t-aux);color:var(--mute);line-height:1.7}
.qzfoot{display:flex;justify-content:space-between;align-items:center;margin-top:22px;min-height:40px}
.qzfoot .btn:only-child{margin-left:auto}
.toast{padding-right:6px}
.toast .tx,#mlfx .tx{color:var(--paper);opacity:.6;font-size:18px;line-height:1;padding:4px 6px}
#mlfx{padding-right:16px}
#mlfx .tx{position:absolute;right:6px;top:6px}
#mlfx .mlfx-h{padding-right:22px}
.mlfx-src{font-size:var(--t-tag);opacity:.75;margin:0 0 8px;line-height:1.6}
.olfoot{padding-top:10px}
.olfoot .btn{display:flex;align-items:center;justify-content:center;gap:6px}
.olfoot svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
</style>""")
open(p,'w',encoding='utf-8').write(s); print('ok v946')
