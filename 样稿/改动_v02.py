"""样稿 v0.1 → v0.2（用户 10-27 四条）：毛笔 logo；注册只留账号密码；书架三种排列 + 四种排序 + 整理拖动 + 继续阅读。
用法：python3 样稿/改动_v02.py   （从 界面样稿_v0.1.html 生成 界面样稿_v0.2.html；每处替换断言只匹配 1 次）"""
import os
D=os.path.dirname(os.path.abspath(__file__))
s=open(os.path.join(D,'界面样稿_v0.1.html'),encoding='utf-8').read()
def rep(a,b):
    global s; n=s.count(a); assert n==1,(n,a[:70]); s=s.replace(a,b)

rep("<title>伏笔 · 界面样稿 v0.1</title>","<title>伏笔 · 界面样稿 v0.2</title>")
rep("<b>伏笔 · 界面样稿 v0.1</b>","<b>伏笔 · 界面样稿 v0.2</b>")

# ---- 毛笔 logo：笔杆（墨）+ 笔头一半在地平线上（朱实心）一半埋在下面（朱虚线） ----
i=s.index("const LOGO=c=>`"); j=s.index("`;",i)+2
s=s[:i]+r"""const LOGO=c=>`<svg class="logo" viewBox="0 0 40 40" aria-hidden="true">
  <clipPath id="u${c.slice(1)}"><rect width="40" height="25"/></clipPath><clipPath id="d${c.slice(1)}"><rect y="26.6" width="40" height="14"/></clipPath>
  <rect x="18.4" y="2.5" width="3.2" height="11" rx="1.2" fill="var(--ink)"/><rect x="17.2" y="12.6" width="5.6" height="2.4" rx=".8" fill="var(--ink)"/>
  <g clip-path="url(#u${c.slice(1)})"><path d="M17.4 15H22.6Q26 21 24.6 27.5Q23 33.5 20 38Q17 33.5 15.4 27.5Q14 21 17.4 15Z" fill="${c}"/></g>
  <g clip-path="url(#d${c.slice(1)})"><path d="M24.6 27.5Q23 33.5 20 38Q17 33.5 15.4 27.5" fill="none" stroke="${c}" stroke-width="1.4" stroke-dasharray="1.8 1.8" stroke-linecap="round"/></g>
  <path d="M5 25.8H35" stroke="var(--ink)" stroke-width="1.6" stroke-linecap="round"/></svg>`;"""+s[j:]

# ---- 注册：logo + 一句话 + 账号 + 密码 + 两个按钮 ----
i=s.index("function auth(){"); j=s.index("const BOOKS=")
s=s[:i]+r"""function auth(){
  return `<div class="auth">
    <div class="left"><div class="hero">
      <div class="mark">${LOGO(accent())}<b>伏笔</b></div>
      <p class="tag">不是帮你读完，是让你想读下去。</p>
    </div></div>
    <div class="right"><div class="form">
      <div class="fld"><label for="a1">手机号或邮箱</label><input id="a1" inputmode="email" autocomplete="username"></div>
      <div class="fld"><label for="a2">密码</label><input id="a2" type="password" autocomplete="new-password" placeholder="6～20 位，含字母和数字"></div>
      <button class="btn wide go">注册</button>
      <p class="alt"><button class="link">已有账号，登录</button><span class="sep">·</span><button class="link">先体验</button></p>
    </div></div>
  </div>`;
}
"""+s[j:]
rep(""".auth{min-height:100%;display:flex;flex-direction:column;padding:calc(var(--safe-t) + 24px) 32px calc(var(--safe-b) + 16px)}""",
    """.auth{min-height:100%;display:flex;flex-direction:column;justify-content:center;gap:48px;padding:calc(var(--safe-t) + 24px) 32px calc(var(--safe-b) + 48px)}""")
rep(""".hero .tag{margin-top:14px;""",""".hero .tag{margin-top:16px;""")
rep(""".form{margin-top:36px;display:flex;flex-direction:column;gap:16px}""",""".form{display:flex;flex-direction:column;gap:16px}""")
rep(""".hero .mark .logo{width:30px;height:30px}""",""".hero .mark .logo{width:44px;height:44px}""")
rep(""".logo{width:26px;height:26px;flex:none}""",""".logo{width:32px;height:32px;flex:none}""")

