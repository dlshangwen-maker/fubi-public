"""v9.45 模板改动（2026-10-26）：注册两节点；章回顾放进书里；答案快到了去掉页边图标；主线碎片揭晓的拼图卡。
用法：python3 -I 生成/自测/改动_v945.py Demo/模板.html"""
import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
def R(a,b,cnt=1):
    global s
    n=s.count(a)
    if n!=cnt: raise SystemExit(f'找到 {n} 次（应 {cnt}）：{a[:90]}')
    s=s.replace(a,b)

# ===== 1. 首次流程：两个节点（账号 / 问卷）；问卷里三题自己的进度 =====
R("""  return `<div class="pg flow"><div class="flbar">${back?'<button class="back" id="flBack" aria-label="上一步">‹</button>':'<span></span>'}<div class="fldots" aria-label="第 ${step} 步，共 ${total} 步">${[...Array(total)].map((_,i)=>`<i class="${i<step?'on':''}"></i>`).join('')}</div><span></span></div><div class="flbody">${body}</div></div>`; }""",
  """  const L=['账号','问卷'];   /* 2026-10-26 用户：整体只两个节点，三道题是"问卷"里面的事 */
  return `<div class="pg flow"><div class="flbar">${back?'<button class="back" id="flBack" aria-label="上一步">‹</button>':'<span></span>'}<ol class="flsteps" aria-label="第 ${step} 步，共 ${total} 步">${L.slice(0,total).map((l,i)=>`<li class="${i<step?'on':''} ${i===step-1?'cur':''}"><i>${i+1}</i>${l}</li>`).join('<li class="ln" aria-hidden="true"></li>')}</ol><span></span></div><div class="flbody">${body}</div></div>`; }""")
R("  showPage(flowHTML(1,4,`<div class=\"auth\">","  showPage(flowHTML(1,2,`<div class=\"auth\">")
R("    <div class=\"qzn\">${step+1} / ${QZ.length}</div><h1 class=\"qzt\">","    <div class=\"qzbar\" aria-label=\"第 ${step+1} 题，共 ${QZ.length} 题\">${QZ.map((_,i)=>`<i class=\"${i<=step?'on':''}\"></i>`).join('')}<span>${step+1} / ${QZ.length}</span></div><h1 class=\"qzt\">")
R("  showPage(first?flowHTML(step+2,4,body,true):","  showPage(first?flowHTML(2,2,body,true):")
R("  showPage(first?flowHTML(4,4,body):","  showPage(first?flowHTML(2,2,body):")
R("""  const body=`<div class="qz qzdone"><div class="qzn">好了</div>""","""  const body=`<div class="qz qzdone"><div class="qzbar">${QZ.map(()=>'<i class="on"></i>').join('')}<span>完成</span></div>""")

# ===== 2. 章回顾放进书里：每章末尾一行"回顾这一章"，读完这一章才出现；不再弹提示；轻重都有 =====
R("""  S.uDone[pu.k]=Date.now(); save();
  setTimeout(()=>toast(`<div class="tq">${pu.name}读完了。</div><button>看回顾</button>`,()=>unitRecap(pu.k),8000),400);
}""","""  S.uDone[pu.k]=Date.now(); save(); paintUEnd();
}
/* 每章末尾的"回顾这一章"：这一章读完了才出现（只讲读过的），点开才看；轻重都有，不弹窗（2026-10-26 用户：滑得快时提示总在后面才出来） */
function unitHasRecap(u){ return NOVEL?!!REC().find(x=>x['回']===u.k):true; }
function unitRead(u){ for(let j=u.first;j<u.end;j++) if(!isRd(j)) return false; return true; }
function paintUEnd(){ const U=UNITS(); document.querySelectorAll('.uend').forEach(e=>{ const u=U.find(x=>String(x.k)===e.dataset.u); const on=!!u&&unitRead(u)&&unitHasRecap(u);
  e.hidden=!on; if(on&&!e.innerHTML) e.innerHTML=`<button class="uebtn" data-ur="${esc(String(u.k))}">${ic('toc','')}回顾${NOVEL?'这一'+UNIT:'这一节'}</button>`; }); }""")
R("function unitDoneCheck(cur){\n  if(!heavy()||cur<1||jumping()) return;","function unitDoneCheck(cur){\n  if(cur<1||jumping()) return;")
R("""    const hu=HUI.find(x=>x.first===i);
    if(hu){ const [a,b]""","""    const hu=HUI.find(x=>x.first===i);
    if(hu&&i>0) h+=`<div class="uend" data-u="${huiOf(i-1).n}" hidden></div>`;
    if(hu){ const [a,b]""")
R("""    h+=`<div class="prop ${cls}" id="p${i}" data-i="${i}" tabindex="0" role="button" aria-label="命题 ${p.n}，点开解释" style="--rail:${rails?rails*8+2:0}px">""",
  """    if(i>0&&d===0) h+=`<div class="uend" data-u="${P.slice(0,i).filter(x=>depth(x.n)===0).pop()?.n||''}" hidden></div>`;
    h+=`<div class="prop ${cls}" id="p${i}" data-i="${i}" tabindex="0" role="button" aria-label="命题 ${p.n}，点开解释" style="--rail:${rails?rails*8+2:0}px">""")
