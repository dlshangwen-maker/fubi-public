"""样稿 v0.2 → v0.3（用户 10-27："没问题"，按规范改阅读页和面板）。
阅读页：顶栏和导航读的时候自动收起、点正文中间唤出；"上次读到这里"分隔线；章名；页边批注；横屏批注栏。
面板：统一结构（拖动条 → 标题行 → 内容 → 底部操作）；伏笔卡、解释卡、笔记三种；面板里进下一层原地替换、左上角"‹"；竖屏下拉关闭；横屏居中。
提示条：一种样式；"写下猜想 → 已保存 · 撤销"示范。
用法：python3 样稿/改动_v03.py   （从 界面样稿_v0.2.html 生成 界面样稿_v0.3.html）"""
import os,subprocess,sys
D=os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable,os.path.join(D,'改动_v02.py')],check=True)
s=open(os.path.join(D,'界面样稿_v0.2.html'),encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:70]); s=s.replace(a,b)

rep("<title>伏笔 · 界面样稿 v0.2</title>","<title>伏笔 · 界面样稿 v0.3</title>")
rep("<b>伏笔 · 界面样稿 v0.2</b>","<b>伏笔 · 界面样稿 v0.3</b>")
rep("""<button data-p="clue">伏笔卡</button>""","""<button data-p="clue">伏笔卡</button><button data-p="card">解释</button><button data-p="notes">笔记</button>""")

# ---------------- 阅读页 ----------------
i=s.index("function read(){"); j=s.index("function clue(){")
s=s[:i]+r"""function read(){
  const tags=x=>x.map(([k,t])=>`<button class="${k}" data-open="${k}">${st.v==='case'?(k==='z'?'线索':'想法'):t}</button>`).join('');
  const side=`<aside class="side" aria-label="批注">
    <div class="ml"><div class="h"><span class="seal zhu">主线</span><span class="k">已拼上 1 / 5</span></div><p class="q">一僧一道要把那块石头带去“温柔富贵之乡”——那究竟是怎样一户人家？</p><div class="sq" aria-label="已拼上 1 块，已出现 1 块，共 5 块"><i class="on"></i><i class="found"></i><i></i><i></i><i></i></div></div>
    <button class="pz d" data-open="d"><small>我的想法　第一回</small>真与假、有与无，像是在提醒读者别太当真。</button>
    <button class="pz" data-open="z"><small>伏笔　第一回</small>僧人为什么说英莲是“有命无运、累及爹娘之物”？</button>
  </aside>`;
  return `<div class="rd v-${st.v} ${st.chrome?'':'calm'}">
    <div class="main"><div class="bar"><button class="back">‹ 书架</button><div class="where">第一回　甄士隐梦幻识通灵<small>红楼梦　7%</small></div><button class="bm" aria-label="添加书签" aria-pressed="false"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6">${I.bm}</svg></button></div>
    <div class="prog"><i></i></div>
    <div class="body" id="rbody"><div class="page"><div class="txt">
      <header class="hui"><p class="n">第一回</p><h2>甄士隐梦幻识通灵<br>贾雨村风尘怀闺秀</h2></header>
      ${P.map(([n,t,m,k],ix)=>`${ix===1?'<div class="lastline" role="separator"><span>上次读到这里</span></div>':''}<p class="para ${k||''}" data-n="${n}">${m.length?t.replace('@@',`<span class="mg">${tags(m)}</span>`):t}</p>`).join('')}
    </div>${side}</div></div></div>
    <nav class="nav" aria-label="阅读工具"><button>${ic('toc')}导览</button><button class="fb" data-open="list">${ic('clue')}伏笔<span class="c">1</span></button><button data-open="notes">${ic('note')}笔记</button><button>${ic('aa')}设置</button></nav>
    <div class="toast" id="toast" role="status"></div>
  </div>`;
}
"""+s[j:]
rep("""let st={p:'read',v:'anno',o:'por',sheet:false}; var render;""","""let st={p:'read',v:'anno',o:'por',sheet:false,chrome:true,panel:'clue',guess:''}; var render;""")