# ---- 书架：继续阅读 + 三种排列 + 四种排序 + 整理（拖动排序） ----
i=s.index("const BOOKS="); j=s.index("const P=[")
s=s[:i]+r"""let BOOKS=[
 {t:'红楼梦',a:'曹雪芹',c:'#3A2F3B',p:'读至第三回',pc:41,f:3,last:5,add:1},
 {t:'巴斯克维尔的猎犬',a:'柯南·道尔［英国］',c:'#34302A',p:'读至第二章',pc:12,f:2,last:4,add:5},
 {t:'呐喊',a:'鲁迅',c:'#5A2B24',p:'读至《故乡》',pc:62,f:1,last:3,add:3},
 {t:'逻辑哲学论',a:'维特根斯坦［奥地利］',c:'#2E3A44',p:'',pc:0,f:0,last:0,add:2},
 {t:'李鸿章传',a:'梁启超',c:'#2B3A33',p:'',pc:0,f:0,last:0,add:4},
 {t:'傲慢与偏见',a:'简·奥斯汀［英国］',c:'#47394A',p:'',pc:0,f:0,last:0,add:6},
 {t:'西游记',a:'吴承恩',c:'#3D3426',p:'读至第一回',pc:3,f:0,last:2,add:7},
 {t:'朝花夕拾',a:'鲁迅',c:'#2A3A3F',p:'',pc:0,f:0,last:0,add:8},
 {t:'瓦尔登湖',a:'亨利·梭罗［美国］',c:'#33402F',p:'',pc:0,f:0,last:1,add:9}];
let shv={lay:'grid',sort:'recent',edit:false,menu:false};
const SORTS=[['recent','最近阅读'],['added','加入时间'],['title','书名'],['manual','手动']];
function sortedBooks(){
  const b=BOOKS.slice();
  if(shv.sort==='recent') b.sort((x,y)=>y.last-x.last||y.add-x.add);
  if(shv.sort==='added') b.sort((x,y)=>y.add-x.add);
  if(shv.sort==='title') b.sort((x,y)=>x.t.localeCompare(y.t,'zh-Hans-CN'));
  return b;
}
const cover=(b,small)=>`<span class="cv ${small?'sm':''}" style="--c:${b.c}"><span class="slip ${b.t.length>5?'long':''}">${b.t}</span></span>`;
const prog=b=>b.pc?`<span class="pbar"><i style="width:${b.pc}%"></i></span>`:'';
function bookItem(b){
  const meta=b.p?`${b.p}　${b.pc}%`:'未读';
  const grip=shv.edit?`<span class="grip" aria-label="拖动调整顺序"><i></i><i></i><i></i></span>`:'';
  /* 书格：只有封面和书名，不放进度条、不放红色数字（用户 10-27：一排横线和红点会给人压力）。进度和未揭晓的伏笔在"列表"排列、书的详情里看 */
  if(shv.lay==='grid') return `<button class="gb" data-t="${b.t}" title="${b.t}">${cover(b)}<span class="gt">${b.t}</span>${grip}</button>`;
  if(shv.lay==='list') return `<button class="book" data-t="${b.t}">${cover(b)}<span class="bi"><span class="t">${b.t}</span><span class="a">${b.a}</span><span class="p">${meta}</span>${b.f?`<span class="f">${b.f} 处伏笔待揭晓</span>`:''}</span>${grip}</button>`;
  return `<button class="lb" data-t="${b.t}"><span class="lt">${b.t}</span><span class="la">${b.a.replace(/［.*］/,'')}</span><span class="lp">${b.pc?b.pc+'%':'未读'}</span>${grip}</button>`;
}
const LAYI={grid:'<path d="M4 4h6v7H4zM14 4h6v7h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>',list:'<path d="M4 5h4v6H4zM11 6h9M11 9h6M4 14h4v6H4zM11 15h9M11 18h6"/>',rows:'<path d="M4 6h16M4 12h16M4 18h16"/>'};
function shelf(){
  const cur=BOOKS.filter(b=>b.last).sort((x,y)=>y.last-x.last)[0];
  const list=sortedBooks();
  return `<div class="shelf ${shv.edit?'editing':''}">
    <div class="top">${LOGO(accent())}<b>伏笔</b><span class="me" aria-label="我的">读</span></div>
    ${cur&&!shv.edit?`<button class="cont"><span class="ck">继续阅读</span>${cover(cur,1)}<span class="ci"><span class="t">${cur.t}</span><span class="p">${cur.p}　${cur.pc}%</span>${prog(cur)}</span></button>`:''}
    <div class="shh"><h1>书架</h1>${shv.edit?`<div class="acts"><button class="link" id="eDone">完成</button></div>`:`<div class="acts"><button class="link">找书</button><span>·</span><button class="link">导入</button></div>`}</div>
    <div class="tools">
      ${shv.edit?`<span class="etip">拖动书籍调整顺序</span>`:`<button class="sortb" id="sortB" aria-haspopup="true" aria-expanded="${shv.menu}">${SORTS.find(x=>x[0]===shv.sort)[1]}<svg viewBox="0 0 12 12" width="10" height="10"><path d="M2.5 4.5L6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4"/></svg></button>
      ${shv.menu?`<div class="menu" role="menu">${SORTS.map(([k,l])=>`<button role="menuitemradio" aria-checked="${shv.sort===k}" data-sort="${k}">${l}</button>`).join('')}</div>`:''}`}
      <span class="lays">${shv.edit?'':Object.keys(LAYI).map(k=>`<button data-lay="${k}" aria-pressed="${shv.lay===k}" aria-label="${{grid:'书格',list:'列表',rows:'简表'}[k]}"><svg viewBox="0 0 24 24">${LAYI[k]}</svg></button>`).join('')}${shv.edit?'':`<button class="link edit" id="eBtn">整理</button>`}</span>
    </div>
    <div class="books lay-${shv.lay}" id="bookList">${list.map(bookItem).join('')}</div>
  </div>`;
}
function wireShelf(scr){
  scr.querySelectorAll('[data-lay]').forEach(b=>b.onclick=()=>{shv.lay=b.dataset.lay;render();});
  scr.querySelector('#sortB')?.addEventListener('click',()=>{shv.menu=!shv.menu;render();});
  scr.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{shv.sort=b.dataset.sort;shv.menu=false;render();});
  scr.querySelector('#eBtn')?.addEventListener('click',()=>{shv.edit=true;shv.menu=false;if(shv.sort!=='manual'){BOOKS=sortedBooks();}render();});
  scr.querySelector('#eDone')?.addEventListener('click',()=>{shv.edit=false;render();});
  if(!shv.edit) return;
  /* 拖动排序：按住书往上下（或左右）拖，松手落位；拖过之后排序自动变为"手动" */
  const box=scr.querySelector('#bookList'); let drag=null;
  box.querySelectorAll('[data-t]').forEach(el=>{
    el.addEventListener('pointerdown',e=>{ drag={el,t:el.dataset.t}; el.classList.add('drag'); el.setPointerCapture(e.pointerId); e.preventDefault(); });
    el.addEventListener('pointermove',e=>{ if(!drag||drag.el!==el) return;
      const over=document.elementsFromPoint(e.clientX,e.clientY).map(x=>x.closest&&x.closest('[data-t]')).find(x=>x&&x!==el&&box.contains(x));
      if(over){ const r=over.getBoundingClientRect(), after=shv.lay==='grid'?(e.clientX>r.left+r.width/2):(e.clientY>r.top+r.height/2); box.insertBefore(el,after?over.nextSibling:over); } });
    el.addEventListener('pointerup',()=>{ if(!drag) return; el.classList.remove('drag');
      const order=[...box.querySelectorAll('[data-t]')].map(x=>x.dataset.t); BOOKS.sort((x,y)=>order.indexOf(x.t)-order.indexOf(y.t)); shv.sort='manual'; drag=null; });
  });
}
"""+s[j:]
rep("""  scr.querySelectorAll('[data-open="z"]').forEach""","""  if(st.p==='shelf') wireShelf(scr);
  scr.querySelectorAll('[data-open="z"]').forEach""")