R("""  h+=`<div class="endmark" id="endMark">""","""  if(NOVEL) h+=`<div class="uend" data-u="${HUI[HUI.length-1].n}" hidden></div>`;
  else { const lm=P.filter(x=>depth(x.n)===0).pop(); if(lm) h+=`<div class="uend" data-u="${lm.n}" hidden></div>`; }
  h+=`<div class="endmark" id="endMark">""")
R("""    const dh=e.target.closest('.dochd');""","""    const ur=e.target.closest('[data-ur]'); if(ur){ unitRecap(ur.dataset.ur); return; }
    const dh=e.target.closest('.dochd');""")
R("""  mainToast();\n}""","""  mainToast(); paintUEnd();\n}""")

# ===== 3. 答案快到了：书里不显示图标，只留提示条 =====
a=s.index("    Object.entries(S.soon||{}).forEach(([id,x])=>{ const sv=SUS.find(y=>y.id===id), mn=id[0]==='m'?S.notes.find(n=>'m'+n.id===id):null;")
b=s.index("  Object.keys(S.bm).forEach(i=>{const b=box(+i);")
s=s[:a]+s[b:]
R("  if(heavy()){ soonCheck();\n","  if(heavy()) soonCheck();   /* 2026-10-26 用户：答案快到了在书里不显示图标，只出提示条 */\n")

# ===== 4. 主线碎片揭晓：拼图卡 =====
R("""      cluePanel.last='done'; const ml=ML()&&isPiece(s.id)?`<small style="display:block;opacity:.75">主线拼上一块：${mlDone(D.main)} / ${D.main.pieces.length}</small>`:'';
      setTimeout(()=>toast(`<div class="tq">伏笔揭晓：${esc(s['问题'])}${ml}</div><button>看解释</button>`,()=>reveal(s.id,true),12000),calm()?0:900);""",
  """      cluePanel.last='done';
      if(ML()&&isPiece(s.id)) setTimeout(()=>mainReveal(s.id),calm()?0:900);   /* 主线的碎片：不走普通提示条，单独一张"拼上一块"的卡 */
      else setTimeout(()=>toast(`<div class="tq">伏笔揭晓：${esc(s['问题'])}</div><button>看解释</button>`,()=>reveal(s.id,true),12000),calm()?0:900);""")
R("function cluePanel(tab){","""/* 主线拼上一块：从底部升起一张卡——主线问题、拼图格（新的一块飞进来点亮）、这一块拼上了什么；最后一块 = 全部拼上。不挡阅读、不用点掉，几秒后自己落下 */
function mainReveal(id){
  const m=D.main, n=mlDone(m), N=m.pieces.length, k=m.pieces.indexOf(id), last=n===N, note=(m.notes||{})[id]||'';
  let el=$('#mlfx'); if(!el){ el=document.createElement('div'); el.id='mlfx'; el.setAttribute('role','status'); document.body.appendChild(el); }
  el.className=''; void el.offsetWidth;
  el.innerHTML=`<div class="mlfx-h"><span class="mltag">主线</span><span>${last?'全部拼上了':`拼上第 ${n} 块`}</span><span class="mlfx-c">${n} / ${N}</span></div>
    <div class="mlfx-q">${esc(m.q)}</div>
    <div class="mlfx-p">${m.pieces.map((p,i)=>`<i class="${S.doneS[p]?'on':''} ${i===k?'new':''}"></i>`).join('')}</div>
    <p class="mlfx-n">${esc(note)}</p>
    <div class="mlfx-a"><button id="mlfxAns">看这处伏笔</button><button id="mlfxMain">${last?'看完整的回答':'看主线'}</button></div>`;
  el.classList.add('show'); if(last) el.classList.add('done'); if(calm()) el.classList.add('calm');
  const live=$('#live'); if(live) live.textContent=`主线拼上一块，${n} / ${N}。${note}`;
  clearTimeout(mainReveal.t); const hide=()=>el.classList.remove('show'); mainReveal.t=setTimeout(hide,last?14000:9000);
  $('#mlfxAns').onclick=()=>{ hide(); reveal(id,true); }; $('#mlfxMain').onclick=()=>{ hide(); cluePanel('done'); };
}
function cluePanel(tab){""")
R("""    ${withEnd&&S.finished?`<p class="mlend">${esc(m.end)}</p>`:''}</div>`; }""",
  """    ${n&&!S.finished?`<ol class="mlnotes">${m.pieces.filter(id=>S.doneS[id]).map(id=>`<li>${esc((m.notes||{})[id]||'')}</li>`).join('')}</ol>`:''}
    ${withEnd&&S.finished?`<p class="mlend">${esc(m.end)}</p>`:''}</div>`; }""")
R("getMain:()=>D.main,","getMain:()=>D.main,mainReveal,paintUEnd,")