# ---------------- 面板 ----------------
i=s.index("function clue(){"); j=s.index("const NOTES0={")
s=s[:i]+r"""/* 面板统一结构：拖动条 → 标题行（返回 · 标题 · 关闭）→ 内容 → 底部操作（次按钮靠左，主按钮靠右） */
const panel=(ttl,body,foot,back)=>`<div class="shd">${back?`<button class="x bk" data-back="${back}" aria-label="返回">‹</button>`:''}<span class="ttl">${ttl}</span><button class="x" aria-label="关闭" data-close>×</button></div>
  <div class="shb">${body}</div>${foot?`<div class="shf">${foot}</div>`:''}`;
function clue(){
  if(st.panel==='guess') return panel('写下猜想',`
    <p class="qq">僧人为什么说英莲是“有命无运、累及爹娘之物”？</p>
    <div class="fld" style="margin-top:20px"><label for="gs">你的猜想</label><textarea id="gs" rows="4" placeholder="只有你自己能看到">${st.guess}</textarea></div>
    <div class="conf"><span>把握</span>${[3,5,7,9].map(n=>`<button aria-pressed="${n===5}">${n} 成</button>`).join('')}</div>`,
    `<button class="btn ghost" data-back="clue">取消</button><button class="btn" id="gSave">保存</button>`,'clue');
  if(st.panel==='list') return panel('伏笔',`
    <div class="mainl"><div class="mlh"><span class="seal zhu">主线</span><span class="mlc">已拼上 1 / 5</span></div><p class="mlq">一僧一道要把那块石头带去“温柔富贵之乡”——那究竟是怎样一户人家？</p><div class="sq"><i class="on"></i><i class="found"></i><i></i><i></i><i></i></div></div>
    <div class="seg" role="tablist"><button role="tab" aria-selected="true">待揭晓　2</button><button role="tab" aria-selected="false">已揭晓　1</button></div>
    <button class="li" data-go="clue"><span class="lh"><span class="seal zhu-o">主线</span><span>第一回</span></span><span class="lq">僧人为什么说英莲是“有命无运、累及爹娘之物”？</span></button>
    <button class="li"><span class="lh"><span>第一回</span></span><span class="lq">绛珠草要把一生的眼泪还给神瑛侍者，眼泪怎么能还？</span></button>`,'');
  if(st.panel==='notes') return panel('笔记',`
    <div class="seg" role="tablist"><button role="tab" aria-selected="true">全部　3</button><button role="tab" aria-selected="false">划线</button><button role="tab" aria-selected="false">想法</button><button role="tab" aria-selected="false">疑问</button></div>
    <div class="ni"><span class="nh">第一回　划线</span><p class="nq d">“假作真时真亦假，无为有处有还无。”</p><p class="nt">真与假、有与无，像是在提醒读者别太当真。</p></div>
    <div class="ni"><span class="nh">第一回　疑问</span><p class="nt">一僧一道和梦里的僧道是同一对人吗？</p></div>
    <div class="ni"><span class="nh">第一回　划线</span><p class="nq d">“好防佳节元宵后，便是烟消火灭时。”</p></div>`,
    `<button class="btn ghost">导出读书札记</button>`);
  if(st.panel==='card') return panel('第一回',`
    <div class="seg" role="tablist"><button role="tab" aria-selected="false">入门</button><button role="tab" aria-selected="true">标准</button><button role="tab" aria-selected="false">深入</button></div>
    <p class="cw">梦醒后僧道真身出现于街头，形貌由“骨格不凡”变为疯癫邋遢。</p>
    <p class="ce">梦中僧道仙风道骨，现实中却是“癞头跣足”“跛足蓬头”的模样，原文没有明说他们是不是同一对人。“有命无运”字面意思是有生命而无好运气。甄士隐“知是疯话，也不睬他”，与他梦中恭敬求教的态度形成对比。</p>
    <div class="cb"><span>背景知识</span>癞头：头上长癞疮。施主：僧人对布施者的称呼。粉妆玉琢：形容孩子白净可爱。</div>`,
    `<button class="btn ghost">划线</button><button class="btn ghost">写想法</button><button class="btn ghost" style="margin-left:auto">提问</button>`);
  return panel('伏笔',`
    <div class="mlrow"><span class="seal zhu-o">主线</span><span>一僧一道要把那块石头带去“温柔富贵之乡”——那究竟是怎样一户人家？</span></div>
    <p class="src"><small>第一回</small>那僧便大哭起来，又向士隐道：“施主，你把这<span class="dot">有命无运累及爹娘之物</span>抱在怀内作甚？”</p>
    <p class="qq">僧人为什么说英莲是“有命无运、累及爹娘之物”？</p>
    ${st.guess?`<div class="gv"><span>我的猜想　5 成把握</span>${st.guess}</div>`:''}
    <p class="hint">读到答案处会自动揭晓。</p>`,
    `<button class="btn ghost" data-close>继续阅读</button><button class="btn" data-go="guess">${st.guess?'修改猜想':'写下猜想'}</button>`,st.from==='list'?'list':'');
}
"""+s[j:]
rep("""  scr.innerHTML=h+`<div class="scrim ${st.p==='clue'||st.sheet?'on':''}" data-close></div><div class="sh ${st.p==='clue'||st.sheet?'on':''}"><div class="grab"></div>${clue()}</div>`;""",
"""  const showSheet=['clue','card','notes'].includes(st.p)||st.sheet;
  if(['card','notes'].includes(st.p)&&!st.sheet) st.panel=st.p;
  scr.innerHTML=h+`<div class="scrim ${showSheet?'on':''}" data-close></div><div class="sh ${showSheet?'on':''}" id="sheet"><div class="grab" aria-hidden="true"></div>${clue()}</div>`;""")
