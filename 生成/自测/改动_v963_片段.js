### lastLineRecap
/* 轻度打开书（用户 10-28 定）：回顾不弹卡，放进"上次读到这里"那条线下面——一行"距上次 N 天。上次读到……"，点"展开前情"才看完整回顾 */
function lastLineRecap(gap){
  const l=$('#lastLine'); if(!l) return;
  const cur=Math.max(S.current,0), days=gap==null?0:Math.floor(gap/DAY);
  let line, full='';
  if(NOVEL){ const h=huiOf(cur), sec=secOf(cur), secs=readSecs(h,cur), prev=REC().filter(r=>r['回']<h.n);
    line=`${days?`距上次 ${days} 天。`:''}上次读到${unitName(h.n)}${sec?`：${esc(sec['写'])}`:'开头'}。`;
    full=`${secs.length>1?`<p class="llh">${unitName(h.n)}已读部分</p>${secs.map(x=>`<p>${esc(x['写'])}</p>`).join('')}`:''}${prev.length?`<p class="llh">前面几${UNIT}</p>${prev.map(r=>`<p>${esc(r['一句话'])}</p>`).join('')}`:''}`; }
  else { const mains=P.filter((p,i)=>depth(p.n)===0&&isRd(i));
    line=`${days?`距上次 ${days} 天。`:''}上次读到 ${P[cur].n}。`;
    full=mains.length?`<p class="llh">已读的主干</p>${mains.map(p=>`<p><span class="lln">${p.n}</span>${esc(firstLine(txt(p),60))}</p>`).join('')}`:''; }
  l.classList.add('rc');
  l.innerHTML=`<span class="llt">上次读到这里</span><div class="llr"><p class="ll1">${line}</p>${full?`<button class="linkbtn" id="llMore" aria-expanded="false">展开前情</button><div class="llf" hidden>${full}</div>`:''}</div>`;
  $('#llMore')?.addEventListener('click',e=>{ e.stopPropagation(); const f=l.querySelector('.llf'), o=f.hidden; f.hidden=!o; l.classList.toggle('open',o); e.currentTarget.textContent=o?'收起':'展开前情'; e.currentTarget.setAttribute('aria-expanded',String(o)); placeMarks(); });
}
### novelOutline
function novelOutline(tab,q){
  /* v9.62：最上面"正在读"一行；搜索收进放大镜；每回一根细进度条 */
  tab=tab||novelOutline.last||'hui'; novelOutline.last=tab;
  const lim=P.length-1;
  q=(q??novelOutline.q??'').trim(); novelOutline.q=q;
  const searching=!!q||novelOutline.srch;
  let body='';
  if(q){ body=searchBody(tab,q,lim); }
  else if(tab==='hui'){
    const curI=Math.max(S.current,0), curH=huiOf(curI);
    body=(RD.size?`<button class="olnow" data-go="${P[curI].n}"><span>正在读</span><b>${esc(unitName(curH.n))}</b><em>${pctOf()}%</em><span class="chev">›</span></button>`:'')+HUI.map(h=>{
        const cur=S.current>=h.first&&curH.n===h.n;
        const [a,b]=h.t.split(/\s+|　/);
        const all=(REC().find(x=>x['回']===h.n)||{})['小节']||[]; let prev=h.first;
        const end=(HUI.find(x=>x.n===h.n+1)||{first:P.length}).first;
        let n=0; for(let j=h.first;j<end;j++) if(RD.has(j)) n++;
        const pc=Math.round(n/(end-h.first)*100);
        /* 回目标题本身就是书的目录，都显示；小节概要是对内容的复述，只显示读过的 */
        const kids=all.map(x=>{const s0=prev; prev=IDX[x['到']]+1; return isRd(IDX[x['到']])?`<button data-go="${P[s0].n}"><span>${esc(x['写'])}</span></button>`:'';}).join('');
        const left=all.filter(x=>!isRd(IDX[x['到']])).length;
        return `<details ${cur?'open':''}><summary>${D.titled?'':`<span class="on hn">${h.n===0?'':`第${cnum(h.n)}${UNIT}`}</span>`}<span class="ot">${esc(a)}${b?'<br>'+esc(b):''}</span><span class="olpb" title="已读 ${pc}%" aria-label="${n?`已读 ${pc}%`:'未读'}"><i style="width:${pc}%"></i></span></summary>
          <div class="kids"><div class="olgo"><button data-go="${P[h.first].n}"><span>本${UNIT}开头</span></button>${h.first>0&&!isRd(h.first-1)?`<button class="olfrom" data-from="${h.first}">从这里开始读</button>`:''}</div>${kids}${left&&n?`<p class="fog" style="padding:4px 0">未读的部分不显示概要。</p>`:''}</div></details>`;}).join('');
    body+=`<div class="fog">可以跳到任何一${UNIT}；没翻过的内容不算已读。</div>`;
  } else {
    const lm=seenTo();
    const ps=PEOPLE.filter(p=>p.ap.some(known));
    if(!ps.length) body='<div class="fog">已出场的人物将在此显示。</div>';
    else{
      const by={}; ps.forEach(p=>{const h=huiOf(p.first).n;(by[h]=by[h]||[]).push(p);});
      body=`<p class="mini">按出场先后排列，信息以阅读进度为界。</p>`+Object.keys(by).map(h=>`<div class="h3">${unitName(+h)}</div>${by[h].map(p=>{
        const id=p.ids.filter(x=>x[0]<=lm&&known(x[0])).pop(); const n=p.ap.filter(known).length;
        return `<button class="prow" data-pc="${p.id}"><b>${esc(pName(p,lm))}</b><span>${esc(id?id[1]:'')}</span><small>出场 ${n} 段</small></button>`;}).join('')}`).join('');
    }
  }
  openSheet(`<div class="shead"><span class="ttl">导览</span>
    <div class="seg" role="group" aria-label="导览分类"><button data-ot="hui" aria-pressed="${tab==='hui'}">${D.titled?'篇目':UNIT==='回'?'回目':'章节'}</button><button data-ot="ppl" aria-pressed="${tab==='ppl'}">人物</button></div>
    <button class="x srchb" id="olS" aria-label="搜索" aria-expanded="${searching}">${ic('search','')}</button><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="srch" ${searching?'':'hidden'}><input id="olQ" type="search" enterkeyhint="search" placeholder="${tab==='ppl'?'搜索人物、称呼':'搜索已读正文'}" value="${esc(q)}" aria-label="搜索"></div>
  <div class="sbody"><div class="ol" id="olBody">${body}</div></div>
  ${tab==='hui'&&RD.size?`<div class="sfoot olfoot"><button class="btn ghost wide" id="olRecap">${ic('toc','')}阅读回顾</button></div>`:''}`,{tall:true});
  const sh=$('#sheet');
  const qi=$('#olQ'); let qt=null;
  $('#olS').onclick=()=>{ const box=sh.querySelector('.srch'), open=box.hidden; box.hidden=!open; novelOutline.srch=open; $('#olS').setAttribute('aria-expanded',String(open)); if(open) qi.focus(); else if(qi.value){ qi.value=''; novelOutline.q=''; novelOutline(tab,''); } };
  qi.oninput=()=>{ clearTimeout(qt); qt=setTimeout(()=>{ novelOutline.q=qi.value.trim(); $('#olBody').innerHTML=novelOutline.q?searchBody(tab,novelOutline.q,lim):''; if(!novelOutline.q){ novelOutline(tab,''); setTimeout(()=>$('#olQ')?.focus(),0); return; } wireOl(); },160); };
  const wireOl=()=>{ sh.querySelectorAll('#olBody [data-pc]').forEach(b=>b.onclick=()=>personCard(+b.dataset.pc,null,'ppl'));
    sh.querySelectorAll('#olBody [data-go]').forEach(b=>b.onclick=()=>{closeSheet();jump(b.dataset.go);}); };
  wireOl();
  sh.querySelectorAll('[data-ot]').forEach(b=>b.onclick=()=>novelOutline(b.dataset.ot));
  sh.querySelectorAll('[data-pc]').forEach(b=>b.onclick=()=>personCard(+b.dataset.pc,null,'ppl'));
  $('#olRecap')?.addEventListener('click',()=>novelRecap(Infinity,true,true));
  wireFrom(sh,()=>novelOutline(tab));
}
### propOutline
function propOutline(){
  let h='';
  { const mains=P.map((p,i)=>[p,i]).filter(([p])=>depth(p.n)===0);
    h=mains.map(([p,i],k)=>{
      const end=k+1<mains.length?mains[k+1][1]:P.length;
      const kids=P.slice(i+1,end).map((c,j)=>[c,i+1+j]).filter(([c])=>depth(c.n)===1);
      const cur=S.current>=i&&S.current<end;
      let n=0; for(let j=i;j<end;j++) if(RD.has(j)) n++;
      const pc=Math.round(n/(end-i)*100);
      /* 主干命题、二级命题的原文只在读过后显示；没读过的只露编号 */
      const t=(c,j,len)=>isRd(j)?`<span>${esc(firstLine(txt(c),len))}</span>`:`<span class="unrd">未读</span>`;
      return `<details ${cur?'open':''}><summary><span class="on">${p.n}</span>${isRd(i)?`<span class="ot">${esc(firstLine(txt(p),80))}</span>`:`<span class="ot unrd">未读</span>`}<span class="olpb" aria-label="${n?`已读 ${pc}%`:'未读'}"><i style="width:${pc}%"></i></span></summary>
        <div class="kids"><div class="olgo"><button data-go="${p.n}"><span class="kn">${p.n}</span><span>本节开头</span></button>${i>0&&!isRd(i-1)?`<button class="olfrom" data-from="${i}">从这里开始读</button>`:''}</div>${kids.map(([c,j])=>`<button data-go="${c.n}"><span class="kn">${c.n}</span>${t(c,j,40)}</button>`).join('')}</div></details>`;}).join('');
  }
  const curI=Math.max(S.current,0);
  openSheet(`<div class="shead"><span class="ttl">导览</span><button class="x srchb" id="olS" aria-label="搜索" aria-expanded="false">${ic('search','')}</button><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="srch" hidden><input id="olQ" type="search" enterkeyhint="search" placeholder="${D.orig?'搜索已读正文（中文或原文）':'搜索已读正文'}" aria-label="搜索"></div>
  <div class="sbody"><div id="olHit" class="ol" hidden></div><div id="olTree">${RD.size?`<button class="olnow" data-go="${P[curI].n}"><span>正在读</span><b>命题 ${P[curI].n}</b><em>${pctOf()}%</em><span class="chev">›</span></button>`:''}<p class="mini">编号即目录：1、2、3 为主干，1.1 是对 1 的注释，1.11 是对 1.1 的注释。可以跳到任何位置；没翻过的内容不算已读。</p>
  <div class="ol"><details><summary><span class="on" style="font-size:16px">序</span><span class="ot">前言</span></summary><div class="kids"><button id="goPre"><span>前言</span></button></div></details>${h}</div></div></div>
  ${RD.size?`<div class="sfoot olfoot"><button class="btn ghost wide" id="olRecap">${ic('toc','')}阅读回顾</button></div>`:''}`,{tall:true});
  $('#olRecap')?.addEventListener('click',()=>propRecap(true));
  $('#goPre').onclick=()=>{closeSheet();noRead();preEl.scrollIntoView({block:'start'});};
  wireFrom($('#sheet'),()=>propOutline());
  const qi=$('#olQ'); let qt=null;
  $('#olS').onclick=()=>{ const box=$('#sheet .srch'), open=box.hidden; box.hidden=!open; $('#olS').setAttribute('aria-expanded',String(open)); if(open) qi.focus(); else { qi.value=''; qi.oninput(); } };
  qi.oninput=()=>{ clearTimeout(qt); qt=setTimeout(()=>{ const q=qi.value.trim(); $('#olTree').hidden=!!q; const hb=$('#olHit'); hb.hidden=!q;
    hb.innerHTML=q?searchBody('hui',q,P.length-1):''; hb.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{closeSheet();jump(b.dataset.go);}); },160); };
}
### bookInfo
function bookInfo(k,prog,openList){
  /* v9.63：详情和"待揭晓"合成一张：封面、书名、作者、进度 → 主线进度、"N 处伏笔待揭晓" → 版本来源 → 继续阅读 */
  const b=BOOKS[k], row=SHELF.find(x=>x[0]===k)||[k,'',b.t,'',''], st=bookStat(k);
  const keep=BK; setBook(k); const {book,mine}=unresolved(), m=ML(), mlN=m?mlDone(m):0, mlT=m?m.pieces.length:0, mq=m?m.q:'';
  const ur=[...book.map(s=>({pos:posOf(s['提出']),q:s['问题'],g:S.guesses[s.id]})),...mine.map(n=>({pos:n.at,q:n.text,g:n.guess?{text:n.guess}:null,mine:1}))].sort((a,b2)=>a.pos-b2.pos).map(x=>({...x,lab:label(x.pos)}));
  setBook(keep);
  openSheet(`<div class="shead"><span class="ttl">书籍详情</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody">
    <div class="bihead">${coverHTML(b.t,b.cover)}<div class="bit"><b>${esc(b.t)}</b>${row[3]?`<span>${esc(authorName(row[3],row[4]))}</span>`:''}<span class="bip">${st.fin?'已读完':st.started?`${esc(st.where)}　${st.pct}%`:'尚未开始'}</span>${st.started&&!st.fin?`<span class="pbar"><i style="width:${st.pct}%"></i></span>`:''}</div></div>
    ${m&&!b.imported?`<div class="biml"><div class="mlh"><span class="mltag">主线</span><span class="mlc">已拼上 ${mlN} / ${mlT}</span></div><p class="mlq">${esc(mq)}</p></div>`:''}
    ${ur.length?`<button class="biur" id="biUr" aria-expanded="${!!openList}"><span class="dia"></span>${ur.length} 处伏笔待揭晓<span class="chev">${openList?'⌃':'›'}</span></button><div class="biurl" ${openList?'':'hidden'}>${ur.map(x=>`<div class="cr"><span class="crh"><span>${esc(x.lab)}</span>${x.mine?'<span class="seal dai">我发现的</span>':''}${x.g?'<span class="crg">已猜</span>':''}</span><span class="crq">${esc(x.q)}</span></div>`).join('')}<p class="mini" style="margin-top:8px">答案在后文。</p></div>`:''}
    <dl class="meta bimeta">${b.rows.map(([a,v])=>`<dt>${a}</dt><dd>${v}</dd>`).join('')}</dl>
    <p class="mini" style="margin-top:16px">${b.imported?'解释和回顾都以你的阅读进度为界。':BOOKS[k].rows.some(r=>r[1].includes('切换只看中文'))||k==='tractatus'?'可在阅读设置中切换只看中文或只看原文。':'解释、伏笔和人物信息均以你的阅读进度为界，不涉及后文。'}</p></div>
  <div class="sfoot">${b.imported?'<button class="btn ghost danger" id="bDel">从书架移除</button>':''}<button class="btn" id="bOpen" style="margin-left:auto">${st.fin?'再读一遍':st.started?'继续阅读':'开始阅读'}</button></div>`,{tall:true});
  $('#bOpen')?.addEventListener('click',()=>{closeSheet();openBook(k);});
  $('#bDel')?.addEventListener('click',()=>{ closeSheet(); removeBooks([k]); });
  $('#biUr')?.addEventListener('click',e=>{ const l=$('#sheet .biurl'), o=l.hidden; l.hidden=!o; e.currentTarget.setAttribute('aria-expanded',String(o)); e.currentTarget.querySelector('.chev').textContent=o?'⌃':'›'; });
}
### unresolvedSheet
function unresolvedSheet(k){ bookInfo(k,bookStat(k).prog,true); }   /* v9.63：并进书籍详情 */
### mePage
function mePage(){
  /* v9.63：账号卡上直接点昵称改名；"账号与安全"一页取消，退出登录在最下面 */
  const u=curUser(), x=meStats(), open=!!mePage.open, off=mePage.off||0;
  showPage(pageHTML('我的','书架',`
    <div class="mecard" id="meAcc">${avatarHTML(u,'big')}<span class="mew">${u?`<button class="mename" id="meName" aria-label="修改昵称">${esc(u.name)}<span class="pen">${ic('pen','')}</span></button>`:'<b>未登录</b>'}<small>${u?`${esc(maskAcc(u.id))}　${mdate(u.t)}加入　${SRV?'记录保存在服务器上':'记录保存在这台设备上'}`:'<button class="linkbtn" id="meLogin">登录或注册</button>'}</small></span></div>
    <div class="mestat"><div><b>${x.st}<small>天</small></b><span>连续阅读</span></div><div><b>${x.wmin}<small>分</small></b><span>本周阅读</span></div><div><b>${x.fin}<small>本</small></b><span>读完</span></div><div><b>${x.sv}<small>处</small></b><span>揭晓伏笔</span></div></div>
    <section class="mebox"><div class="meh"><b>阅读打卡</b><button class="linkbtn" id="calTg" aria-expanded="${open}">${open?'收起':'展开月历'}</button></div>
      ${open?calHTML(off):`<div class="week">${weekDays().map((d,i)=>`<div class="wkc"><span class="wd">${WD[i]}</span>${dayCell(d,true)}</div>`).join('')}</div>`}
      <p class="melg"><span class="svk"></span>那天有伏笔揭晓</p></section>
    <nav class="melist" aria-label="设置">
      <button id="mePref"><span>阅读偏好</span><small>带读${MODE_T[PROF.mode]}</small><span class="chev">›</span></button>
      <button id="meAbout"><span>关于伏笔</span><small></small><span class="chev">›</span></button></nav>
    ${u?'<button class="meout" id="secOut">退出登录</button>':''}`),()=>shelf());
  $('#calTg').onclick=()=>{ mePage.open=!open; mePage.off=0; mePage(); };
  $('#calP')?.addEventListener('click',()=>{ mePage.off=off-1; mePage(); });
  const pick=()=>{ const n=new Date(), y=+$('#calY').value, m=Math.min(+$('#calM').value, y===n.getFullYear()?n.getMonth():11); mePage.off=(y-n.getFullYear())*12+(m-n.getMonth()); mePage(); };
  $('#calY')?.addEventListener('change',pick); $('#calM')?.addEventListener('change',pick); $('#calN')?.addEventListener('click',()=>{ if(off<0){ mePage.off=off+1; mePage(); } });
  $('#meLogin')?.addEventListener('click',()=>authPage('login'));
  $('#meName')?.addEventListener('click',()=>{ const b=$('#meName'); b.outerHTML=`<span class="menedit"><input id="secName" maxlength="12" value="${esc(u.name)}" aria-label="昵称"><button class="linkbtn" id="secSave">保存</button></span>`;
    const inp=$('#secName'); inp.focus(); inp.select();
    const done=()=>{ const n=inp.value.trim(); if(n&&n!==u.name){ ACC.users[u.id].name=n; saveAcc(); toast('<div class="tq">昵称已保存</div>',null,2000); } mePage(); };
    $('#secSave').onclick=done; inp.addEventListener('keydown',e=>{ if(e.key==='Enter') done(); if(e.key==='Escape') mePage(); }); });
  $('#secOut')?.addEventListener('click',()=>{ if(!confirm('确定退出登录？阅读记录仍保留在这台设备上。')) return; ACC.cur=null; saveAcc(); authPage('login'); });
  $('#mePref').onclick=()=>prefPage(); $('#meAbout').onclick=()=>aboutPage();
}
### css
/* ===== v9.63 交互重做第二批 ===== */
.lastline.rc{display:block;margin:8px 0 16px;padding:0;color:var(--mute)}
.lastline.rc::before,.lastline.rc::after{display:none}
.lastline.rc .llt{display:flex;align-items:center;gap:12px;color:var(--faint);font-size:var(--t-tag);line-height:1}
.lastline.rc .llt::before,.lastline.rc .llt::after{content:"";flex:1;height:1px;background:var(--line)}
.lastline .llr{margin-top:10px;padding:0 4px}
.lastline .ll1{margin:0;font-family:var(--serif);font-size:var(--t-aux);line-height:1.7;color:var(--ink2);text-align:center}
.lastline #llMore{display:flex;margin:4px auto 0;padding:4px 0;font-size:var(--t-tag)}
.lastline .llf{margin-top:8px;padding:12px 16px;border-radius:6px;background:var(--paper2);font-family:var(--serif);font-size:var(--t-aux);line-height:1.75;color:var(--ink2)}
.lastline .llf p{margin:0 0 6px}
.lastline .llf .llh{font-family:var(--ui);font-size:var(--t-tag);color:var(--mute);margin:8px 0 4px}
.lastline .llf .llh:first-child{margin-top:0}
.lastline .lln{font-family:var(--num);color:var(--mute);margin-right:8px}
.olnow{display:flex;align-items:center;gap:10px;width:100%;margin:0 0 8px;padding:12px 14px;border-radius:6px;background:var(--paper2);text-align:left;font-family:var(--ui)}
.olnow span:first-child{font-size:var(--t-tag);color:var(--mute)}
.olnow b{flex:1;font-family:var(--serif);font-size:var(--t-body);font-weight:600;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.olnow em{font-style:normal;font-size:var(--t-aux);color:var(--ink2);font-variant-numeric:tabular-nums}
.olpb{flex:none;align-self:center;width:36px;height:2px;border-radius:1px;background:var(--line);overflow:hidden}
.olpb i{display:block;height:2px;background:var(--ink)}
.shead .srchb{margin-left:auto}.shead .srchb+.x{margin-left:0}
.shead .srchb svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.7}
.srch[hidden]{display:none}
.bihead{display:flex;gap:16px;align-items:center;margin:4px 0 16px}
.bihead .cover{width:64px;flex:none}
.bit{display:flex;flex-direction:column;gap:4px;min-width:0;flex:1}
.bit b{font-family:var(--serif);font-size:var(--t-key);font-weight:600}
.bit span{font-size:var(--t-aux);color:var(--mute)}
.bit .bip{color:var(--ink2);margin-top:4px}
.biml{padding:12px 0;border-top:1px solid var(--line)}
.biml .mlq{font-family:var(--kai);font-size:15px;margin:6px 0 0}
.biur{display:flex;align-items:center;gap:8px;width:100%;padding:12px 0;border-top:1px solid var(--line);font-size:var(--t-aux);color:var(--hl);text-align:left}
.biur .dia{width:6px;height:6px;background:var(--hl);transform:rotate(45deg)}
.biur .chev{margin-left:auto}
.biurl{padding-bottom:4px}
.bimeta{padding-top:12px;border-top:1px solid var(--line);font-size:var(--t-aux)}
.bkm{flex:none;align-self:center;width:32px;height:32px;display:flex;align-items:center;justify-content:center;color:var(--mute);font-size:16px;letter-spacing:.1em;margin-left:4px;cursor:pointer}
.books.lay-list .book{align-items:center}
.mename{display:inline-flex;align-items:center;gap:6px;font-family:var(--serif);font-size:var(--t-key);font-weight:600;color:var(--ink);padding:0}
.mename .pen svg{width:14px;height:14px;stroke:var(--mute);fill:none;stroke-width:1.6}
.menedit{display:flex;align-items:center;gap:8px}
.menedit input{height:32px;width:9em;padding:0 8px;border:1px solid var(--line);border-radius:6px;background:var(--sheet);font:var(--t-body) var(--serif);color:var(--ink)}
.mecard{cursor:default}
.meout{display:block;margin:24px auto 0;padding:8px 16px;font-size:var(--t-aux);color:var(--mute)}
