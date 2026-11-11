### minePanel
function minePanel(tab='all'){
  /* v9.67（用户 10-30）：读书札记和笔记是同一个地方——笔记标签行最后多一个"札记"，在原处切换，不再是另一整页、也没有大按钮 */
  const items=[];
  Object.keys(S.bm).forEach(i=>items.push({k:'bm',at:+i,t:S.bm[i]}));
  S.ul.forEach(u=>items.push({k:'hl',at:u.at,t:u.t,u}));
  S.notes.forEach(n=>items.push({k:n.type,at:n.at,t:n.t,n}));
  items.sort((a,b)=>a.at-b.at||a.t-b.t);
  const noted=new Set(S.notes.map(n=>n.hl).filter(Boolean));
  const isQ=x=>(x.k==='q'||x.k==='qa')&&!isFb(x.n);
  const pick={all:x=>!(x.k==='hl'&&noted.has(x.u.id)),hl:x=>x.k==='hl',note:x=>x.k==='note',q:isQ,bm:x=>x.k==='bm'};
  const TABS=[['all','全部'],['hl','划线'],['note','想法'],['q','疑问'],['bm','书签']].map(([k,l])=>[k,l,items.filter(pick[k]).length]).concat([['arc','札记',0]]);
  const KN={bm:'书签',hl:'划线',note:'想法',q:'疑问',qa:'疑问'};
  const row=x=>{ const p=x.at>=0?P[x.at]:null, n=x.n, u=x.u||(n&&n.hl&&S.ul.find(v=>v.id===n.hl));
    const src=u?u.text:n&&n.quote?n.quote:p?firstLine(txt(p),60):'';
    const go=u?`data-gu="${u.id}"`:`data-go="${p?p.n:'1'}"`;
    const st=isFb(n)?(n.done?'已揭晓':'未揭晓'):n&&n.type==='q'?(n.done?'已解答':'待解答'):n&&n.type==='qa'?'已解答':'';
    const more=x.k==='bm'?`<button class="nrm txt" data-ub="${x.at}">移除</button>`:n&&n.type==='qa'?`<button class="nrm" data-sa="${n.id}" aria-label="看回答">…</button>`:n?`<button class="nrm" data-nm="${n.id}" aria-label="编辑、删除">…</button>`:`<button class="nrm" data-hs="${u.id}" aria-label="写点什么、取消划线">…</button>`;
    return `<div class="nr ${n&&n.done?'done':''}" role="button" tabindex="0" ${go}><div class="nrh"><span>${label(x.at)}　${isFb(n)?'我发现的伏笔':KN[x.k]}</span>${st?`<span class="nrs ${/待|未/.test(st)?'open':''}">${st}</span>`:''}${more}</div>
      ${src?`<p class="nrq ${x.k==='bm'?'bm':''}">${esc(src)}</p>`:''}
      ${n?`<p class="nrt">${esc(n.text)}</p>`:''}${n&&n.guess?`<p class="nrg">我的猜想：${esc(n.guess)}　${n.conf} 成把握</p>`:''}${n&&n.done&&n.ans?`<p class="nrg">我记下的答案：${esc(n.ans)}</p>`:''}</div>`; };
  const tabs=`<div class="ntabs" role="group" aria-label="笔记分类">${TABS.map(([k,l,c])=>`<button data-tab="${k}" aria-pressed="${k===tab}">${l}${c?`<small>${c}</small>`:''}</button>`).join('')}</div>`;
  let body;
  if(tab==='arc') body=arcBody();
  else { const list=items.filter(pick[tab]); body=list.length?list.map(row).join(''):`<div class="empty">${tab==='bm'?'尚无书签。点顶栏右上角的图标，可为当前位置添加书签。':tab==='all'?'尚无记录。长按并拖动选择文字，可划线、写想法或提问。':'尚无记录。'}</div>`; }
  openSheet(`<div class="shead"><span class="ttl">笔记</span>${tab==='arc'?'<span class="nacts"><button class="linkbtn" id="exCopy">复制</button><button class="linkbtn" id="exSave">导出</button></span>':''}<button class="x" data-close aria-label="关闭">×</button></div>
    ${tabs}<div class="sbody ${tab==='arc'?'arcb':''}">${body}</div>`,{tall:true});
  const sh=$('#sheet'), again=()=>minePanel(tab);
  sh.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>minePanel(b.dataset.tab));
  if(tab==='arc'){ wireArc(); return; }
  sh.querySelectorAll('.nrm').forEach(b=>b.addEventListener('click',e=>e.stopPropagation()));
  sh.querySelectorAll('[data-sa]').forEach(b=>b.onclick=()=>showAnswer(S.notes.find(n=>n.id===+b.dataset.sa),again));
  sh.querySelectorAll('[data-nm]').forEach(b=>b.onclick=()=>noteSheet(+b.dataset.nm,again));
  sh.querySelectorAll('[data-hs]').forEach(b=>b.onclick=()=>hlSheet(+b.dataset.hs));
  sh.querySelectorAll('[data-ub]').forEach(b=>b.onclick=()=>{ const k=b.dataset.ub, t0=S.bm[k]; delete S.bm[k]; save(); paintMarks(); syncTbm(); minePanel(tab);
    toast('<div class="tq">已移除书签</div><button>撤销</button>',()=>{ S.bm[k]=t0; save(); paintMarks(); syncTbm(); if($('#sheet').classList.contains('show')) minePanel(tab); },4000); });
  sh.querySelectorAll('.nr').forEach(r=>{ const go=()=>{ closeSheet(); if(r.dataset.gu) flashUL(+r.dataset.gu); else jump(r.dataset.go); };
    r.addEventListener('click',go); r.addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target===r) go(); }); });
}
### arcBody
/* 札记：把划线、想法、伏笔、疑问整理成一篇，排成书里的一页；读后感在最前。可以编辑（点"编辑"原地变成输入框）、复制、导出 */
function arcBody(){
  const fresh=archiveMD(), d=S.expDraft, stale=d&&mdBody(d.base)!==mdBody(fresh), text=d?d.text:fresh;
  arcBody.text=text; arcBody.fresh=fresh; arcBody.stale=stale;
  return `${d?`<p class="exnote">${stale?'你编辑后笔记又有更新，以下内容未包含新记录。':'这是你编辑过的版本。'}<button class="linkbtn" id="exReset">${stale?'按最新笔记重新整理':'恢复原始内容'}</button></p>`:''}
    <div id="arcView">${reflectHTML()}<div class="mdv">${mdHTML(S.reflect&&S.reflect.text?text.replace('## 读后感\n\n'+S.reflect.text+'\n',''):text)}</div></div>
    <div id="arcEdit" hidden><textarea id="exText" class="extext" spellcheck="false">${esc(text)}</textarea></div>
    <p class="arcact"><button class="linkbtn" id="exEdit">编辑这篇札记</button></p>`;
}
function wireArc(){
  const sh=$('#sheet'), text=arcBody.text, fresh=arcBody.fresh, stale=arcBody.stale, d=S.expDraft;
  sh.querySelectorAll('[data-rfc]').forEach(b=>b.onclick=()=>copyText(b.dataset.rfc==='mine'?S.reflect.text:RF_EX[BK][1],'已复制读后感全文'));
  $('#rfEx')?.addEventListener('click',e=>{ const x=$('#rfX'), b=e.currentTarget; x.hidden=!x.hidden; b.textContent=x.hidden?'看示例':'收起'; b.setAttribute('aria-expanded',String(!x.hidden)); });
  $('#exCopy').onclick=()=>exportNotes('copy',$('#exText').value);
  $('#exSave').onclick=()=>exportNotes('save',$('#exText').value);
  $('#exReset')?.addEventListener('click',()=>{ if(!confirm(stale?'将按最新笔记重新整理，你的编辑会被替换。确定？':'将恢复原始内容，你的编辑会被替换。确定？')) return; delete S.expDraft; save(); minePanel('arc'); });
  const ed=$('#exEdit'); let on=false;
  ed.onclick=()=>{ if(!on){ on=true; $('#arcView').hidden=true; $('#arcEdit').hidden=false; ed.textContent='完成'; $('#exText').focus(); }
    else { const v=$('#exText').value; if(v!==text){ S.expDraft={base:(d&&!stale)?d.base:fresh,text:v}; save(); } minePanel('arc'); } };
}
### exportSheet
function exportSheet(mode,from){ minePanel('arc'); }   /* v9.67：札记并进笔记的"札记"标签，不再是单独一页 */
### novelOutlineRecap
/* 导览"正在读"那一行右边的"回顾"文字入口，代替底部大按钮 */
const recapLink=`<button class="olrc" id="olRecap">回顾</button>`;
### css
.shead .nacts{display:flex;gap:16px;margin-left:auto;margin-right:8px}
.shead .nacts .linkbtn{padding:0;height:32px}
.sbody.arcb{padding-top:12px}
.arcb .mdv{font-family:var(--serif);font-size:var(--t-body);line-height:1.85;color:var(--ink)}
.arcb .mdv h3.mt{font-size:var(--t-key);letter-spacing:.04em;margin:0 0 2px}
.arcb .mdv h4{display:flex;align-items:center;gap:8px;font-family:var(--ui);font-size:var(--t-aux);font-weight:600;color:var(--ink);margin:20px 0 6px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.arcb .mdv h4::before{content:"";width:6px;height:6px;background:var(--hl);transform:rotate(45deg);flex:none}
.arcb .mdv p.meta{margin:0 0 8px}
.arcb .mdv blockquote{border-left:2px solid color-mix(in srgb,var(--blue) 45%,transparent);color:var(--ink2);font-size:var(--t-aux)}
.arcb .mdv li{font-family:var(--kai)}
.arcb .rf{margin:0 0 12px}
.arcact{margin:20px 0 0;text-align:center}
.arcact .linkbtn{display:inline-flex;font-size:var(--t-aux)}
.olnow .olrc{margin-left:8px;color:var(--blue);font-size:var(--t-aux);padding:4px 8px}
