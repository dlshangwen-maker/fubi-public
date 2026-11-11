### homePage
function homePage(){
  /* v9.66（用户 10-30："不要这么刻意"）：没登录的首页就是一个书架——logo、右上角"登录"、精读版的封面，没有大标题、介绍、大按钮。
     点封面看书籍详情；读、找书、导入都要登录（点了才弹登录，登录后回到原处） */
  const bk=SHELF.filter(r=>!(BOOKS[r[0]]&&BOOKS[r[0]].imported));
  showPage(`<div class="pg home">
    <div class="hmbar">${LOGO}<b>伏笔</b><button class="linkbtn" id="hmLogin">登录</button></div>
    <div class="shh"><h1>书架</h1></div>
    <div class="books lay-grid hmbooks">${bk.map(([k,id,t])=>`<button class="book gb" data-k="${k}" aria-label="《${esc(t)}》详情">${coverHTML(t,BOOKS[k].cover)}<span class="t">${esc(t)}</span></button>`).join('')}</div>
    <p class="foot">登录后可以阅读，也可以找书、导入自己的书。</p>
  </div>`);
  $('#hmLogin').onclick=()=>authPage('login');
  document.querySelectorAll('.hmbooks [data-k]').forEach(b=>b.onclick=()=>bookInfo(b.dataset.k,'尚未开始',false,true));
}
### avatar
/* ---------- 头像（用户 10-30）：一个字 + 一种颜色，或上传自己的图片（裁成方形、缩到 160px 存在本机）。默认取昵称第一个字、墨色 ---------- */
const AV_COLORS=['#1E2622','#B23A2E','#2F4A8C','#3B3A52','#5B2A26','#2C3E3A','#4A3B2A','#4B2E45'];
const avatarHTML=(u,cls='')=>{ const a=(u&&u.av)||{}, ch=esc((a.ch||(u&&u.name)||'读').slice(0,1));
  if(a.img) return `<span class="av img ${cls}" aria-hidden="true"><img src="${a.img}" alt=""></span>`;
  return `<span class="av ${cls}" style="background:${a.c||AV_COLORS[0]}" aria-hidden="true">${ch}</span>`; };