rep("""  scr.querySelectorAll('[data-open="z"]').forEach(b=>b.onclick=()=>{st.sheet=true;render();});
  scr.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{st.sheet=false;if(st.p==='clue')st.p='read';render();});""",
"""  const openP=(k,from)=>{st.sheet=true;st.panel=k;st.from=from||'';render();};
  scr.querySelectorAll('[data-open="z"]').forEach(b=>b.onclick=e=>{e.stopPropagation();openP('clue');});
  scr.querySelectorAll('[data-open="list"]').forEach(b=>b.onclick=()=>openP('list'));
  scr.querySelectorAll('[data-open="notes"]').forEach(b=>b.onclick=()=>openP('notes'));
  scr.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{ const k=b.dataset.go; st.from=(st.panel==='list'&&k==='clue')?'list':st.from; st.panel=k; render(); });
  scr.querySelectorAll('[data-back]').forEach(b=>b.onclick=()=>{ st.panel=b.dataset.back; render(); });
  const close=()=>{ st.sheet=false; st.panel='clue'; st.from=''; if(['clue','card','notes'].includes(st.p)) st.p='read'; render(); };
  scr.querySelectorAll('[data-close]').forEach(b=>b.onclick=close);
  scr.querySelector('#gSave')?.addEventListener('click',()=>{ const v=scr.querySelector('#gs').value.trim(); st.guess=v||'英莲会遭难，并连累家里。'; st.panel='clue'; render(); toast('已保存','撤销',()=>{st.guess='';render();}); });
  /* 点正文：中间三分之一 = 唤出 / 收起顶栏和导航；其余位置 = 打开这一段的解释 */
  const body=scr.querySelector('#rbody');
  if(body){
    body.addEventListener('click',e=>{ if(e.target.closest('button')) return; const r=body.getBoundingClientRect(), y=e.clientY-r.top;
      if(y>r.height/3&&y<r.height*2/3&&!e.target.closest('.para')){ st.chrome=!st.chrome; scr.querySelector('.rd').classList.toggle('calm',!st.chrome); return; }
      if(e.target.closest('.para')){ st.sheet=true; st.panel='card'; render(); } });
    let y0=0; body.addEventListener('scroll',()=>{ const y=body.scrollTop, d=y-y0; y0=y; if(Math.abs(d)<6) return; st.chrome=d<0||y<8; scr.querySelector('.rd').classList.toggle('calm',!st.chrome); },{passive:true});
  }
  /* 竖屏下拉关闭面板 */
  const sh=scr.querySelector('#sheet.on');
  if(sh&&st.o==='por'){ let sy=null,dy=0; const g=sh.querySelector('.grab'), hd=sh.querySelector('.shd');
    [g,hd].forEach(el=>el&&el.addEventListener('pointerdown',e=>{ if(e.target.closest('button')) return; sy=e.clientY; dy=0; sh.style.transition='none'; el.setPointerCapture(e.pointerId); }));
    [g,hd].forEach(el=>el&&el.addEventListener('pointermove',e=>{ if(sy===null) return; dy=Math.max(0,e.clientY-sy); sh.style.transform=`translateY(${dy}px)`; }));
    [g,hd].forEach(el=>el&&el.addEventListener('pointerup',()=>{ if(sy===null) return; sh.style.transition=''; sh.style.transform=''; sy=null; if(dy>80) close(); }));
  }""")
