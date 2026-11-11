"""v9.57（10-28）第三阶段 C 阅读页（规范 v2 第六节 3）：
顶栏两行（上：章节名宋体；下：书名　进度，小字）；往下读顶栏和底部导航自动收起，往上滑、滑到书末或点正文时出现；
打开书时在上次的位置画一条"上次读到这里"分隔线（读过去三段后淡出）；页边伏笔标记改成竖排楷体批注（朱 = 书里的伏笔，黛 = 读者发现的；
没打开 = 朱色细框，打开了 = 细框，揭晓 = 实心朱底；答案处 = 实心"揭晓"）；伏笔那一句下面朱色圈点（着重号，到揭晓为止）；底部"伏笔"按钮朱色。
备份 Demo/模板_v72备份.html。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)

# ---------- 顶栏两行 ----------
rep("""  const w=$('#where'); if(w) w.innerHTML=cur>=0?`<b>${NOVEL?lab(P[cur].n):P[cur].n}</b><small>${pctOf()}%</small>`:(NOVEL?`<b>${unitName(HUI[0].n)}</b>`:'前言');""",
"""  const w=$('#where'); if(w) w.innerHTML=whereHTML(cur);""")
rep("/* 书末：没读完时只标\"完\"","""/* 顶栏（规范 v2）：上行章节名（小说写全"第一回　甄士隐梦幻识通灵"；短篇集《故乡》；哲学书写命题号），下行小字"书名　进度" */
function whereHTML(cur){
  const bt=esc((BOOKS[BK]||{}).t||''), pc=cur>=0?`　${pctOf()}%`:'';
  let top;
  if(NOVEL){ const h=cur>=0?huiOf(cur):HUI[0], nm=unitName(h.n), t=huiTitle(h.n).split(/\\s+|　/)[0]; top=D.imported||D.titled||h.n===0||!t?nm:`${nm}　${t}`; }
  else top=cur>=0?`命题 ${P[cur].n}`:'前言';
  return `<b>${esc(top)}</b><small>${bt}${pc}</small>`;
}
/* 书末：没读完时只标"完\"""")

# ---------- 往下读自动收起顶栏和导航 ----------
rep("""    $('#bar')?.classList.toggle('scrolled',scrollY>4); tickRead();""",
"""    $('#bar')?.classList.toggle('scrolled',scrollY>4); tickRead(); chromeTick(); lastLineTick();""")
rep("/* 跳转（导览、搜索、引用、回到出处、打开书）期间不记\"读过\"","""/* 读的时候顶栏和底部导航自动收起：往下滑超过一屏的 1/6 收起；往上滑、回到顶部、滑到书末、点正文时出现。跳转期间不动 */
let chromeY=0;
function chromeTick(){ const a=$('#app'); if(!a) return; const y=scrollY, dy=y-chromeY, bottom=innerHeight+y>=document.body.scrollHeight-40;
  if(jumping()||y<80||bottom||$('#sheet').classList.contains('show')){ a.classList.remove('calmread'); chromeY=y; return; }
  if(dy>innerHeight/6){ a.classList.add('calmread'); chromeY=y; } else if(dy<-24){ a.classList.remove('calmread'); chromeY=y; } else if(dy<0) chromeY=Math.max(chromeY,y); else if(!a.classList.contains('calmread')) chromeY=Math.min(chromeY,y); }
