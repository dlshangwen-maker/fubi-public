"""v9.55（10-28）第三阶段替换第一块：全局视觉换成批注本（设计规范 v2）+ 注册页（A）。
颜色：纸 #ECEEE7、墨 #1E2622；朱 #B23A2E = 书里埋的（伏笔、主线，原来的金色 --hl 全部换成朱）；黛 #2F4A8C = 读者自己的（划线、想法、疑问）。
字体：宋 = 书，楷 = 批注（伏笔的问题、主线问题），苹方 = 界面。圆角三级 2/6/14。面板标题 17。毛笔 logo。
注册页：logo + 一句话 + 账号 + 密码 + 注册 + "已有账号，登录 · 先体验"；昵称不在注册时问（默认"读者+后四位"，在"我的 › 账号与安全"里改）。
备份 Demo/模板_v70备份.html。每处替换断言只匹配 1 次。"""
import os
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:80]); s=s.replace(a,b)

# ---------- 主题：四套纸墨，朱/黛只调亮度 ----------
rep('<meta name="theme-color" content="#ECEFE9">','<meta name="theme-color" content="#ECEEE7">')
rep('[data-theme=sage]{color-scheme:light;--paper:#ECEFE9;--paper2:#E1E6DE;--ink:#1F2A26;--ink2:#2C3733;--mute:#66706B;--faint:#9AA39D;--line:#C9CFC7;--sheet:#F7F8F5;--field:#FFFFFF;--blue:#2F4A8C;--blue-soft:#DCE2EF;--hl:#D9A92B;--hl-soft:rgba(217,169,43,.30);--mark:rgba(217,169,43,.22);',
    '[data-theme=sage]{color-scheme:light;--paper:#ECEEE7;--paper2:#E2E5DC;--ink:#1E2622;--ink2:#38423D;--mute:#69736D;--faint:#9CA49F;--line:#CDD2C9;--sheet:#F6F7F3;--field:#F6F7F3;--blue:#2F4A8C;--blue-soft:#DCE2EF;--hl:#B23A2E;--hl-soft:rgba(178,58,46,.14);--mark:rgba(178,58,46,.08);--on-hl:#F6F2EC;')
rep('--blue:#2F4A8C;--blue-soft:#E1E6F2;--hl:#D9A92B;--hl-soft:rgba(217,169,43,.30);--mark:rgba(217,169,43,.22);',
    '--blue:#2F4A8C;--blue-soft:#E1E6F2;--hl:#B23A2E;--hl-soft:rgba(178,58,46,.13);--mark:rgba(178,58,46,.07);--on-hl:#FFF8F2;')
rep('--blue:#3A5590;--blue-soft:#E0DCD4;--hl:#C98F1E;--hl-soft:rgba(201,143,30,.30);--mark:rgba(201,143,30,.22);',
    '--blue:#3A5590;--blue-soft:#E0DCD4;--hl:#A8382B;--hl-soft:rgba(168,56,43,.14);--mark:rgba(168,56,43,.08);--on-hl:#FBF3E6;')
rep('--blue:#94AEE6;--blue-soft:#25304A;--hl:#C9992A;--hl-soft:rgba(201,153,42,.30);--mark:rgba(201,153,42,.20);',
    '--blue:#94AEE6;--blue-soft:#25304A;--hl:#D9705F;--hl-soft:rgba(217,112,95,.20);--mark:rgba(217,112,95,.10);--on-hl:#151918;')
rep("['sage','灰绿','#ECEFE9','#1F2A26']","['sage','灰绿','#ECEEE7','#1E2622']")
# 金底上的深色字 → 朱底上的浅色字
s=s.replace('background:var(--hl);color:#1F2A26','background:var(--hl);color:var(--on-hl)')
rep('.tabs .k-q[aria-pressed=true] svg{color:#1F2A26}','.tabs .k-q[aria-pressed=true] svg{color:var(--on-hl)}')
rep('.fxlabel{position:absolute;left:50%;bottom:calc(100% + 10px);transform:translateX(-50%);white-space:nowrap;font:600 13px/1 var(--ui);color:#1F2A26;','.fxlabel{position:absolute;left:50%;bottom:calc(100% + 10px);transform:translateX(-50%);white-space:nowrap;font:600 13px/1 var(--ui);color:var(--on-hl);')
rep("const COVER_C=['#3B3A52','#5B2A26','#1F2A26',","const COVER_C=['#3B3A52','#5B2A26','#1E2622',")
rep('.cover{width:84px;flex:none;aspect-ratio:3/4.3;background:#1F2A26;color:#ECEFE9;','.cover{width:84px;flex:none;aspect-ratio:3/4.3;background:#1E2622;color:#ECEEE7;')
rep('--t-page:22px; --t-panel:18px;','--t-page:22px; --t-panel:17px;')
rep('  --safe-b:env(safe-area-inset-bottom,0px);\n}','  --safe-b:env(safe-area-inset-bottom,0px); --safe-t:env(safe-area-inset-top,0px);\n  --ease:cubic-bezier(.2,.8,.2,1);\n}')

