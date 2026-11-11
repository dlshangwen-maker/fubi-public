### renderCard
function renderCard(i){
  /* v9.62：标题 = 位置；深浅在内容顶部；底部上一段 / 下一段 */
  const p=P[i], c=CARDS[p.n][LV[cardLv]], U=unitOf(i), uEnd=U.slice(-1)[0], u0=U[0];
  const sub=NOVEL?esc(firstLine(txt(P[u0]),10).replace(/……$/,'')+'…'):'';
  const prev=u0>0?unitOf(u0-1)[0]:-1, next=uEnd+1<P.length?uEnd+1:-1, word=NOVEL?'段':'条';
  const html=`<div class="shead">${cardBack?`<button class="x back" id="cardBack" aria-label="返回${cardBack.label}">‹</button>`:''}<span class="n ${NOVEL?'nv':''}">${NOVEL?lab(p.n):p.n}</span>${sub?`<span class="nsub">${sub}</span>`:''}
    <button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">
    <div class="lvrow" role="group" aria-label="解释深浅">${LV.map((l,k)=>`<button data-lv="${k}" aria-pressed="${k===cardLv}">${l}</button>`).join('')}</div>
    ${D.orig&&S.lang==='orig'?`<div class="quote zhq"><b>中文</b>${esc(p.zh.replace(/⟦img:[^⟧]+⟧/g,'[公式]').replace(/⟦表:[^⟧]*⟧/g,'[表]'))}</div>`:''}
    ${D.orig&&S.lang!=='orig'&&U.some(j=>P[j][ogl()])?`<details class="ogq"><summary>原文（${(D.orig.find(x=>x[0]===ogl())||[])[1]||''}）</summary><div lang="${ogl()}">${U.map(j=>P[j][ogl()]?`<p>${esc(P[j][ogl()])}</p>`:'').join('')}</div></details>`:''}
    <p class="plain">${linkRefs(c['白话'],uEnd)}</p>
    <p class="more">${linkRefs(c['展开'],uEnd)}</p>
    ${c['前置']?`<div class="need"><b>背景知识</b>${linkRefs(c['前置'],uEnd)}</div>`:''}
    ${qaBlock(QA.filter(q=>U.some(j=>P[j].n===q['锚点'])))}
    ${CANEDIT()?`<p style="margin-top:14px"><button class="linkbtn" id="cSplit">从这里分章</button></p>`:''}
  </div>
  <div class="sfoot">${prev>=0?`<button class="btn ghost" id="cPrev">‹ 上一${word}</button>`:''}${next>=0?`<button class="btn ghost" id="cNext" style="margin-left:auto">下一${word} ›</button>`:''}</div>`;
  const wasOpen=$('#sheet').classList.contains('show');
  openSheet(html); if(wasOpen) $('#sheet').classList.add('show');
  U.forEach(j=>els[j].classList.add('on'));
  document.querySelectorAll('#sheet [data-lv]').forEach(b=>b.onclick=()=>switchLv(i,+b.dataset.lv));
  if(cardBack){ const cb=cardBack; $('#cardBack').onclick=()=>{ cardBack=null; els[i].classList.remove('on'); cb.fn(); }; }
  wireQA(i);
  $('#cSplit')?.addEventListener('click',()=>{closeSheet();splitHere(i);});
  const go=j=>{ cardBack=null; els.forEach(e=>e.classList.remove('on')); noRead(); unfoldFor(j); els[j].scrollIntoView({block:'start',behavior:calm()?'auto':'smooth'}); openCard(j); };
  $('#cPrev')?.addEventListener('click',()=>go(prev)); $('#cNext')?.addEventListener('click',()=>go(next));
}
### switchLv
function switchLv(i,k){
  /* v9.62：直接记住读者最后一次选的深浅（不再连切三次才问要不要设为默认） */
  if(k===cardLv) return; cardLv=k; S.level=k; save(); renderCard(i);
}
### openClue
function openClue(id,pop,back){
  const s=SUS.find(x=>x.id===id); const first=!S.seen[id];
  if(first){S.seen[id]=Date.now();save();paintMarks();}
  lateSolve(s);
  const g=S.guesses[id], done=S.doneS[id], self=()=>openClue(id,pop,back);
  openSheet(`<div class="shead">${back?'<button class="x back" data-bk aria-label="返回">‹</button>':''}<span class="ttl">伏笔</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">
    ${ML()&&isPiece(id)?`<div class="clmain"><span class="mltag">主线</span><span>${esc(D.main.q)}</span></div>`:''}
    <div class="q" style="border:0;padding-top:0">${srcBlock(srcQuote(s,true))}<div class="qt">${esc(s['问题'])}</div></div>
    ${g?`<div class="gv"><small>我的猜想　${g.conf} 成把握</small>${esc(g.text)}</div>`:''}
    ${done?`<p class="mini">这处伏笔在${lab(s['揭晓'])}揭晓了。</p>`:`<p class="mini">读到答案处会自动揭晓。${Object.keys(S.seen).length<=1?'伏笔只是阅读引导，不判对错。':''}</p>`}
  </div>
  <div class="sfoot">${done?`<button class="btn ghost" id="cSrc">回到原文</button><button class="btn" id="cRv" style="margin-left:auto">看揭晓</button>`:`<button class="btn ghost" data-close>继续阅读</button><button class="btn" id="cg" style="margin-left:auto">${g?'修改猜想':'写下猜想'}</button>`}</div>`);
  wireBack(back);
  $('#cg')?.addEventListener('click',()=>guessEditor(id,self));
  $('#cRv')?.addEventListener('click',()=>reveal(id,false,self));
  $('#cSrc')?.addEventListener('click',()=>goSrc(id));
}
### guessEditor
function guessEditor(id,back){
  /* v9.62：原地换成填写页，‹ 回到伏笔卡；保存后回到伏笔卡，提示"已保存 · 撤销"。把握仍用滑条（用户 10-28 定） */
  const s=SUS.find(x=>x.id===id), old=S.guesses[id], g=old||{text:'',conf:5}, bk=back||(()=>openClue(id));
  openSheet(`<div class="shead"><button class="x back" data-bk aria-label="返回伏笔">‹</button><span class="ttl">${old?'修改猜想':'写下猜想'}</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody"><div class="q" style="border:0;padding-top:0"><div class="qt">${esc(s['问题'])}</div></div>
    <p class="flab">你的猜想</p><textarea id="gt" placeholder="只有你自己能看到，会在揭晓处重新出现">${esc(g.text)}</textarea>${confRow(g.conf)}</div>
  <div class="sfoot"><button class="btn ghost" data-bk>取消</button><button class="btn" id="gs" style="margin-left:auto">保存</button></div>`);
  wireBack(bk); wireConf(); $('#gt').focus();
  $('#gs').onclick=()=>{ const t=$('#gt').value.trim(); if(!t){ $('#gt').focus(); return; }
    S.guesses[id]={text:t,conf:+$('#cf').value,at:S.current}; save(); bk();
    toast('<div class="tq">已保存</div><button>撤销</button>',()=>{ if(old) S.guesses[id]=old; else delete S.guesses[id]; save(); if($('#sheet').classList.contains('show')) bk(); },4000); };
}
### reveal
function reveal(id,auto,back){
  const s=SUS.find(x=>x.id===id), g=S.guesses[id];
  S.ansSeen=S.ansSeen||{}; if(!S.ansSeen[id]){S.ansSeen[id]=Date.now();save();paintMarks();}
  if(!auto) sweep(clueRange(s,'ans'));
  const nP=ML()&&isPiece(id)?D.main.pieces.filter(x=>S.doneS[x]).length:0;
  const piece=nP?`<p class="rvml"><span class="mltag">主线</span>拼上第 ${nP} 块　${nP} / ${D.main.pieces.length}</p>`:'';
  openSheet(`<div class="shead">${back?`<button class="x back" data-bk aria-label="返回">‹</button>`:''}<span class="ttl">伏笔在${NOVEL?lab(s['揭晓']):' '+s['揭晓']+' '}揭晓</span><button class="x" data-close aria-label="关闭">×</button></div>
    <div class="sbody"><div class="rvq"><small>埋于${NOVEL?lab(s['提出']):' '+s['提出']}</small><div class="qt">${esc(s['问题'])}</div></div>
    <div class="rvpair"><div class="rvg"><small>你当时猜</small>${g?`<p>${esc(g.text)}</p><span class="rvc">${g.conf} 成把握</span>`:'<p class="rvnone">当时没有写猜想。</p>'}</div>
    <div class="rva"><small>书里的答案（揭晓说明）</small><p class="plain">${esc(s['兑现说明'])}</p></div></div>${piece}</div>
    <div class="sfoot">${auto?`<button class="btn ghost" data-go="${s['揭晓']}">回到原文</button><button class="btn" data-close style="margin-left:auto">继续阅读</button>`:`<button class="btn" data-go="${s['揭晓']}" style="margin-left:auto">回到原文</button>`}</div>`);
  wireBack(back);
}
### revealMine
function revealMine(id,auto,back){
  const n=S.notes.find(x=>x.id===id), q=(D.qa||[]).find(x=>x.id===n.qa); if(!q) return;
  if(!n.ansSeen){n.ansSeen=Date.now();save();paintMarks();}
  if(!auto) sweep(mineRange(n,'ans'));
  openSheet(`<div class="shead">${back?`<button class="x back" data-bk aria-label="返回">‹</button>`:''}<span class="ttl">答案在${NOVEL?lab(n.rv):' '+n.rv+' '}</span><button class="x" data-close aria-label="关闭">×</button></div>
    <div class="sbody"><div class="rvq mine"><small>问于${label(n.at)}　我发现的</small><div class="qt">${esc(n.text)}</div></div>
    <div class="rvpair"><div class="rvg"><small>你当时猜</small>${n.guess?`<p>${esc(n.guess)}</p><span class="rvc">${n.conf} 成把握</span>`:'<p class="rvnone">当时没有写猜想。</p>'}</div>
    <div class="rva"><small>书里的答案（揭晓说明）</small><p class="plain">${esc(q['回收说明'])}</p></div></div></div>
    <div class="sfoot">${auto?`<button class="btn ghost" data-go="${n.rv}">回到原文</button><button class="btn" data-close style="margin-left:auto">继续阅读</button>`:`<button class="btn" data-go="${n.rv}" style="margin-left:auto">回到原文</button>`}</div>`);
  wireBack(back);
}
### cluePanel
function cluePanel(tab){
  /* v9.62：每条两行（位置 + 印章 / 问题），点一条原地进伏笔卡或揭晓卡；没打开的也排在里面 */
  const rc=reachedClues(), qs=S.notes.filter(isFb);
  const all=[...rc.map(s=>({b:s,pos:posOf(s['提出']),done:S.doneS[s.id]||0})),...qs.map(n=>({m:n,pos:n.at,done:n.done||0}))];
  const open=all.filter(x=>!x.done).sort((a,b)=>a.pos-b.pos);
  const done=all.filter(x=>x.done).sort((a,b)=>b.done-a.done);   /* 最近揭晓的排最前 */
  if(!tab){ const tOpen=Math.max(0,...open.map(x=>x.b?(S.seen[x.b.id]||0):(x.m.t||0))), tDone=Math.max(0,...done.map(x=>x.done||0)); tab=tDone>tOpen?'done':'open'; }
  cluePanel.last=tab;
  const row=x=>{ if(x.b){ const s=x.b, d=S.doneS[s.id], lk=!S.seen[s.id];
      return `<button class="cr ${d?'done':''} ${lk?'locked':''}" data-cl="${s.id}"><span class="crh"><span>${label(posOf(s['提出']))}</span>${ML()&&isPiece(s.id)?'<span class="seal zhu">主线</span>':''}${d?`<span class="crs">${lab(s['揭晓'])}揭晓</span>`:''}${S.guesses[s.id]?'<span class="crg">已猜</span>':''}</span><span class="crq">${lk?'点开查看问题':esc(s['问题'])}</span></button>`; }
    const n=x.m; return `<button class="cr mine ${n.done?'done':''}" data-cm="${n.id}"><span class="crh"><span>${label(n.at)}</span><span class="seal dai">我发现的</span>${n.done?`<span class="crs">${n.rv?lab(n.rv)+'揭晓':'已揭晓'}</span>`:''}${n.guess?'<span class="crg">已猜</span>':''}</span><span class="crq">${esc(n.text)}</span></button>`; };
  const L=tab==='open'?open:done;
  const body=L.length?L.map(row).join(''):`<div class="empty">${tab==='done'?'暂无已揭晓的伏笔。':all.length?'暂无未揭晓的伏笔。':`${S.view.guide?`阅读时，页边朱色的“伏笔”批注标出书中的伏笔${ML()?'；其中一部分是主线的碎片，揭晓一处就拼上一块':''}。`:''}你写下的疑问如果答案在后文，也会作为伏笔列在这里。`}</div>`;
  openSheet(`<div class="shead"><span class="ttl">伏笔</span>
    <div class="seg" role="group" aria-label="伏笔分类"><button data-ct="open" aria-pressed="${tab==='open'}">未揭晓 ${open.length}</button><button data-ct="done" aria-pressed="${tab==='done'}">已揭晓 ${done.length}</button></div>
    <button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">
    ${mainHTML(true)}
    ${!S.view.guide?'<p class="mini" style="margin-top:6px">书中伏笔已关闭，可在“设置 › 更多设置 › 阅读引导”中开启。你发现的伏笔不受影响。</p>':''}
    <div class="crl">${body}</div>
  </div>`,{tall:true});
  const sh=$('#sheet'), bk=()=>cluePanel(tab);
  sh.querySelectorAll('[data-ct]').forEach(b=>b.onclick=()=>cluePanel(b.dataset.ct));
  sh.querySelectorAll('[data-cl]').forEach(b=>b.onclick=()=>{ const id=b.dataset.cl; S.doneS[id]?reveal(id,false,bk):openClue(id,false,bk); });
  sh.querySelectorAll('[data-cm]').forEach(b=>b.onclick=()=>{ const n=S.notes.find(x=>x.id===+b.dataset.cm); n.done&&n.rv?revealMine(n.id,false,bk):noteSheet(n.id,bk); });
}
### noteSheet
function noteSheet(id,back){
  const n=S.notes.find(x=>x.id===id); if(!n) return;
  const kind=n.type==='note'?'想法':isFb(n)?'伏笔':'疑问';
  openSheet(`<div class="shead">${back?'<button class="x back" data-bk aria-label="返回">‹</button>':''}<span class="ttl">${kind}</span><span class="nsub">${label(n.at)}</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody"><div class="quote" style="max-height:none">${esc(mineQuote(n))}</div>${noteRow(n)}</div>
  <div class="sfoot"><button class="btn ghost" id="nDel">删除</button>${n.at>=0?'<button class="btn ghost" id="nGo">回到原文</button>':''}${n.at>=0?'<button class="btn ghost" id="nCard" style="margin-left:auto">解释</button>':''}</div>`);
  wireBack(back);
  $('#nDel').onclick=()=>{ const ul=n.hl&&S.ul.find(u=>u.id===n.hl); S.notes=S.notes.filter(x=>x.id!==n.id); if(ul) S.ul=S.ul.filter(u=>u!==ul); save(); paintUL(); paintMarks(); back?back():closeSheet();
    toast(`<div class="tq">已删除这条${kind}。</div><button>撤销</button>`,()=>{ S.notes.push(n); if(ul) S.ul.push(ul); save(); paintUL(); paintMarks(); if(back&&$('#sheet').classList.contains('show')) back(); },4000); };
  $('#nGo')?.addEventListener('click',()=>{ closeSheet(); if(!(n.hl&&flashUL(n.hl))) jump(P[n.at].n); });
  $('#nCard')?.addEventListener('click',()=>openCard(n.at,{back:()=>noteSheet(id,back),backLabel:kind}));
  wireNoteRows($('#sheet'),back||(()=>noteSheet(id)));
}
### minePanel
function minePanel(tab='all'){
  /* v9.62：分类是一行纯文字；每条 = 位置和种类 → 原文 → 自己写的；点一条回到原文，"…"进这条记录 */
  const items=[];
  Object.keys(S.bm).forEach(i=>items.push({k:'bm',at:+i,t:S.bm[i]}));
  S.ul.forEach(u=>items.push({k:'hl',at:u.at,t:u.t,u}));
  S.notes.forEach(n=>items.push({k:n.type,at:n.at,t:n.t,n}));
  items.sort((a,b)=>a.at-b.at||a.t-b.t);
  const noted=new Set(S.notes.map(n=>n.hl).filter(Boolean));
  const isQ=x=>(x.k==='q'||x.k==='qa')&&!isFb(x.n);
  const pick={all:x=>!(x.k==='hl'&&noted.has(x.u.id)),hl:x=>x.k==='hl',note:x=>x.k==='note',q:isQ,bm:x=>x.k==='bm'};
  const TABS=[['all','全部'],['hl','划线'],['note','想法'],['q','疑问'],['bm','书签']].map(([k,l])=>[k,l,items.filter(pick[k]).length]);
  const list=items.filter(pick[tab]);
  const KN={bm:'书签',hl:'划线',note:'想法',q:'疑问',qa:'疑问'};
  const row=x=>{ const p=x.at>=0?P[x.at]:null, n=x.n, u=x.u||(n&&n.hl&&S.ul.find(v=>v.id===n.hl));
    const src=u?u.text:n&&n.quote?n.quote:p?firstLine(txt(p),60):'';
    const go=u?`data-gu="${u.id}"`:`data-go="${p?p.n:'1'}"`;
    const st=isFb(n)?(n.done?'已揭晓':'未揭晓'):n&&n.type==='q'?(n.done?'已解答':'待解答'):n&&n.type==='qa'?'已解答':'';
    const more=x.k==='bm'?`<button class="nrm txt" data-ub="${x.at}">移除</button>`:n&&n.type==='qa'?`<button class="nrm" data-sa="${n.id}" aria-label="看回答">…</button>`:n?`<button class="nrm" data-nm="${n.id}" aria-label="编辑、删除">…</button>`:`<button class="nrm" data-hs="${u.id}" aria-label="写点什么、取消划线">…</button>`;
    return `<div class="nr ${n&&n.done?'done':''}" role="button" tabindex="0" ${go}><div class="nrh"><span>${label(x.at)}　${isFb(n)?'我发现的伏笔':KN[x.k]}</span>${st?`<span class="nrs ${/待|未/.test(st)?'open':''}">${st}</span>`:''}${more}</div>
      ${src?`<p class="nrq ${x.k==='bm'?'bm':''}">${esc(src)}</p>`:''}
      ${n?`<p class="nrt">${esc(n.text)}</p>`:''}${n&&n.guess?`<p class="nrg">我的猜想：${esc(n.guess)}　${n.conf} 成把握</p>`:''}${n&&n.done&&n.ans?`<p class="nrg">我记下的答案：${esc(n.ans)}</p>`:''}</div>`; };
  openSheet(`<div class="shead"><span class="ttl">笔记</span><button class="x" data-close aria-label="关闭">×</button></div>
    <div class="ntabs" role="group" aria-label="笔记分类">${TABS.map(([k,l,c])=>`<button data-tab="${k}" aria-pressed="${k===tab}">${l}${c?`<small>${c}</small>`:''}</button>`).join('')}</div>
    <div class="sbody">${list.length?list.map(row).join(''):`<div class="empty">${tab==='bm'?'尚无书签。点顶栏右上角的图标，可为当前位置添加书签。':tab==='all'?'尚无记录。长按并拖动选择文字，可划线、写想法或提问。':'尚无记录。'}</div>`}</div>
    <div class="sfoot"><button class="btn ghost wide" id="expOpen">${ic('memo','i')}查看读书札记</button></div>`,{tall:true});
  const sh=$('#sheet'), again=()=>minePanel(tab);
  sh.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>minePanel(b.dataset.tab));
  $('#expOpen').onclick=()=>exportSheet(null,'notes');
  sh.querySelectorAll('.nrm').forEach(b=>b.addEventListener('click',e=>e.stopPropagation()));
  sh.querySelectorAll('[data-sa]').forEach(b=>b.onclick=()=>showAnswer(S.notes.find(n=>n.id===+b.dataset.sa),again));
  sh.querySelectorAll('[data-nm]').forEach(b=>b.onclick=()=>noteSheet(+b.dataset.nm,again));
  sh.querySelectorAll('[data-hs]').forEach(b=>b.onclick=()=>hlSheet(+b.dataset.hs));
  sh.querySelectorAll('[data-ub]').forEach(b=>b.onclick=()=>{ const k=b.dataset.ub, t0=S.bm[k]; delete S.bm[k]; save(); paintMarks(); syncTbm(); minePanel(tab);
    toast('<div class="tq">已移除书签</div><button>撤销</button>',()=>{ S.bm[k]=t0; save(); paintMarks(); syncTbm(); if($('#sheet').classList.contains('show')) minePanel(tab); },4000); });
  sh.querySelectorAll('.nr').forEach(r=>{ const go=()=>{ closeSheet(); if(r.dataset.gu) flashUL(+r.dataset.gu); else jump(r.dataset.go); };
    r.addEventListener('click',go); r.addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target===r) go(); }); });
}
### qkind
  /* 想法 | 疑问：按写的内容自动选好；读者点过就以读者选的为准（v9.62，用户 10-28 定流程 A） */
  let qk=null; const kindNow=()=>qk||judgeKind(ta.value.trim(),hl);
  const showK=()=>bar.querySelectorAll('[data-qk]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.qk===kindNow())));
  bar.querySelectorAll('[data-qk]').forEach(b=>b.onclick=()=>{ qk=b.dataset.qk; showK(); ta.focus(); });
  ta.oninput=()=>{ fit(); showK(); };
### css
/* ===== v9.62 交互重做第一批 ===== */
.shead .nsub{font-family:var(--serif);font-size:var(--t-aux);color:var(--mute);min-width:0;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lvrow{display:flex;gap:16px;margin:0 0 12px;font-size:var(--t-aux)}
.lvrow button{height:28px;color:var(--mute);border-bottom:1.5px solid transparent;padding:0}
.lvrow button[aria-pressed=true]{color:var(--ink);border-bottom-color:var(--ink)}
.gv{margin:12px 0 4px;padding:10px 12px;border-radius:6px;background:var(--paper2);font-family:var(--kai);font-size:15px;line-height:1.7;color:var(--blue)}
.gv small{display:block;font-family:var(--ui);font-size:var(--t-tag);color:var(--mute);margin-bottom:2px}
.flab{font-size:var(--t-aux);color:var(--mute);margin:16px 0 6px}
.rvq small,.rvpair small{display:block;font-size:var(--t-tag);color:var(--mute);margin-bottom:4px;font-family:var(--ui)}
.rvq .qt{font-family:var(--kai);font-size:var(--t-key);line-height:1.6;padding-left:12px;border-left:2px solid var(--hl);margin:0 0 16px}
.rvq.mine .qt{border-left-color:var(--blue)}
.rvpair{border-top:1px solid var(--line)}
.rvg,.rva{padding:12px 0;border-bottom:1px solid var(--line)}
.rvg p{margin:0;font-family:var(--kai);font-size:15px;line-height:1.7;color:var(--blue)}
.rvg .rvc{display:block;font-size:var(--t-tag);color:var(--mute);margin-top:4px}
.rvg .rvnone{font-family:var(--ui);font-size:var(--t-aux);color:var(--faint)}
.rva .plain{margin:0}
.rvml{display:flex;align-items:center;gap:8px;margin:12px 0 0;font-size:var(--t-aux);color:var(--hl)}
.seal{flex:none;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;height:20px;padding:0 6px;border-radius:2px;font-size:var(--t-tag);line-height:20px;letter-spacing:.06em}
.seal.zhu{background:var(--hl);color:var(--on-hl)}
.seal.dai{box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--blue) 50%,transparent);color:var(--blue)}
.crl{margin-top:8px}
.cr{display:block;width:100%;text-align:left;padding:12px 0;border-bottom:1px solid var(--line)}
.cr .crh{display:flex;align-items:center;gap:8px;font-size:var(--t-tag);color:var(--mute);line-height:20px}
.cr .crs{color:var(--faint)}
.cr .crg{margin-left:auto;color:var(--blue)}
.cr .crq{display:block;margin-top:4px;font-family:var(--kai);font-size:16px;line-height:1.6;color:var(--ink)}
.cr.locked .crq{font-family:var(--ui);font-size:var(--t-aux);color:var(--hl)}
.cr.done .crq{color:var(--mute)}
.ntabs{display:flex;gap:20px;padding:0 20px;flex:none;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none}
.ntabs button{height:36px;font-size:var(--t-aux);color:var(--mute);border-bottom:1.5px solid transparent;white-space:nowrap;padding:0}
.ntabs button[aria-pressed=true]{color:var(--ink);border-bottom-color:var(--ink)}
.ntabs small{margin-left:4px;font-size:var(--t-tag);color:var(--faint)}
.nr{padding:12px 0;border-bottom:1px solid var(--line);cursor:pointer}
.nr .nrh{display:flex;align-items:center;gap:8px;font-size:var(--t-tag);color:var(--mute);min-height:24px}
.nr .nrs{color:var(--faint)}.nr .nrs.open{color:var(--blue)}
.nr .nrm{margin-left:auto;width:32px;height:24px;color:var(--mute);font-size:16px;letter-spacing:.1em;line-height:1}
.nr .nrm.txt{width:auto;font-size:var(--t-tag);color:var(--blue);letter-spacing:0}
.nr .nrq{margin:4px 0 0;padding-left:12px;border-left:2px solid color-mix(in srgb,var(--blue) 45%,transparent);font-family:var(--serif);font-size:var(--t-aux);line-height:1.7;color:var(--ink2);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.nr .nrq.bm{border-left-color:var(--line)}
.nr .nrt{margin:6px 0 0;font-family:var(--kai);font-size:15px;line-height:1.7;color:var(--blue)}
.nr .nrg{margin:4px 0 0;font-size:var(--t-tag);color:var(--mute);line-height:1.6}
.nr.done .nrt{color:var(--mute)}
#expOpen{display:flex;align-items:center;justify-content:center;gap:6px}
#expOpen svg{width:18px;height:18px}
.qkind{display:flex;gap:2px;padding:2px;border-radius:6px;background:var(--paper2);margin-left:8px}
.qkind button{height:26px;padding:0 10px;border-radius:4px;font-size:var(--t-tag);color:var(--mute)}
.qkind button[aria-pressed=true]{background:var(--sheet);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.1)}
.qkind button[data-qk=q][aria-pressed=true]{color:var(--blue)}
.qtop .qx{margin-left:auto}
.setmore{display:flex;align-items:center;gap:8px;width:100%;margin-top:8px;padding:14px 0 4px;border-top:1px solid var(--line);text-align:left;font-size:var(--t-body);color:var(--ink)}
.setmore small{flex:1;font-size:var(--t-tag);color:var(--faint);text-align:right}
.sheet.setp{max-height:62vh}
.scrim.clear{background:transparent}