# ---- 书架样式 ----
rep(""".lan .shelf{""",""".cont{display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;column-gap:14px;align-items:center;width:100%;margin-top:20px;padding:14px 16px;border-radius:6px;background:var(--paper2);text-align:left}
.cont .ck{grid-column:1/3;font-size:var(--t-tag);color:var(--mute);margin-bottom:10px}
.cont .ci{display:flex;flex-direction:column;gap:4px;min-width:0}
.cont .t{font-family:var(--song);font-size:var(--t-key);font-weight:600}.cont .p{font-size:var(--t-aux);color:var(--ink2)}
.cv.sm{width:44px;height:61px}.cv.sm::before{left:4px;top:6px;bottom:6px}.cv.sm .slip{left:10px;top:6px;width:14px;min-height:32px;font-size:8px;line-height:14px;padding:2px 0}.cv.sm .slip.long{font-size:7px;line-height:11px;width:13px;left:10px;max-height:50px}
.pbar{display:block;height:2px;background:var(--line);border-radius:1px;overflow:hidden;margin-top:4px}.pbar i{display:block;height:2px;background:var(--ink)}
.shh{margin-top:28px}
.tools{position:relative;display:flex;align-items:center;margin-top:12px;height:32px}
.sortb{display:inline-flex;align-items:center;gap:4px;font-size:var(--t-aux);color:var(--ink2)}
.menu{position:absolute;z-index:5;top:34px;left:0;min-width:128px;padding:4px;border-radius:8px;background:var(--sheet);box-shadow:0 8px 24px rgba(0,0,0,.14)}
.menu button{display:block;width:100%;height:36px;padding:0 12px;text-align:left;font-size:var(--t-ui);border-radius:4px}
.menu button[aria-checked=true]{color:var(--dai)}.menu button[aria-checked=true]::after{content:"✓";float:right}
.lays{margin-left:auto;display:flex;align-items:center;gap:4px}
.lays button[data-lay]{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:6px;color:var(--faint)}
.lays button[data-lay][aria-pressed=true]{color:var(--ink);background:var(--paper2)}
.lays svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linejoin:round}
.lays .edit{margin-left:8px}
.etip{font-size:var(--t-aux);color:var(--mute)}
.books{margin-top:12px}
.books.lay-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px 16px;padding-top:6px;align-items:start}
.gb .cv{overflow:hidden}
.gb{position:relative;display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
.gb .cv{width:100%;height:auto;aspect-ratio:72/100}
.gb .cv::before{left:9%;top:8%;bottom:8%}
.gb .cv .slip{left:21%;top:8%;width:24%;min-height:46%;max-height:84%;font-size:12px;line-height:1.5;letter-spacing:.1em;padding:6px 0;overflow:hidden}
.gb .cv .slip.long{width:24%;left:21%;font-size:10px;line-height:1.35;letter-spacing:0;max-height:84%}
.gb .gt{width:100%;font-family:var(--song);font-size:var(--t-aux);line-height:1.4;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gb .pbar{width:100%;margin-top:-2px}
.gb .pnone{display:block;height:2px;margin-top:-2px}
.gb .gf{position:absolute;top:-6px;right:-6px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--zhu);color:#F6F2EC;font-size:11px;line-height:18px;text-align:center}
.lb{display:flex;align-items:center;gap:12px;width:100%;height:48px;border-bottom:1px solid var(--line);text-align:left}
.lb:first-child{border-top:1px solid var(--line)}
.lb .lt{font-family:var(--song);font-size:var(--t-ui);font-weight:600;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lb .la{font-size:var(--t-aux);color:var(--mute)}.lb .lp{width:36px;text-align:right;font-size:var(--t-aux);color:var(--ink2);font-variant-numeric:tabular-nums}
.lb .lf{width:18px;height:18px;border-radius:9px;background:var(--zhu);color:#F6F2EC;font-size:11px;line-height:18px;text-align:center}
.grip{display:flex;flex-direction:column;gap:3px;padding:6px;margin-left:8px;cursor:grab}.grip i{display:block;width:14px;height:1.5px;background:var(--faint);border-radius:1px}
.gb .grip{position:absolute;top:6px;right:6px;margin:0;background:var(--sheet);border-radius:4px}
.editing [data-t]{touch-action:none;cursor:grab}
.editing .gb .cv{animation:wig .32s ease-in-out infinite alternate}
@keyframes wig{from{transform:rotate(-.6deg)}to{transform:rotate(.6deg)}}
.drag{opacity:.85;z-index:3;box-shadow:0 8px 24px rgba(0,0,0,.18)}
.lan .books.lay-grid{grid-template-columns:repeat(6,minmax(0,1fr));gap:20px 16px}
.gb{min-width:0}
.lan .cont{display:none}
.lan .shelf{""")
rep(""".lan .books{display:grid;grid-template-columns:1fr 1fr;column-gap:40px}""",""".lan .books.lay-list{display:grid;grid-template-columns:1fr 1fr;column-gap:40px}
.lan .books.lay-rows{display:grid;grid-template-columns:1fr 1fr;column-gap:40px}
@media (prefers-reduced-motion:reduce){.editing .gb .cv{animation:none}}""")

# ---- 说明文字（只换第一处 render 定义前的位置：锚点带上紧跟的下一行，保证唯一） ----
rep("""const NOTES={""","""const NOTES0={""")
rep("""render=function(){
  const dev=""","""const NOTES={
 auth:'注册页只保留 logo、一句话、账号、密码和两个按钮；昵称改在“我的”里修改，注册时不问。logo 改为毛笔：笔头一半在地平线上，一半埋在下面。',
 shelf:'书架：顶部“继续阅读”一步回到上次的位置。右上角三种排列（书格 / 列表 / 简表），左侧切换排序（最近阅读 / 加入时间 / 书名 / 手动）。点“整理”后可拖动调整顺序，拖过之后排序自动变为“手动”。书格是默认排列，一屏能看十几本。',
 read:NOTES0.read, clue:NOTES0.clue};
render=function(){
  const dev=""")
open(os.path.join(D,'界面样稿_v0.2.html'),'w',encoding='utf-8').write(s)
print('ok')
