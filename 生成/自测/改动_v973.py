"""v9.73（11-02 真账号·前端）：服务器开了账号（window.FUBI.auth）时：
登录页换成"邮箱 + 密码"，注册多一个邀请码，登录页有"忘记密码"（两步：发验证码 → 填验证码和新密码）；
登录状态来自服务端（FUBI.user），ACC 变成服务端用户的镜像；账户页的昵称、头像、改密码、退出、注销都走接口；
没有 auth 时一切照旧（demo 合并版、单文件版自测不变）。备份 模板_v89备份.html"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)
# 1) ACC 镜像
rep("const ACC=Object.assign({users:{},cur:null},store.get(AKEY)||{});","""const AUTH=!!(window.FUBI&&window.FUBI.auth);   /* 服务器开了真账号 */
const ACC=AUTH?(()=>{ const u=window.FUBI.user, o={users:{},cur:null}; if(u){ o.cur=u.email; o.users[u.email]={name:u.name,t:(u.t||0)*1000,av:u.av&&Object.keys(u.av).length?u.av:undefined,pw:''}; } return o; })()
  :Object.assign({users:{},cur:null},store.get(AKEY)||{});""")
rep("const saveAcc=()=>store.set(AKEY,ACC);","const saveAcc=()=>{ if(!AUTH) store.set(AKEY,ACC); };\nconst api=async(path,obj)=>{ try{ const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj||{})}); let j={}; try{ j=await r.json(); }catch(e){} return {ok:r.ok,status:r.status,...j}; }catch(e){ return {ok:false,error:'网络不通，请稍后再试'}; } };")
# 2) 登录页
i=s.index("function authPage(tab='reg'){"); j=s.index("\n}\n",i)+3
OLD=s[i:j]
NEW='''function authPage(tab='reg'){
  if(AUTH) return authPageSrv(tab);
'''+OLD[len("function authPage(tab='reg'){\n"):]+'''/* 真账号（服务器开了 FUBI_AUTH）：邮箱 + 密码；注册要邀请码；忘记密码发验证码到邮箱 */
function authPageSrv(tab='login'){
  const reg=tab==='reg', fg=tab==='forgot';
  const field=(id,label,type,extra='')=>`<label class="fld"><span>${label}</span><input id="${id}" type="${type}" ${extra}></label>`;
  const title=fg?'<p class="autag">输入注册时用的邮箱，我们发一个验证码给你。</p>':'<p class="autag">不是帮你读完，是让你想读下去。</p>';
  showPage(flowHTML(1,2,`<div class="auth">
    <div class="authbrand"><div class="aumark">${LOGO}<b>伏笔</b></div>${title}</div>
    <div class="auform">
    ${field('auAcc','邮箱','email','autocomplete="username" inputmode="email"')}
    ${fg?`<div id="auStep2" hidden>${field('auCode','邮箱里的验证码','text','inputmode="numeric" autocomplete="one-time-code" maxlength="6"')}${field('auPw','新密码','password','autocomplete="new-password" placeholder="8 位以上，要有字母和数字"')}</div>`
        :`${field('auPw','密码','password',`autocomplete="${reg?'new-password':'current-password'}" ${reg?'placeholder="8 位以上，要有字母和数字"':''}`)}${reg?field('auInv','邀请码','text','autocomplete="off" autocapitalize="characters" placeholder="朋友给你的 8 位邀请码"'):''}`}
    <p class="aumsg" id="auMsg" role="alert"></p>
    <button class="btn wide" id="auGo">${fg?'发送验证码':reg?'注册':'登录'}</button>
    <p class="auswitch">${fg?'<button class="linkbtn" data-t="login">想起来了，去登录</button>':reg?'<button class="linkbtn" data-t="login">已有账号，登录</button>':'<button class="linkbtn" data-t="reg">注册新账号</button><span class="dot">·</span><button class="linkbtn" data-t="forgot">忘记密码</button>'}</p>
    </div></div>`,true));
  document.querySelectorAll('.auswitch [data-t]').forEach(x=>x.onclick=()=>authPageSrv(x.dataset.t));
  $('#flBack')?.addEventListener('click',()=>{ AFTER_LOGIN=null; AFTER_T=''; homePage(); });
  const msg=(t,ok)=>{ const m=$('#auMsg'); m.textContent=t||''; m.style.color=ok?'var(--ink2)':''; }, busy=(on)=>{ $('#auGo').disabled=on; };
  const after=()=>{ /* 登录成功：刷新页面，让服务器按账号给出书和阅读记录；想回到的动作靠 sessionStorage 带过去 */
    try{ sessionStorage.setItem('fubi_after',JSON.stringify({t:Date.now(),hint:AFTER_T})); }catch(e){} location.reload(); };
  let step=1;
  $('#auGo').onclick=async()=>{ const email=$('#auAcc').value.trim(); msg(''); if(!email){ $('#auAcc').focus(); return msg('请填邮箱'); }
    busy(true);
    try{
      if(fg){
        if(step===1){ const r=await api('/api/auth/forgot',{email}); if(!r.ok) return msg(r.error||'没发出去，请稍后再试'); step=2; $('#auStep2').hidden=false; $('#auGo').textContent='改好密码'; $('#auCode').focus(); return msg(r.msg||'验证码已发出',true); }
        const r=await api('/api/auth/reset',{email,code:$('#auCode').value.trim(),password:$('#auPw').value}); if(!r.ok) return msg(r.error||'没改成功');
        const l=await api('/api/auth/login',{email,password:$('#auPw').value}); if(l.ok) return after(); authPageSrv('login'); return;
      }
      const pw=$('#auPw').value; if(!pw){ $('#auPw').focus(); return msg('请填密码'); }
      const r=await api(reg?'/api/auth/register':'/api/auth/login',reg?{email,password:pw,invite:$('#auInv').value}:{email,password:pw});
      if(!r.ok) return msg(r.error||'没成功，请稍后再试'); after();
    } finally { busy(false); } };
  document.querySelectorAll('.auform input').forEach(x=>x.addEventListener('keydown',e=>{ if(e.key==='Enter') $('#auGo').click(); }));
}
'''
s=s[:i]+NEW+s[j:]
# 3) 登录后刷新：回到想去的地方（简单版：刷新后进书架；问卷没填就先填）
rep("if(window.__TEST) shelf(); else if(!curUser()) homePage(); else if(!PROF.qz) quizPage({first:true}); else shelf();",
    "try{ if(AUTH) sessionStorage.removeItem('fubi_after'); }catch(e){}\nif(window.__TEST) shelf(); else if(!curUser()) homePage(); else if(!PROF.qz) quizPage({first:true}); else shelf();")
# 4) 账户页：昵称、头像、改密码、退出、注销走接口
rep("ACC.users[u.id].name=n; saveAcc(); $('#secNm').textContent=n;","ACC.users[u.id].name=n; saveAcc(); if(AUTH) api('/api/auth/profile',{name:n}); $('#secNm').textContent=n;")
rep("$('#avSave').onclick=()=>{ ACC.users[u.id].av={ch:ch===u.name.slice(0,1)?'':ch,c,img}; saveAcc();","$('#avSave').onclick=()=>{ ACC.users[u.id].av={ch:ch===u.name.slice(0,1)?'':ch,c,img}; saveAcc(); if(AUTH) api('/api/auth/profile',{av:ACC.users[u.id].av});")
rep("$('#avReset').onclick=()=>{ delete ACC.users[u.id].av; saveAcc();","$('#avReset').onclick=()=>{ delete ACC.users[u.id].av; saveAcc(); if(AUTH) api('/api/auth/profile',{av:{}});")
open(P,'w',encoding='utf-8').write(s); print('ok')