rep("""function fit(){""","""function toast(msg,act,fn){ const t=document.querySelector('#toast'); if(!t) return; t.innerHTML=`<span>${msg}</span>${act?`<button>${act}</button>`:''}<button class="tx" aria-label="关闭">×</button>`; t.classList.add('on');
  clearTimeout(toast.t); toast.t=setTimeout(()=>t.classList.remove('on'),4000); const b=t.querySelector('button:not(.tx)'); if(b) b.onclick=()=>{t.classList.remove('on');fn&&fn();}; t.querySelector('.tx').onclick=()=>t.classList.remove('on'); }
function fit(){""")
rep("""  if(onlyRead&&st.p!=='read'&&st.p!=='clue') st.p='read';""","""  if(onlyRead&&!['read','clue','card','notes'].includes(st.p)) st.p='read';""")

# ---------------- 样式 ----------------
rep("""/* ---------- 对比：纸本、线索档案 ---------- */""",r"""/* ---------- v0.3：阅读页 ---------- */
/* 顶栏：上行章节名（宋体），下行书名 + 进度（小字）。用户 10-27 问显示书名还是章节名——章节名为主，书名小字保留 */
.bar .where{max-width:100%;overflow:hidden}
.bar .where{white-space:nowrap;text-overflow:ellipsis}
.bar .where small{white-space:nowrap}
.bar,.prog,.nav{transition:transform .28s cubic-bezier(.2,.8,.2,1),opacity .2s}
.rd.calm .bar,.rd.calm .prog{transform:translateY(-100%);opacity:0;pointer-events:none}
.rd.calm .nav{transform:translateY(100%);opacity:0;pointer-events:none}
.rd.calm .body{margin-top:-50px;margin-bottom:calc(-56px - var(--safe-b))}
.lan .rd.calm .nav{transform:translateX(-100%)}
.lan .rd.calm .body{margin-top:-42px;margin-bottom:0}
.lan .rd.calm .main{margin-left:calc(-56px - var(--safe-l))}
.body{transition:margin .28s cubic-bezier(.2,.8,.2,1)}
.lastline{display:flex;align-items:center;gap:12px;margin:4px 0 16px;color:var(--faint);font-size:var(--t-tag)}
.lastline::before,.lastline::after{content:"";flex:1;height:1px;background:var(--line)}
.hui{margin:16px 0 28px}
.hui .n{font-size:var(--t-tag);letter-spacing:.4em;margin-right:-.4em}
.toast{position:absolute;z-index:20;left:16px;right:16px;bottom:calc(56px + var(--safe-b) + 12px);display:flex;align-items:center;gap:12px;min-height:44px;padding:0 8px 0 16px;border-radius:8px;background:var(--ink);color:var(--paper);font-size:var(--t-aux);transform:translateY(12px);opacity:0;pointer-events:none;transition:transform .2s,opacity .2s}
.toast.on{transform:none;opacity:1;pointer-events:auto}
.toast span{flex:1}.toast button{color:#E8C9A0;font-size:var(--t-aux);height:32px;padding:0 8px}.toast .tx{color:var(--paper);opacity:.6;font-size:16px}
.lan .toast{left:auto;right:calc(var(--safe-r) + 24px);width:320px;bottom:calc(var(--safe-b) + 16px)}
/* ---------- v0.3：面板 ---------- */
.shd .bk{margin-left:-8px;margin-right:2px;font-size:22px;color:var(--ink2)}
.shd .bk+.ttl{margin-left:0}
textarea{width:100%;padding:10px 12px;border-radius:6px;border:1px solid var(--line);background:var(--paper);font:inherit;font-family:var(--kai);font-size:16px;line-height:1.7;color:var(--ink);resize:none}
textarea::placeholder{font-family:var(--ui);font-size:var(--t-ui);color:var(--faint)}
.conf{display:flex;align-items:center;gap:8px;margin-top:16px;font-size:var(--t-aux);color:var(--mute)}
.conf span{margin-right:4px}
.conf button{height:30px;padding:0 12px;border-radius:15px;box-shadow:inset 0 0 0 1px var(--line);font-size:var(--t-aux);color:var(--ink2)}
.conf button[aria-pressed=true]{background:var(--ink);color:var(--paper);box-shadow:none}
.gv{margin-top:16px;padding:12px 14px;border-radius:6px;background:var(--paper2);font-family:var(--kai);font-size:15px;line-height:1.7;color:var(--ink)}
.gv span{display:block;font-family:var(--ui);font-size:var(--t-tag);color:var(--mute);margin-bottom:4px}
.seg{display:flex;gap:2px;margin:4px 0 16px;padding:2px;border-radius:8px;background:var(--paper2)}
.seg button{flex:1;height:32px;border-radius:6px;font-size:var(--t-aux);color:var(--mute)}
.seg button[aria-selected=true]{background:var(--sheet);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.06)}
.mainl{margin-bottom:16px;padding:14px 16px;border-radius:6px;background:var(--paper2)}
.mlh{display:flex;align-items:center;gap:8px;font-size:var(--t-tag);color:var(--mute)}.mlh .mlc{margin-left:auto}
.mlq{margin-top:8px;font-family:var(--kai);font-size:16px;line-height:1.7;color:var(--ink)}
.li{display:flex;flex-direction:column;gap:6px;width:100%;padding:14px 0;border-top:1px solid var(--line);text-align:left}
.lh{display:flex;align-items:center;gap:8px;font-size:var(--t-tag);color:var(--mute)}
.lq{padding-left:12px;border-left:2px solid var(--zhu);font-family:var(--kai);font-size:16px;line-height:1.7;color:var(--ink)}
.qq{font-family:var(--kai)}
.ni{padding:14px 0;border-top:1px solid var(--line)}
.ni .nh{display:block;font-size:var(--t-tag);color:var(--mute);margin-bottom:6px}
.ni .nq{font-family:var(--song);font-size:15px;line-height:1.8;color:var(--ink)}
.ni .nq.d{padding-left:12px;border-left:2px solid var(--dai)}
.ni .nt{margin-top:6px;font-family:var(--kai);font-size:15px;line-height:1.7;color:var(--dai)}
.cw{font-family:var(--song);font-size:17px;line-height:1.7;color:var(--ink)}
.ce{margin-top:12px;font-size:15px;line-height:1.8;color:var(--ink2)}
.cb{margin-top:16px;padding:12px 14px;border-radius:6px;background:var(--paper2);font-size:var(--t-aux);line-height:1.7;color:var(--ink2)}
.cb span{display:block;font-weight:600;font-size:var(--t-tag);color:var(--mute);margin-bottom:4px}
.shf .btn{height:40px}
.lan .sh{max-height:92%}

/* ---------- 对比：纸本、线索档案 ---------- */""")
# notes
rep(""" read:NOTES0.read, clue:NOTES0.clue};""",""" read:'阅读页：往下读时顶栏和导航自动收起，往上滑或点正文中间唤出；回到书里时，正文中有一条“上次读到这里”，读过去即消失。伏笔那一句加朱色圈点，页边竖排楷体朱字“伏笔”，自己的想法为黛蓝。点段落打开解释。横屏：左侧导航、右侧批注栏（主线 + 拼图格 + 本屏批注）。',
 clue:'伏笔卡：标题 → 主线（一行）→ 出处原文（圈点）→ 问题（楷体，朱色竖线）→ 一句说明 → 底部操作。点“写下猜想”原地换成填写页（左上角“‹”返回），保存后出提示条“已保存 · 撤销”。竖屏可下拉关闭，横屏居中。',
 card:'解释：三档切换（入门 / 标准 / 深入）→ 白话一句 → 展开 → 背景知识；底部是这一段能做的事（划线、写想法、提问）。',
 notes:'笔记：顶部分类（全部 / 划线 / 想法 / 疑问），每条写清在第几回、是什么；划线是黛蓝竖线，想法是黛蓝楷体。底部只有一个操作：导出读书札记。'};""")
open(os.path.join(D,'界面样稿_v0.3.html'),'w',encoding='utf-8').write(s)
print('ok')