const showChrome=()=>{ $('#app')?.classList.remove('calmread'); chromeY=scrollY; };
/* "上次读到这里"：打开书时画在上次的位置上方；往后读过三段就淡出 */
function lastLineTick(){ const l=$('#lastLine'); if(!l||jumping()) return; if(S.current>=+l.dataset.i+3){ l.classList.add('gone'); setTimeout(()=>l.remove(),400); } }
/* 跳转（导览、搜索、引用、回到出处、打开书）期间不记"读过\"""")
rep("""  $('#text').addEventListener('click',e=>{
    if(hasSel()) return;""","""  $('#text').addEventListener('click',e=>{
    if(hasSel()) return; showChrome();""")
rep("""  if(S.current>=0) requestAnimationFrame(()=>els[S.current].scrollIntoView({block:'start'}));
  else window.scrollTo(0,0);""","""  if(S.current>=0){ const ll=document.createElement('div'); ll.id='lastLine'; ll.className='lastline'; ll.dataset.i=S.current; ll.setAttribute('role','separator'); ll.innerHTML='<span>上次读到这里</span>';
    if(S.current>0&&fromShelf){ const el=els[S.current], at=el.closest('.doc.folded')||el; at.parentNode.insertBefore(ll,at); }
    requestAnimationFrame(()=>els[S.current].scrollIntoView({block:'start'})); }
  else window.scrollTo(0,0);
  showChrome();""")

# ---------- 页边批注：竖排楷体 ----------
rep("""${st==='solved'?ic('gemok','big'):'<span class="gem"></span>'}</button>`""","""${st==='solved'?ic('gemok','big'):'<span class="gem"></span>'}<span class="mz">伏笔</span></button>`""")
rep("""${n.done?ic('gemok','big'):'<span class="gem"></span>'}</button>`""","""${n.done?ic('gemok','big'):'<span class="gem"></span>'}<span class="mz">伏笔</span></button>`""")
rep("""data-ans="${s.id}" aria-label="伏笔在此揭晓，查看">${ic('check','')}</button>`""","""data-ans="${s.id}" aria-label="伏笔在此揭晓，查看">${ic('check','')}<span class="mz">揭晓</span></button>`""")
rep("""data-mans="${n.id}" aria-label="你发现的伏笔在此揭晓，查看">${ic('check','')}</button>`""","""data-mans="${n.id}" aria-label="你发现的伏笔在此揭晓，查看">${ic('check','')}<span class="mz">揭晓</span></button>`""")
# 批注高度不再固定 26：按实际高度居中、往下错开
rep("""      .forEach(({m,y})=>{ const h=26, top=Math.max(y-h/2,floor); m.style.top=top+'px'; floor=top+h+4; });""",
"""      .forEach(({m,y})=>{ const h=m.offsetHeight||26, top=Math.max(y-h/2,floor); m.style.top=top+'px'; floor=top+h+4; });""")

# ---------- 圈点：伏笔那一句下面朱色着重号（发现后到揭晓前） ----------
rep("""  document.querySelectorAll('.marks').forEach(m=>m.innerHTML='');
  reachedClues().forEach(s=>{""","""  document.querySelectorAll('.marks').forEach(m=>m.innerHTML='');
  paintDots();
  reachedClues().forEach(s=>{""")
rep("/* 底部“伏笔”按钮上的特效","""function paintDots(){
  document.querySelectorAll('#text mark.cd').forEach(m=>{const p=m.parentNode; while(m.firstChild)p.insertBefore(m.firstChild,m); p.removeChild(m); p.normalize();});
  reachedClues().filter(s=>!S.doneS[s.id]&&s['提出锚句']).forEach(s=>{ const rg=clueRange(s,'src'); if(!rg) return;
    rg.forEach(pt=>{ const C=cOf(pt.c); if(!C||!visEl(C)) return;
      const w=document.createTreeWalker(C,NodeFilter.SHOW_TEXT); const nodes=[]; let n; while((n=w.nextNode()))nodes.push(n);
      let pos=0; nodes.forEach(tn=>{ const a=pos,b=pos+tn.length; pos=b; const st=Math.max(pt.s,a),e=Math.min(pt.e,b); if(e<=st) return;
        let x=tn; if(st>a) x=x.splitText(st-a); if(e<b) x.splitText(e-st);
        const m=document.createElement('mark'); m.className='cd'; x.parentNode.insertBefore(m,x); m.appendChild(x); }); }); });
}
/* 底部“伏笔”按钮上的特效""")

CSS=r'''
/* ===== v9.57 阅读页（规范 v2 第六节 3） ===== */
.bar{display:grid;grid-template-columns:72px 1fr auto;align-items:center;height:calc(52px + var(--safe-t));padding:var(--safe-t) 12px 0;gap:0;transition:transform .28s var(--ease),opacity .2s,border-color .2s}
.bar .back{justify-self:start;font-size:var(--t-aux);color:var(--ink2)}
.bar .where{min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;color:var(--ink);font-family:var(--serif);line-height:1.25}
.bar .where b{max-width:100%;font-size:14px;font-weight:600;letter-spacing:.06em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .where small{margin:0;font-family:var(--ui);font-size:10px;color:var(--faint);letter-spacing:0;white-space:nowrap;font-variant-numeric:tabular-nums}
.bar>.aa,.bar>.lg{justify-self:end}
.bar:has(.lg){grid-template-columns:72px 1fr auto auto}
.bar::after{height:2px;opacity:1;background:var(--line);bottom:0}
.prog{height:2px;bottom:0;background:var(--ink);opacity:1;border-radius:0}
.nav{height:calc(56px + var(--safe-b));padding:0 6px var(--safe-b);align-items:center;transition:transform .28s var(--ease),opacity .2s}
.nav button{letter-spacing:.06em;gap:3px}
.nav #nClue{color:var(--hl)}
.nav #nClue svg.i{width:24px;height:24px;stroke-width:1.8}
.calmread .bar{transform:translateY(-100%);opacity:0;pointer-events:none}
.calmread .nav{transform:translate(-50%,100%);opacity:0;pointer-events:none}
@media (prefers-reduced-motion:reduce){.calmread .bar,.calmread .nav{transition:none}}
/* 上次读到这里 */
.lastline{display:flex;align-items:center;gap:12px;margin:4px 0 12px;color:var(--faint);font-family:var(--ui);font-size:var(--t-tag);line-height:1;transition:opacity .4s}
.lastline::before,.lastline::after{content:"";flex:1;height:1px;background:var(--line)}
.lastline.gone{opacity:0}
/* 章名 */
.hui{margin:48px 0 24px}
.hui:first-child{margin-top:24px}
.hui .hn{letter-spacing:.4em;margin-right:-.4em;margin-bottom:8px}
.hui::after{display:none}
/* 页边批注：竖排楷体小字。朱 = 书里的伏笔（没打开：朱色细框 + 轻轻呼吸；打开过：细框；揭晓：实心）；黛 = 读者发现的 */
.mk.clue,.mk.answer{width:22px;height:auto;min-height:0;margin:0 2px;padding:6px 0;border-radius:2px;background:transparent;box-shadow:inset 0 0 0 1px color-mix(in srgb,currentColor 40%,transparent);animation:none}
.mk.clue::before,.mk.clue .gem,.mk.clue svg,.mk.answer svg{display:none}
.mk .mz{writing-mode:vertical-rl;font-family:var(--kai);font-size:13px;line-height:1;letter-spacing:.2em;margin-bottom:-.2em}
.mk.clue{color:var(--hl)}
.mk.clue:not(.seen):not(.solved){box-shadow:inset 0 0 0 1px var(--hl);animation:mzIn 2.4s ease-in-out infinite}
@keyframes mzIn{50%{background:var(--hl-soft)}}
.mk.clue.solved{color:var(--hl);opacity:.55}
.mk.answer{background:var(--hl);color:var(--on-hl);box-shadow:none}
.mk.answer.fresh{animation:none;box-shadow:0 0 0 3px var(--hl-soft)}
.mk.clue.mine,.mk.clue.mine.seen{color:var(--blue);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--blue) 45%,transparent)}
.mk.answer.mine{background:var(--blue);color:var(--paper);box-shadow:none}
.marks.abs{width:26px}
.marks.abs .mk{left:2px}
@media (prefers-reduced-motion:reduce){.mk.clue:not(.seen):not(.solved){animation:none}}
/* 圈点：伏笔那一句下面朱色着重号 */
mark.cd{background:none;color:inherit;-webkit-text-emphasis:filled dot var(--hl);text-emphasis:filled dot var(--hl);-webkit-text-emphasis-position:under right;text-emphasis-position:under right}
'''
rep('</style>',CSS+'</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