function avatarSheet(u,done){
  const a=Object.assign({ch:'',c:AV_COLORS[0],img:''},u.av||{}); let ch=a.ch||u.name.slice(0,1), c=a.c, img=a.img;
  const draw=()=>{ $('#avPrev').innerHTML=avatarHTML({name:u.name,av:{ch,c,img}},'xl'); $('#avChars').hidden=!!img; };
  openSheet(`<div class="shead"><span class="ttl">头像</span><button class="x" data-close aria-label="关闭">×</button></div>
  <div class="sbody"><div class="avprev" id="avPrev"></div>
    <div id="avChars"><label class="fld"><span>字</span><input id="avCh" maxlength="1" value="${esc(ch)}" aria-label="头像上的字"></label>
    <p class="flab">颜色</p><div class="avcols">${AV_COLORS.map(x=>`<button class="avcol" data-c="${x}" style="background:${x}" aria-pressed="${x===c}" aria-label="颜色 ${x}"></button>`).join('')}</div></div>
    <div class="avact"><label class="btn ghost avup">${img?'换一张图片':'上传图片'}<input type="file" id="avFile" accept="image/*" hidden></label>${img?'<button class="linkbtn" id="avNoImg">不用图片，改用字</button>':''}</div>
    <p class="mini avnote">图片只存在这台设备上，会自动裁成正方形。</p></div>
  <div class="sfoot"><button class="btn ghost" id="avReset">恢复默认</button><button class="btn" id="avSave" style="margin-left:auto">保存</button></div>`);
  draw();
  $('#avCh').oninput=e=>{ ch=e.target.value.slice(0,1)||u.name.slice(0,1); draw(); };
  document.querySelectorAll('#sheet .avcol').forEach(b=>b.onclick=()=>{ c=b.dataset.c; document.querySelectorAll('#sheet .avcol').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); draw(); });
  $('#avNoImg')?.addEventListener('click',()=>{ img=''; avatarSheet({...u,av:{ch,c,img:''}},done); });
  $('#avFile').onchange=()=>{ const f=$('#avFile').files[0]; if(!f) return;
    if(!/^image\//.test(f.type)){ toast('<div class="tq">请选择图片文件</div>',null,2500); return; }
    const rd=new FileReader(); rd.onload=()=>{ const im=new Image(); im.onload=()=>{ const n=Math.min(im.width,im.height), cv=document.createElement('canvas'); cv.width=cv.height=160;
        cv.getContext('2d').drawImage(im,(im.width-n)/2,(im.height-n)/2,n,n,0,0,160,160); img=cv.toDataURL('image/jpeg',.82); avatarSheet({...u,av:{ch,c,img}},done); };
      im.onerror=()=>toast('<div class="tq">这张图片打不开</div>',null,2500); im.src=rd.result; }; rd.readAsDataURL(f); };
  $('#avReset').onclick=()=>{ delete ACC.users[u.id].av; saveAcc(); closeSheet(); done(); toast('<div class="tq">已恢复默认头像</div>',null,2000); };
  $('#avSave').onclick=()=>{ ACC.users[u.id].av={ch:ch===u.name.slice(0,1)?'':ch,c,img}; saveAcc(); closeSheet(); done(); toast('<div class="tq">头像已保存</div>',null,2000); };
}
### secPage
function secPage(){
  /* 个人账户：头像（点了改）、昵称、密码、账号信息、退出登录、注销。v9.66：账号信息改成分隔行；不给用户看"数据保存在哪" */
  const u=curUser(); if(!u) return authPage('login');
  showPage(pageHTML('个人账户','我的',`
    <div class="secid"><button class="avbtn" id="secAv" aria-label="修改头像">${avatarHTML(u,'big')}<span class="avedit">${ic('pen','')}</span></button><span class="secnm"><b id="secNm">${esc(u.name)}</b><small>点头像可以更换</small></span></div>
    <section class="mebox"><label class="fld"><span>昵称</span><input id="secName" maxlength="12" value="${esc(u.name)}"></label><button class="btn ghost" id="secSave">保存昵称</button></section>
    <section class="mebox"><label class="fld"><span>修改密码</span><input id="secPw" type="password" autocomplete="new-password" placeholder="新密码，6～20 位，含字母和数字"></label><button class="btn ghost" id="secPwSave">保存新密码</button></section>
    <div class="secinfo"><div><span>账号</span><b>${esc(maskAcc(u.id))}</b></div><div><span>加入时间</span><b>${mdate(u.t)}</b></div></div>
    <div class="secbtns"><button class="btn ghost wide" id="secOut">退出登录</button><button class="meout" id="secDel">注销账号</button></div>`),()=>mePage());
  $('#secAv').onclick=()=>avatarSheet(u,()=>secPage());
  $('#secSave').onclick=()=>{ const n=$('#secName').value.trim(); if(!n){ $('#secName').focus(); return; } ACC.users[u.id].name=n; saveAcc(); $('#secNm').textContent=n; if(!(u.av&&(u.av.ch||u.av.img))){ const av=document.querySelector('.secid .av'); if(av&&!av.querySelector('img')) av.textContent=n.slice(0,1); } toast('<div class="tq">昵称已保存</div>',null,2000); };
  $('#secPwSave').onclick=()=>{ const p=$('#secPw').value; if(!p){ $('#secPw').focus(); return; } ACC.users[u.id].pw=pwh(p); saveAcc(); $('#secPw').value=''; toast('<div class="tq">密码已修改</div>',null,2000); };
  $('#secOut').onclick=()=>{ if(!confirm('确定退出登录？')) return; ACC.cur=null; saveAcc(); homePage(); };
  $('#secDel').onclick=()=>{ if(!confirm('注销后，这个账号和它的设置会被删除，无法恢复。确定注销？')) return; delete ACC.users[u.id]; ACC.cur=null; saveAcc(); homePage(); };
}
### css
/* ===== v9.66 访客书架、头像、账户页信息区 ===== */
.home{padding:calc(var(--safe-t) + 16px) 24px calc(var(--safe-b) + 40px);max-width:560px;margin:0 auto}
.home .shh{margin-top:24px}
.home .foot{margin-top:32px;font-size:var(--t-tag);color:var(--faint);line-height:1.7;text-align:left;font-family:var(--ui)}
.home .hmbooks{margin-top:16px}
.av.xl{width:96px;height:96px;font-size:44px}
.av.img{background:none;overflow:hidden;padding:0}
.av.img img{width:100%;height:100%;object-fit:cover;display:block}
.avbtn{position:relative;flex:none;padding:0;border-radius:50%}
.avbtn .avedit{position:absolute;right:-2px;bottom:-2px;width:22px;height:22px;border-radius:50%;background:var(--sheet);box-shadow:0 0 0 1px var(--line);display:flex;align-items:center;justify-content:center}
.avbtn .avedit svg{width:12px;height:12px;stroke:var(--ink2);fill:none;stroke-width:1.8}
.avprev{display:flex;justify-content:center;margin:8px 0 20px}
.avcols{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 4px}
.avcol{width:32px;height:32px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
.avcol[aria-pressed=true]{box-shadow:0 0 0 2px var(--sheet),0 0 0 4px var(--ink)}
.avact{display:flex;align-items:center;gap:16px;margin-top:20px}
.avact .avup{height:40px;padding:0 18px;display:inline-flex;align-items:center;cursor:pointer}
.avnote{margin-top:12px}
#avCh{width:5em;text-align:center;font-family:var(--serif);font-size:18px}
.secinfo{margin:0 0 16px;border-top:1px solid var(--line)}
.secinfo>div{display:flex;align-items:center;justify-content:space-between;min-height:48px;border-bottom:1px solid var(--line);font-size:var(--t-body)}
.secinfo span{color:var(--mute);font-size:var(--t-aux)}
.secinfo b{font-weight:400;color:var(--ink)}
.secbtns{display:flex;flex-direction:column;gap:8px;margin-top:24px}
.secbtns .btn.wide{height:44px}
.secbtns .meout{margin:8px auto 0}