# ---------- 规范 v2 覆盖层（放在样式最后，按规范统一圆角、字体、颜色归属） ----------
OVR=r'''
/* ===== v9.55 设计规范 v2（批注本）：统一覆盖层 =====
   三种墨：墨 = 正文和界面；朱（--hl）= 书里埋的；黛（--blue）= 读者自己的。圆角三级：纸上的 2 / 按钮输入框 6 / 面板 14 */
/* 读者自己的：划线改黛色细线（原来金色） */
mark.ul{background-image:linear-gradient(transparent 84%,var(--blue) 84%,var(--blue) 92%,transparent 92%)}
.tag.t-hl{background:var(--blue-soft);color:var(--blue)}
.tabs .k-hl{color:var(--blue);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--blue) 45%,transparent);background:transparent}
.tabs .k-hl[aria-pressed=true]{background:var(--blue);color:var(--paper);box-shadow:none}
.q.hl .qt{border-left-color:var(--blue)}
.mdv blockquote{border-left-color:var(--line)}
mark.qh{background:var(--blue-soft)}
.qquote{border-left-color:var(--line)}
/* 批注用楷体：伏笔的问题、主线问题 */
.q.fbook .qt,.mlq,#mlfx .mlfx-q{font-family:var(--kai)}
/* 圆角 */
.btn{border-radius:6px}
.btn.wide{height:44px;padding:0 14px;display:flex;align-items:center;justify-content:center;letter-spacing:.04em}
.fld input,.libsearch input,.srch input,.chrow .chname,textarea,.calsel select,.qrow textarea{border-radius:6px}
.fld input{background:var(--sheet);font-size:var(--t-body)}
.selmenu{border-radius:6px}.selmenu button{border-radius:4px}
.toast{border-radius:6px}
.q .from .tag{border-radius:2px;height:20px;padding:0 6px;line-height:20px}
.mltag{border-radius:2px;height:20px;line-height:20px;padding:0 6px;background:var(--hl);color:var(--on-hl)}
.tag.t-main{background:var(--hl);color:var(--on-hl)}
.mlp i{border-radius:2px}
.mainl{border-radius:6px}
.tabs button,.hotw button,.qzchips button,.qsug button,.refchip{border-radius:6px}
.guess,.q .ans,.exnote,.rfx,.askq,.askit,.nudge,.qdone,.kind button,.qpick button,.sw,.mestat div,.qzc,.qzres,.qz .qzo button,.qzo button{border-radius:6px}
.qseg{border-radius:6px}.qseg button{border-radius:4px}
.seg{border-radius:6px}
/* 面板：标题宋体 17 */
.shead .n{font-family:var(--serif);font-size:var(--t-panel)}
/* 首次流程顶部避开状态栏 */
.flow .flbar{padding-top:calc(var(--safe-t) + 14px)}
@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;transition-duration:.01ms!important}}
'''
rep('</style>',OVR+'</style>')

# ---------- 毛笔 logo：笔杆墨色，笔头一半在地平线上（朱实心）、一半埋下（朱虚线） ----------
i=s.index('const LOGO=`'); j=s.index('`;',i)+2
s=s[:i]+'''const LOGO=`<svg class="logo" viewBox="0 0 40 40" aria-hidden="true"><clipPath id="lgU"><rect width="40" height="25"/></clipPath><clipPath id="lgD"><rect y="26.6" width="40" height="14"/></clipPath>
  <rect x="18.4" y="2.5" width="3.2" height="11" rx="1.2" fill="var(--ink)"/><rect x="17.2" y="12.6" width="5.6" height="2.4" rx=".8" fill="var(--ink)"/>
  <g clip-path="url(#lgU)"><path d="M17.4 15H22.6Q26 21 24.6 27.5Q23 33.5 20 38Q17 33.5 15.4 27.5Q14 21 17.4 15Z" fill="var(--hl)"/></g>
  <g clip-path="url(#lgD)"><path d="M24.6 27.5Q23 33.5 20 38Q17 33.5 15.4 27.5" fill="none" stroke="var(--hl)" stroke-width="1.4" stroke-dasharray="1.8 1.8" stroke-linecap="round"/></g>
  <path d="M5 25.8H35" stroke="var(--ink)" stroke-width="1.6" stroke-linecap="round"/></svg>`;'''+s[j:]
# 书末收尾：整支笔从地平线下升起（埋下的都读过了）
i=s.index('const FINLOGO=`'); j=s.index('`;',i)+2
s=s[:i]+'''const FINLOGO=`<svg class="finlogo" viewBox="0 0 40 40" aria-hidden="true"><clipPath id="finU"><rect width="40" height="25.8"/></clipPath>
  <g clip-path="url(#finU)"><g class="finnib"><rect x="18.4" y="-6" width="3.2" height="11" rx="1.2" fill="var(--ink)"/><rect x="17.2" y="4.1" width="5.6" height="2.4" rx=".8" fill="var(--ink)"/><path d="M17.4 6.5H22.6Q26 12.5 24.6 19Q23 25 20 25.6Q17 25 15.4 19Q14 12.5 17.4 6.5Z" fill="var(--hl)"/></g></g>
  <path d="M5 25.8H35" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`;'''+s[j:]

