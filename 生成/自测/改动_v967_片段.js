### needLogin
/* v9.67（用户 10-30）：没登录的页面和登录后几乎一样——排序、排列、找书、导入都在；只是点到"用"的时候才要求登录，登录后回到原处。
   guard(动作, 提示)：已登录直接做；没登录先去登录页，登录（和问卷）完成后接着做 */
const guard=(f,hint)=>{ if(curUser()||(window.__TEST&&!window.__GUESTCHK)) return f(); AFTER_LOGIN=f; AFTER_T=hint||''; authPage('login'); };
### shelfRender
function shelf(){
  window.onscroll=null; closeSheet(); dropBookTips(); lastAct=0; saveProf(true);
  if(S&&S.inBook){S.lastClose=Date.now();S.inBook=false;save();}
  const guest=!curUser()&&!(window.__TEST&&!window.__GUESTCHK);
  const v=shv(), st=Object.fromEntries(SHELF.map(([k])=>[k,bookStat(k)])), L=shelfOrder(st);
  const fbt=ur=>`${ur.n} 处伏笔待揭晓`;
  const fb=ur=>ur.n?`<div class="fb" role="button" tabindex="0" aria-label="${fbt(ur)}，查看"><span class="dia"></span>${fbt(ur)}</div>`:'';
  const pbar=x=>x.started&&!x.fin?`<span class="pbar"><i style="width:${x.pct}%"></i></span>`:'';
  const cur=guest?null:SHELF.map(r=>r[0]).filter(k=>st[k].started&&!st[k].fin&&st[k].last).sort((a,b)=>st[b].last-st[a].last)[0];
  const own=k=>!!(BOOKS[k]&&BOOKS[k].imported);
  const busy=k=>!!(BOOKS[k]&&BOOKS[k].busy);   /* v9.67：外文书还没翻译完 / 还在整理——不能读，显示加载中 */
  const item=([k,id,t,au,cn])=>{ const x=st[k], grip=shEdit?`<span class="grip" aria-hidden="true"><i></i><i></i><i></i></span>`:'', sel=shEdit&&own(k)?`<span class="sel ${shSel.has(k)?'on':''}" aria-hidden="true"></span>`:'';
    const pct=busy(k)?'处理中':x.fin?'读完':x.started?x.pct+'%':'未读', ld=busy(k)?`<span class="ldg" aria-label="${esc(BOOKS[k].busy)}"><i></i></span>`:'';
    if(v.lay==='rows') return `<button class="book lb ${busy(k)?'busy':''}" id="${id}" data-k="${k}" aria-describedby="${id}p">${sel}<span class="t">${esc(t)}</span><span class="a">${esc(au)}</span><span class="lp" id="${id}p">${pct}</span>${shEdit?'':`<span class="bkm" data-bi="${k}" role="button" tabindex="0" aria-label="《${esc(t)}》详情">…</span>`}${grip}</button>`;
    if(v.lay==='grid') return `<button class="book gb ${busy(k)?'busy':''}" id="${id}" data-k="${k}" aria-describedby="${id}p">${coverHTML(t,BOOKS[k].cover)}${ld}<span class="t">${esc(t)}</span><span class="vh" id="${id}p">${busy(k)?BOOKS[k].busy:x.prog}</span>${sel}${grip}</button>`;
    return `<button class="book ${busy(k)?'busy':''}" id="${id}" data-k="${k}" aria-describedby="${id}p">${coverHTML(t,BOOKS[k].cover)}${ld}
      <div class="binfo"><div class="t">${esc(t)}</div>${au?`<div class="a">${esc(authorName(au,cn))}</div>`:''}<div class="p" id="${id}p">${busy(k)?esc(BOOKS[k].busy):x.prog}</div>${busy(k)?'':pbar(x)}${busy(k)?'':fb(x.ur)}</div>${shEdit?'':`<span class="bkm" data-bi="${k}" role="button" tabindex="0" aria-label="《${esc(t)}》详情">…</span>`}${sel}${grip}</button>`; };
  const nSel=shSel.size;
  /* 右上角：登录后是头像；没登录是"登录" */
  const me=guest?`<button class="linkbtn shlogin" id="shLogin">登录</button>`:`<button class="shme" id="shMe" aria-label="我的">${avatarHTML(curUser())}</button>`;
  const web=SRV||guest;   /* 找书、导入：服务器上有；没登录的页面也列出来（点了再登录） */
  $('#app').innerHTML=`<div class="shelf ${shEdit?'editing':''}">
    <div class="brand" aria-label="伏笔">${LOGO}<b>伏笔</b>${me}</div>
    ${cur&&!shEdit?`<button class="cont" id="shCont"><span class="ck">继续阅读</span>${coverHTML(BOOKS[cur].t,BOOKS[cur].cover)}<span class="ci"><span class="t">${esc(BOOKS[cur].t)}</span><span class="p">${st[cur].where}　${st[cur].pct}%</span>${pbar(st[cur])}</span><span class="chev" aria-hidden="true">›</span></button>`:''}
    <div class="shh"><h1>书架</h1>${shEdit?'<span class="shacts"><button class="linkbtn" id="shDone">完成</button></span>':web?`<span class="shacts"><button class="linkbtn" id="shLib">找书</button><span class="shdot">·</span><button class="linkbtn" id="impBtn">导入</button></span>`:''}</div>
    <div class="shtools">${shEdit?`<span class="etip">${SHELF.some(r=>own(r[0]))?'拖动调整顺序；点选自己导入的书可移除':'拖动调整顺序'}</span>`:`<button class="sortb" id="sortB" aria-haspopup="true" aria-expanded="${shMenu}">${SH_SORT.find(x=>x[0]===v.sort)[1]}<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5L6 8l3.5-3.5"/></svg></button>
      ${shMenu?`<div class="shmenu" role="menu">${SH_SORT.map(([k,l])=>`<button role="menuitemradio" aria-checked="${v.sort===k}" data-sort="${k}">${l}</button>`).join('')}</div>`:''}
      <span class="lays">${Object.entries(SH_LAY).map(([k,[l,d]])=>`<button data-lay="${k}" aria-pressed="${v.lay===k}" aria-label="${l}"><svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg></button>`).join('')}<button class="linkbtn" id="shEdit">整理</button></span>`}</div>
    <div class="books lay-${v.lay}" id="bookList">${L.map(item).join('')}</div>
    ${shEdit&&nSel?`<div class="shbar"><span>已选 ${nSel} 本</span><button class="btn ghost danger" id="shDel">移除</button></div>`:''}
    ${importBox()}
    <p class="foot">${guest?'登录后可以阅读、记录和找书。':'长按书籍可查看详情。'}</p>
  </div>`;
  wireImport();
  $('#shLib')?.addEventListener('click',()=>guard(()=>findPage(),'登录后找书'));
  $('#impBtn')?.addEventListener('click',()=>guard(()=>importPage(),'登录后导入'));
  $('#shMe')?.addEventListener('click',()=>mePage());
  $('#shLogin')?.addEventListener('click',()=>authPage('login'));
  $('#shCont')?.addEventListener('click',()=>openBook(cur));
  $('#sortB')?.addEventListener('click',e=>{ e.stopPropagation(); shMenu=!shMenu; shelf(); });
  document.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{ v.sort=b.dataset.sort; shMenu=false; saveProf(true); shelf(); });
  if(shMenu) setTimeout(()=>document.addEventListener('click',function off(e){ if(!e.target.closest('.shmenu')){ shMenu=false; document.removeEventListener('click',off); if($('.shmenu')) shelf(); } }),0);
  document.querySelectorAll('[data-lay]').forEach(b=>b.onclick=()=>{ v.lay=b.dataset.lay; saveProf(true); shelf(); });
  $('#shEdit')?.addEventListener('click',()=>{ shEdit=true; shMenu=false; shSel=new Set(); shelf(); });
  $('#shDone')?.addEventListener('click',()=>{ shEdit=false; shSel=new Set(); shelf(); });
  $('#shDel')?.addEventListener('click',()=>{ const ks=[...shSel]; shSel=new Set(); removeBooks(ks); });
  if(shEdit){ wireShelfDrag(own); return; }
  SHELF.forEach(([k,id])=>{ const el=$('#'+id); if(el) longPress(el,e=>e&&e.target.closest('.bkm')?bookInfo(k,st[k].prog,false,guest):e&&e.target.closest('.fb')?bookInfo(k,st[k].prog,true,guest):busy(k)?bookInfo(k,st[k].prog,false,guest):guest?bookInfo(k,st[k].prog,false,true):openBook(k),()=>bookInfo(k,st[k].prog,false,guest)); });
  document.querySelectorAll('.book .fb').forEach(f=>f.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();unresolvedSheet(f.closest('.book').dataset.k);}}));
}
### homePage
function homePage(){ shelf(); }   /* v9.67：没登录的首页就是书架本身（右上角"登录"），点到"用"才要求登录 */
### css
/* ===== v9.67 访客书架、处理中、札记并入笔记 ===== */
.shlogin{margin-left:auto;align-self:center}
.book.busy .cover{opacity:.55}
.book.busy{cursor:default}
.book.gb{position:relative}
.ldg{position:absolute;left:0;top:0;width:100%;aspect-ratio:3/4.3;display:flex;align-items:center;justify-content:center;pointer-events:none}
.book:not(.gb) .ldg{width:var(--cw,72px)}
.ldg i{width:30px;height:30px;border-radius:50%;background:rgba(30,38,34,.72);box-shadow:0 0 0 1px rgba(255,255,255,.2);position:relative;animation:none}
.ldg i::after{content:"";position:absolute;inset:7px;border-radius:50%;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;animation:spin .9s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.ldg i::after{animation:none}}