R("</style>",""".flsteps{display:flex;align-items:center;justify-content:center;gap:8px;margin:0;padding:0;list-style:none;font-size:var(--t-tag);color:var(--faint)}
.flsteps li{display:flex;align-items:center;gap:6px}
.flsteps li i{font-style:normal;width:18px;height:18px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1px var(--line);font-size:11px}
.flsteps li.on{color:var(--ink2)}
.flsteps li.on i{background:var(--ink);color:var(--paper);box-shadow:none}
.flsteps li.ln{width:28px;height:1px;background:var(--line)}
.qzbar{display:flex;align-items:center;gap:5px;margin-bottom:14px}
.qzbar i{width:16px;height:3px;border-radius:2px;background:var(--line)}
.qzbar i.on{background:var(--blue)}
.qzbar span{margin-left:6px;font-size:var(--t-tag);color:var(--faint);font-variant-numeric:tabular-nums}
.uend{display:flex;justify-content:center;margin:18px 0 6px}
.uend[hidden]{display:none}
.uebtn{display:inline-flex;align-items:center;gap:6px;font-family:var(--ui);font-size:var(--t-aux);color:var(--mute);padding:6px 14px;border-radius:16px;box-shadow:inset 0 0 0 1px var(--line)}
.uebtn svg{width:15px;height:15px}
.mlnotes{margin:10px 0 0;padding:0 0 0 1.4em;font-size:var(--t-aux);color:var(--ink2);line-height:1.75}
.mlnotes li::marker{color:var(--hl);font-variant-numeric:tabular-nums}
#mlfx{position:fixed;left:50%;bottom:calc(74px + var(--safe-b));width:calc(100% - 24px);max-width:536px;z-index:31;transform:translate(-50%,24px);opacity:0;visibility:hidden;background:var(--ink);color:var(--paper);border-radius:14px;padding:14px 16px 10px;font-family:var(--ui);box-shadow:0 10px 30px rgba(0,0,0,.18);transition:transform .45s cubic-bezier(.2,.9,.3,1.2),opacity .3s,visibility .3s}
#mlfx.show{transform:translate(-50%,0);opacity:1;visibility:visible}
#mlfx .mltag{background:var(--hl);color:#1F2A26}
.mlfx-h{display:flex;align-items:center;gap:8px;font-size:var(--t-tag);opacity:.9}
.mlfx-c{margin-left:auto;font-variant-numeric:tabular-nums}
.mlfx-q{font-family:var(--serif);font-size:var(--t-key);line-height:1.5;margin:8px 0 10px}
.mlfx-p{display:flex;gap:6px;flex-wrap:wrap}
.mlfx-p i{position:relative;width:18px;height:18px;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.28)}
.mlfx-p i.on{background:var(--hl);box-shadow:none}
#mlfx.show .mlfx-p i.new{animation:pieceIn .9s .25s cubic-bezier(.2,1.6,.4,1) both}
@keyframes pieceIn{0%{transform:translateY(-26px) rotate(-30deg) scale(.4);opacity:0}60%{opacity:1}100%{transform:none;opacity:1}}
#mlfx.show .mlfx-p i.new::after{content:"";position:absolute;inset:-6px;border-radius:7px;box-shadow:0 0 0 2px var(--hl);opacity:0;animation:pieceRing 1.2s .9s ease-out}
@keyframes pieceRing{0%{opacity:.9;transform:scale(.7)}100%{opacity:0;transform:scale(1.5)}}
.mlfx-n{font-family:var(--serif);font-size:var(--t-body);line-height:1.7;margin:12px 0 4px;opacity:0}
#mlfx.show .mlfx-n{animation:noteIn .6s 1s ease-out forwards}
@keyframes noteIn{to{opacity:1}}
.mlfx-a{display:flex;justify-content:flex-end;gap:14px;margin-top:4px}
.mlfx-a button{color:var(--hl);font-size:var(--t-aux);padding:6px 0}
#mlfx.done .mlfx-p i{animation:allLit .6s ease-out both}
#mlfx.done .mlfx-p i:nth-child(2){animation-delay:.08s}#mlfx.done .mlfx-p i:nth-child(3){animation-delay:.16s}#mlfx.done .mlfx-p i:nth-child(4){animation-delay:.24s}#mlfx.done .mlfx-p i:nth-child(5){animation-delay:.32s}#mlfx.done .mlfx-p i:nth-child(6){animation-delay:.4s}#mlfx.done .mlfx-p i:nth-child(7){animation-delay:.48s}#mlfx.done .mlfx-p i:nth-child(8){animation-delay:.56s}#mlfx.done .mlfx-p i:nth-child(9){animation-delay:.64s}
@keyframes allLit{0%{transform:scale(1)}50%{transform:scale(1.25);box-shadow:0 0 10px var(--hl)}100%{transform:scale(1)}}
#mlfx.calm,#mlfx.calm *{animation:none!important;transition:none!important}
#mlfx.calm .mlfx-n{opacity:1}
</style>""")
open(p,'w',encoding='utf-8').write(s); print('ok v945')