# ---------- 注册页（A）：logo + 一句话；账号、密码；注册；已有账号，登录 · 先体验 ----------
old_auth=s[s.index("function authPage(tab='reg'){"):s.index("/* ---------- 问卷：")]
new_auth='''function authPage(tab='reg'){
  /* 规范 v2（10-27 用户定）：注册只留 logo + 一句话 + 账号 + 密码 + 两个按钮；昵称不问，默认"读者+账号后四位"，在"我的 › 账号与安全"里改 */
  const reg=tab==='reg';
  showPage(flowHTML(1,2,`<div class="auth">
    <div class="authbrand"><div class="aumark">${LOGO}<b>伏笔</b></div><p class="autag">不是帮你读完，是让你想读下去。</p></div>
    <div class="auform">
    <label class="fld"><span>手机号或邮箱</span><input id="auAcc" autocomplete="username" inputmode="email"></label>
    <label class="fld"><span>密码</span><input id="auPw" type="password" autocomplete="${reg?'new-password':'current-password'}" ${reg?'placeholder="6～20 位，含字母和数字"':''}></label>
    <p class="aumsg" id="auMsg" role="alert"></p>
    <button class="btn wide" id="auGo">${reg?'注册':'登录'}</button>
    <p class="auswitch">${reg?'<button class="linkbtn" data-t="login">已有账号，登录</button>':'<button class="linkbtn" data-t="reg">注册新账号</button>'}<span class="dot">·</span><button class="linkbtn" id="auSkip">先体验</button></p>
    </div></div>`));
  document.querySelectorAll('.auswitch [data-t]').forEach(x=>x.onclick=()=>authPage(x.dataset.t));
  /* 测试阶段（用户 10-26）：不校验，填什么都能进；空着也行。已有的账号直接登录，没有的就当新注册 */
  const enter=()=>{ const acc=$('#auAcc').value.trim()||'体验账号';
    if(!ACC.users[acc]) ACC.users[acc]={name:defaultName(acc==='体验账号'?'':acc),pw:pwh($('#auPw').value),t:Date.now()};
    ACC.cur=acc; saveAcc(); PROF.qz?shelf():quizPage({first:true}); };
  $('#auGo').onclick=enter; $('#auSkip').onclick=()=>{ $('#auAcc').value=''; enter(); };
  document.querySelectorAll('#auAcc,#auPw').forEach(x=>x.addEventListener('keydown',e=>{ if(e.key==='Enter') $('#auGo').click(); }));
}
'''
s=s.replace(old_auth,new_auth)
AUCSS=r'''
/* 注册页（规范 v2 第六节 1）：竖屏上下排，横屏左右排 */
.flow .auth{max-width:360px;margin:0 auto;padding-top:10vh;display:flex;flex-direction:column;gap:48px}
.authbrand{display:block;margin:0;text-align:center}
.aumark{display:flex;justify-content:center;align-items:center;gap:10px}
.aumark .logo{width:44px;height:44px}
.aumark b{font-family:var(--serif);font-size:26px;font-weight:600;letter-spacing:.28em;margin-right:-.28em}
.autag{margin:16px 0 0;font-family:var(--serif);font-size:15px;color:var(--ink2);letter-spacing:.06em}
.auform .fld{margin:0 0 16px}
.auform .aumsg{min-height:0;margin:0}
.auform .aumsg:empty{display:none}
.auform .btn.wide{margin-top:8px}
.auswitch{margin-top:16px}
.brand .logo{width:36px;height:36px}
@media (orientation:landscape) and (max-height:520px){
  .flow .auth{max-width:720px;flex-direction:row;align-items:center;gap:48px;padding-top:4vh}
  .flow .auth .authbrand{flex:1}.flow .auth .auform{width:300px;flex:none}
  .auform .fld input{height:40px}.auform .btn.wide{height:40px}
}
'''
rep('</style>',AUCSS+'</style>')
open(P,'w',encoding='utf-8').write(s); print('ok')
# 补：墨底提示条按钮颜色（10-28 截图发现朱色在墨底上看不清）
s=open(P,encoding='utf-8').read()
if '--toast-ac' not in s:
    a="@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;transition-duration:.01ms!important}}"
    s=s.replace(a,a+"\n/* 墨底提示条上的按钮：朱色太暗，用浅赭（样稿 v0.3）；夜间提示条是浅底，用深朱 */\n:root{--toast-ac:#E8C9A0}[data-theme=night]{--toast-ac:#A8382B}\n.toast button,.mlfx-a button{color:var(--toast-ac)}")
    open(P,'w',encoding='utf-8').write(s)
