### authPage
/* ===== v9.65（用户 10-30）web 版访客逻辑：输入网址不登录就能看首页（产品介绍 + 精读版封面和详情）；读正文、划线记录、找书、导入都要登录。
   点"登录后阅读"弹登录，登录成功回到刚才要读的那本（AFTER_LOGIN）。 ===== */
let AFTER_LOGIN=null, AFTER_T='';
const goAfter=()=>{ const f=AFTER_LOGIN; AFTER_LOGIN=null; AFTER_T=''; if(f) f(); else shelf(); };
function homePage(){
  const bk=SHELF.filter(r=>!(BOOKS[r[0]]&&BOOKS[r[0]].imported));
  showPage(`<div class="pg home">
    <div class="hmbar">${LOGO}<b>伏笔</b><button class="linkbtn" id="hmLogin">登录</button></div>
    <div class="hmhero"><p class="hmtag">不是帮你读完，是让你想读下去。</p>
      <p class="hmsub">伏笔不替你读，陪你把原文读完。书里埋着的问题、逐段的解释和读后的回顾，都只讲到你读过的地方，不剧透。</p></div>
    <div class="about hmfeat">
      <div class="welrow"><span class="welic">${ic('qm','')}</span><div><b>看不懂，点一下</b><span>点任一段看解释，深浅三档。</span></div></div>
      <div class="welrow"><span class="welic gemic"><i></i></span><div><b>带着问题往下读</b><span>页边的“伏笔”是书里埋着的问题，读到答案处自动揭晓。</span></div></div>
      <div class="welrow"><span class="welic">${ic('toc','')}</span><div><b>放下了也接得上</b><span>再打开时，先告诉你上次读到哪、前面讲了什么。</span></div></div>
    </div>
    <div class="hmh"><h2>精读版</h2><small>${bk.length} 本 · 登录后阅读</small></div>
    <div class="books lay-grid hmbooks">${bk.map(([k,id,t])=>`<button class="book gb" data-k="${k}" aria-label="《${esc(t)}》详情">${coverHTML(t,BOOKS[k].cover)}<span class="t">${esc(t)}</span></button>`).join('')}</div>
    <div class="hmcta"><button class="btn wide" id="hmReg">注册，开始读</button><button class="linkbtn" id="hmLog2">已有账号，登录</button></div>
    ${SRV?'<p class="foot">还可以从古登堡计划、维基文库找书，或导入自己的电子书，登录后使用。</p>':''}
  </div>`);
  $('#hmLogin').onclick=()=>authPage('login'); $('#hmLog2').onclick=()=>authPage('login'); $('#hmReg').onclick=()=>authPage('reg');
  document.querySelectorAll('.hmbooks [data-k]').forEach(b=>b.onclick=()=>bookInfo(b.dataset.k,'尚未开始',false,true));
}
/* ---------- 导入书籍（独立页面，v9.65 用户 10-30：直接导入缺乏引导）：说明能导什么、会发生什么 → 选文件 → 页内看进度 → 去读 ---------- */
function importPage(){
  if(!SRV) return shelf();
  const fm=SRV.formats.map(x=>x.replace(/^\./,'')), acc=fm.map(x=>'.'+x).join(',');
  const COMMON=['epub','pdf','txt','docx','mobi'].filter(x=>fm.includes(x)), rest=fm.length-COMMON.length;
  showPage(pageHTML('导入','书架',`<div class="imp">
    <p class="implead">把你手里的电子书放进来，伏笔会按你的阅读进度陪你读。</p>
    <label class="impdrop" id="impDrop"><input type="file" id="impFile" hidden accept="${acc}"><b>选择文件</b><span>或把文件拖到这里</span><small>常用格式：${COMMON.join('、')}，另支持${rest}种其他格式。单个文件不超过 ${SRV.maxMB} MB。</small></label>
    <div id="impStat" aria-live="polite"></div>
    <ol class="impsteps">
      <li><b>识别章节和封面</b>自动分章；分得不准，可以在书里的“阅读设置 › 更多设置”里调整。</li>
      <li><b>外文书先译成中文</b>译完之前，可以先读原文。</li>
      <li><b>逐步生成解释和回顾</b>需要一些时间；生成期间可以照常阅读、划线、写想法，还没生成的段落会有说明。</li>
    </ol>
    <p class="impnote">请只导入你有权阅读的书。导入的书只有你自己看得到。</p>
    <p class="impalt">手里没有文件？<button class="linkbtn" id="impFind">去找书 ›</button></p></div>`),()=>shelf());
  const stat=(cls,html)=>{ const e=$('#impStat'); e.className='imstat '+cls; e.innerHTML=html; };
  const run=async file=>{
    if(file.size>SRV.maxMB*1048576) return stat('failed',`<b>文件太大</b><span>上限 ${SRV.maxMB} MB，这个文件 ${(file.size/1048576).toFixed(1)} MB。</span>`);
    const nm=esc(file.name.replace(/\.[^.]+$/,''));
    stat('busy',`<b>《${nm}》</b><span>正在上传…</span>`);
    try{ const r=await fetch('/api/import',{method:'POST',headers:{'X-Filename':encodeURIComponent(file.name)},body:file}); const j=await r.json();
      if(!r.ok) throw new Error(j.error||'导入失败');
      stat('busy',`<b>《${nm}》</b><span>正在识别章节和封面…</span>`);
      for(let k=0;k<180;k++){ const st=await (await fetch('/api/books/'+j.id+'/status')).json(); if(st.status!=='parsing'){ if(st.status==='failed') throw new Error(st.err||'导入失败'); break; } await new Promise(z=>setTimeout(z,1000)); }
      const d=await (await fetch('/api/books/'+j.id)).json(); ALL[j.id]=d; addShelfBook(j.id,d);
      const m=d.meta, ch=m.chars>=1e4?(m.chars/1e4).toFixed(1).replace(/\.0$/,'')+' 万':m.chars;
      stat('ok',`<b>《${esc(m.title)}》已放进书架</b><span>${m.chapters} 章，约 ${ch} 字。解释和回顾会在后台逐步生成。</span><div class="imact"><button class="btn" id="imGo">去读</button><button class="btn ghost" id="imMore">再导入一本</button></div>`);
      $('#imGo').onclick=()=>openBook(j.id); $('#imMore').onclick=()=>importPage();
    }catch(e){ stat('failed',`<b>没能导入</b><span>${esc(e.message)}</span><div class="imact"><button class="btn ghost" id="imRetry">重新选择文件</button></div>`); $('#imRetry').onclick=()=>importPage(); }
  };
  $('#impFile').onchange=()=>{ const f=$('#impFile').files[0]; if(f) run(f); };
  const dz=$('#impDrop');
  ['dragenter','dragover'].forEach(t=>dz.addEventListener(t,e=>{ e.preventDefault(); dz.classList.add('over'); }));
  ['dragleave','drop'].forEach(t=>dz.addEventListener(t,e=>{ e.preventDefault(); dz.classList.remove('over'); }));
  dz.addEventListener('drop',e=>{ const f=e.dataTransfer&&e.dataTransfer.files[0]; if(f) run(f); });
  $('#impFind').onclick=()=>findPage();
}
function authPage(tab='reg'){
  /* 规范 v2：注册只留 logo + 一句话 + 账号 + 密码 + 按钮；昵称不问，默认"读者+账号后四位"，在"我的 › 个人账户"里改。v9.65：左上角 ‹ 回访客首页；去掉"先体验"（不登录也能浏览首页） */
  const reg=tab==='reg';
  showPage(flowHTML(1,2,`<div class="auth">
    <div class="authbrand"><div class="aumark">${LOGO}<b>伏笔</b></div><p class="autag">不是帮你读完，是让你想读下去。</p>${AFTER_T?`<p class="auhint">${esc(AFTER_T)}</p>`:''}</div>
    <div class="auform">
    <label class="fld"><span>手机号或邮箱</span><input id="auAcc" autocomplete="username" inputmode="email"></label>
    <label class="fld"><span>密码</span><input id="auPw" type="password" autocomplete="${reg?'new-password':'current-password'}" ${reg?'placeholder="6～20 位，含字母和数字"':''}></label>
    <p class="aumsg" id="auMsg" role="alert"></p>
    <button class="btn wide" id="auGo">${reg?'注册':'登录'}</button>
    <p class="auswitch">${reg?'<button class="linkbtn" data-t="login">已有账号，登录</button>':'<button class="linkbtn" data-t="reg">注册新账号</button>'}</p>
    </div></div>`,true));
  document.querySelectorAll('.auswitch [data-t]').forEach(x=>x.onclick=()=>authPage(x.dataset.t));
  $('#flBack')?.addEventListener('click',()=>{ AFTER_LOGIN=null; AFTER_T=''; homePage(); });
  /* 测试阶段（用户 10-26）：不校验，填什么都能进；空着也行。已有的账号直接登录，没有的就当新注册 */
  const enter=()=>{ const acc=$('#auAcc').value.trim()||'体验账号';
    if(!ACC.users[acc]) ACC.users[acc]={name:defaultName(acc==='体验账号'?'':acc),pw:pwh($('#auPw').value),t:Date.now()};
    ACC.cur=acc; saveAcc(); PROF.qz?goAfter():quizPage({first:true}); };
  $('#auGo').onclick=enter;
  document.querySelectorAll('#auAcc,#auPw').forEach(x=>x.addEventListener('keydown',e=>{ if(e.key==='Enter') $('#auGo').click(); }));
}
### calHTML
function calHTML(off){
  /* v9.65（用户 10-30）：周视图和月视图用同一套格子（同高、同圆角、同底色、都显示当天分钟数），展开只是多几行 */
  const now=new Date(), m=new Date(now.getFullYear(),now.getMonth()+off,1), y=m.getFullYear(), mo=m.getMonth(), nd=new Date(y,mo+1,0).getDate(), lead=(m.getDay()+6)%7;
  let cells=WD.split('').map(x=>`<span class="wd">${x}</span>`).join('')+'<span></span>'.repeat(lead), days=0;
  for(let d=1;d<=nd;d++){ const x=new Date(y,mo,d); if(dayOn(PROF.days[dayKey(x)])) days++; cells+=dayCell(x,true); }
  /* 年份：从最早有记录（或注册）的那年到今年 */
  const ks=Object.keys(PROF.days).map(k=>+k.split('-')[0]), u=curUser(), y0=Math.min(now.getFullYear(),...ks,u?new Date(u.t).getFullYear():now.getFullYear());
  const ys=[]; for(let i=y0;i<=now.getFullYear();i++) ys.push(i);
  const ms=[...Array(12)].map((_,i)=>i).filter(i=>y<now.getFullYear()||i<=now.getMonth());
  return `<div class="calh"><button id="calP" aria-label="上个月">‹</button><span class="calsel"><select id="calY" aria-label="年份">${ys.map(v=>`<option value="${v}" ${v===y?'selected':''}>${v} 年</option>`).join('')}</select><select id="calM" aria-label="月份">${ms.map(v=>`<option value="${v}" ${v===mo?'selected':''}>${v+1} 月</option>`).join('')}</select></span><button id="calN" aria-label="下个月" ${off>=0?'disabled':''}>›</button></div><div class="cal mo">${cells}</div><p class="calsum">这个月读了 ${days} 天</p>`;
}
function weekHTML(){
  const ds=weekDays(), n=ds.filter(x=>dayOn(PROF.days[dayKey(x)])).length, f=x=>`${x.getMonth()+1} 月 ${x.getDate()} 日`;
  return `<div class="calh wkh"><span class="calwk">${f(ds[0])} — ${f(ds[6])}</span></div><div class="cal wk">${WD.split('').map(x=>`<span class="wd">${x}</span>`).join('')}${ds.map(d=>dayCell(d,true)).join('')}</div><p class="calsum">本周读了 ${n} 天</p>`;
}
### mePage
function mePage(){
  /* v9.65：账号卡整张可点，进"个人账户"页（昵称、密码、退出登录、注销都在那里） */
  const u=curUser(), x=meStats(), open=!!mePage.open, off=mePage.off||0;
  showPage(pageHTML('我的','书架',`
    <button class="mecard" id="meAcc">${avatarHTML(u,'big')}<span class="mew"><b>${u?esc(u.name):'未登录'}</b><small>${u?`${esc(maskAcc(u.id))}　个人账户`:'登录后记录会跟着账号'}</small></span><span class="chev">›</span></button>
    <div class="mestat"><div><b>${x.st}<small>天</small></b><span>连续阅读</span></div><div><b>${x.wmin}<small>分</small></b><span>本周阅读</span></div><div><b>${x.fin}<small>本</small></b><span>读完</span></div><div><b>${x.sv}<small>处</small></b><span>揭晓伏笔</span></div></div>
    <section class="mebox"><div class="meh"><b>阅读打卡</b><button class="linkbtn" id="calTg" aria-expanded="${open}">${open?'收起':'展开月历'}</button></div>
      ${open?calHTML(off):weekHTML()}
      <p class="melg"><span class="svk"></span>那天有伏笔揭晓</p></section>
    <nav class="melist" aria-label="设置">
      <button id="mePref"><span>阅读偏好</span><small>带读${MODE_T[PROF.mode]}</small><span class="chev">›</span></button>
      <button id="meAbout"><span>关于伏笔</span><small></small><span class="chev">›</span></button></nav>`),()=>shelf());
  $('#calTg').onclick=()=>{ mePage.open=!open; mePage.off=0; mePage(); };
  $('#calP')?.addEventListener('click',()=>{ mePage.off=off-1; mePage(); });
  const pick=()=>{ const n=new Date(), y=+$('#calY').value, m=Math.min(+$('#calM').value, y===n.getFullYear()?n.getMonth():11); mePage.off=(y-n.getFullYear())*12+(m-n.getMonth()); mePage(); };
  $('#calY')?.addEventListener('change',pick); $('#calM')?.addEventListener('change',pick); $('#calN')?.addEventListener('click',()=>{ if(off<0){ mePage.off=off+1; mePage(); } });
  $('#meAcc').onclick=()=>u?secPage():authPage('login'); $('#mePref').onclick=()=>prefPage(); $('#meAbout').onclick=()=>aboutPage();
}
### secPage
function secPage(){
  /* v9.65（用户 10-30）：个人账户页恢复成独立页面：昵称、密码、账号信息、退出登录、注销账号 */
  const u=curUser(); if(!u) return authPage('login');
  showPage(pageHTML('个人账户','我的',`
    <div class="secid">${avatarHTML(u,'big')}<span class="secnm"><b id="secNm">${esc(u.name)}</b><small>${esc(maskAcc(u.id))}</small></span></div>
    <section class="mebox"><label class="fld"><span>昵称</span><input id="secName" maxlength="12" value="${esc(u.name)}"></label><button class="btn ghost" id="secSave">保存昵称</button></section>
    <section class="mebox"><label class="fld"><span>修改密码</span><input id="secPw" type="password" autocomplete="new-password" placeholder="新密码，6～20 位，含字母和数字"></label><button class="btn ghost" id="secPwSave">保存新密码</button></section>
    <dl class="meta medl"><dt>账号</dt><dd>${esc(maskAcc(u.id))}</dd><dt>加入时间</dt><dd>${mdate(u.t)}</dd><dt>数据</dt><dd>${SRV?'阅读记录保存在服务器上':'阅读记录保存在这台设备上'}</dd></dl>
    <button class="btn ghost wide" id="secOut">退出登录</button>
    <button class="meout" id="secDel">注销账号</button>`),()=>mePage());
  $('#secSave').onclick=()=>{ const n=$('#secName').value.trim(); if(!n){ $('#secName').focus(); return; } ACC.users[u.id].name=n; saveAcc(); $('#secNm').textContent=n; const av=document.querySelector('.secid .av'); if(av) av.textContent=n.slice(0,1); toast('<div class="tq">昵称已保存</div>',null,2000); };
  $('#secPwSave').onclick=()=>{ const p=$('#secPw').value; if(!p){ $('#secPw').focus(); return; } ACC.users[u.id].pw=pwh(p); saveAcc(); $('#secPw').value=''; toast('<div class="tq">密码已修改</div>',null,2000); };
  $('#secOut').onclick=()=>{ if(!confirm('确定退出登录？阅读记录仍保留在这台设备上。')) return; ACC.cur=null; saveAcc(); homePage(); };
  $('#secDel').onclick=()=>{ if(!confirm('注销后，这个账号和它的设置会被删除，无法恢复。书里的阅读记录仍留在这台设备上。确定注销？')) return; delete ACC.users[u.id]; ACC.cur=null; saveAcc(); homePage(); };
}
### css
/* ===== v9.65 web 访客首页、导入页、月历统一、个人账户 ===== */
.home{padding:calc(var(--safe-t) + 16px) 24px calc(var(--safe-b) + 40px);max-width:560px;margin:0 auto}
.hmbar{display:flex;align-items:center;gap:10px;height:40px}
.hmbar .logo{width:32px;height:32px}
.hmbar b{font-family:var(--serif);font-size:20px;font-weight:600;letter-spacing:.2em}
.hmbar .linkbtn{margin-left:auto}
.hmhero{margin:32px 0 24px}
.hmtag{margin:0;font-family:var(--serif);font-size:20px;font-weight:600;line-height:1.6;letter-spacing:.04em;text-wrap:balance}
.hmsub{margin:12px 0 0;font-size:var(--t-body);line-height:1.8;color:var(--ink2)}
.hmfeat{padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.hmfeat .welrow{margin-bottom:16px}.hmfeat .welrow:last-child{margin-bottom:0}
.hmh{display:flex;align-items:baseline;gap:12px;margin:32px 0 0}
.hmh h2{margin:0;font-family:var(--serif);font-size:var(--t-page);font-weight:600;letter-spacing:.08em}
.hmh small{font-size:var(--t-aux);color:var(--mute)}
.hmbooks{margin-top:16px}
.hmbooks .book.gb{cursor:pointer}
.hmcta{display:flex;flex-direction:column;align-items:center;gap:12px;margin-top:40px}
.hmcta .btn.wide{max-width:320px}
.home .foot{text-align:center;margin-top:24px}
.auhint{margin:12px 0 0;font-size:var(--t-aux);color:var(--hl);text-align:center}
.imp{padding-top:8px}
.implead{margin:16px 0 20px;font-family:var(--serif);font-size:var(--t-key);line-height:1.7}
.impdrop{display:flex;flex-direction:column;align-items:center;gap:6px;padding:32px 16px;border:1px dashed var(--faint);border-radius:6px;background:var(--sheet);text-align:center;cursor:pointer}
.impdrop b{display:inline-flex;align-items:center;justify-content:center;height:40px;padding:0 24px;border-radius:6px;background:var(--ink);color:var(--paper);font-size:var(--t-body);font-weight:400;letter-spacing:.04em}
.impdrop span{font-size:var(--t-aux);color:var(--mute)}
.impdrop small{font-size:var(--t-tag);color:var(--faint);line-height:1.6;max-width:26em}
.impdrop.over{border-color:var(--blue);background:var(--blue-soft)}
.imstat{margin:16px 0 0;padding:12px 16px;border-radius:6px;background:var(--paper2);display:flex;flex-direction:column;gap:4px}
.imstat:empty{display:none}
.imstat b{font-family:var(--serif);font-size:var(--t-body);font-weight:600}
.imstat span{font-size:var(--t-aux);color:var(--mute);line-height:1.6}
.imstat.failed span{color:#A33A2A}
.imstat.busy b::after{content:"";display:inline-block;width:6px;height:6px;margin-left:8px;border-radius:50%;background:var(--hl);animation:blink 1.2s ease-in-out infinite;vertical-align:middle}
.imact{display:flex;gap:12px;margin-top:8px}
.imact .btn{height:40px;padding:0 18px}
.impsteps{margin:28px 0 0;padding:0;list-style:none;counter-reset:s}
.impsteps li{position:relative;padding:0 0 16px 32px;font-size:var(--t-aux);line-height:1.7;color:var(--mute);counter-increment:s}
.impsteps li::before{content:counter(s);position:absolute;left:0;top:1px;width:20px;height:20px;border-radius:50%;box-shadow:inset 0 0 0 1px var(--faint);font-size:var(--t-tag);line-height:20px;text-align:center;color:var(--mute)}
.impsteps li b{display:block;font-size:var(--t-body);font-weight:600;color:var(--ink);margin-bottom:2px}
.impnote{margin:8px 0 0;font-size:var(--t-tag);color:var(--faint);line-height:1.7}
.impalt{margin:16px 0 0;font-size:var(--t-aux);color:var(--mute)}
.impalt .linkbtn{display:inline;padding:0}
/* 月历：周视图和月视图同一套格子 */
.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;max-width:none;margin:0;text-align:center}
.cal .wd{font-size:var(--t-tag);color:var(--faint);line-height:20px;text-align:center}
.cal .d{height:44px;width:auto;max-width:none;aspect-ratio:auto;border-radius:6px;background:var(--sheet);font-size:var(--t-aux)}
.cal .d small{font-size:10px;line-height:1;margin-top:3px;min-height:10px;opacity:.85}
.cal .d.on{background:var(--ink)}
.calh{max-width:none;min-height:36px;margin:0 0 8px;display:flex;align-items:center;justify-content:space-between}
.calh .calsel{display:flex;gap:8px;align-items:center}
.calh button{width:32px;height:32px;display:flex;align-items:center;justify-content:center;padding:0;font-size:18px;color:var(--mute)}
.calh.wkh{justify-content:flex-start}
.calwk{font-size:var(--t-aux);color:var(--mute)}
.calsum{text-align:left;margin:12px 0 0}
/* 个人账户 */
.secid{display:flex;align-items:center;gap:16px;margin:8px 0 16px}
.secnm{display:flex;flex-direction:column;gap:2px;min-width:0}
.secnm b{font-family:var(--serif);font-size:var(--t-page);font-weight:600}
.secnm small{font-size:var(--t-aux);color:var(--mute)}
.mebox .btn.ghost{height:40px;padding:0 18px;display:inline-flex;align-items:center}
.medl{margin-bottom:16px}
.secid{align-items:center}
.secnm b{line-height:1.3}
### wireImport
function wireImport(){
  /* v9.65：选文件移到独立的导入页（importPage）；这里只管书架底部"导入失败"那一条的"移除" */
  document.querySelectorAll('[data-del]').forEach(b=>b.onclick=async()=>{ await fetch('/api/books/'+b.dataset.del,{method:'DELETE'}); location.reload(); });
}
