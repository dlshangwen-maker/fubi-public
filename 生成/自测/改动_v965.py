"""v9.65（10-30 用户四点）：
① web 版访客逻辑：输入网址不登录就能看"首页"（产品介绍 + 精读版封面、点封面看书籍详情），读正文 / 划线记录 / 找书 / 导入 / 我的都要登录；
   点"登录后阅读"弹登录页，登录成功回到刚才要读的那本；登录页左上角 ‹ 回首页；去掉"先体验"；"退出登录"回首页；启动时没登录进首页（不再直接进登录页）。
   （用户定：不登录只能浏览，读正文也要登录。）
② 导入书籍独立页面：书架"导入"进整页——说明、选文件/拖文件、能导入的格式和大小、会发生什么三步、版权提醒、页内进度和结果（去读 / 再导入）、"去找书"。
③ 月历：周视图和月视图同一套格子（同高 44、同圆角 6、同底色、都显示分钟数），周视图也有"X 月 X 日 — X 月 X 日"标题和"本周读了 N 天"。
④ 个人账户页恢复：账号卡整张可点进；页内头像昵称、改昵称、改密码、账号信息（账号、加入时间、数据位置）、退出登录、注销账号。
备份 Demo/模板_v80备份.html。函数体在 改动_v965_片段.js。"""
import os,re
B=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+'/'
P=B+'Demo/模板.html'
s=open(P,encoding='utf-8').read()
FR={}; cur=None
for line in open(os.path.dirname(os.path.abspath(__file__))+'/改动_v965_片段.js',encoding='utf-8').read().split('\n'):
    m=re.match(r'^### (\S+)',line)
    if m: cur=m.group(1); FR[cur]=[]; continue
    if cur: FR[cur].append(line)
FR={k:'\n'.join(v).strip('\n')+'\n' for k,v in FR.items()}
def rep(a,b,n=1):
    global s
    c=s.count(a); assert c==n,(c,a[:90]); s=s.replace(a,b)
def fn(name,key=None):
    global s
    i=s.index('\nfunction '+name+'(')+1; j=s.index('\n}\n',i)+2
    s=s[:i]+FR[key or name]+s[j:]
# ---- 函数替换 ----
# authPage 前面的访客变量、homePage、importPage 一起放在 authPage 的位置
fn('authPage'); fn('calHTML'); fn('mePage'); fn('secPage'); fn('wireImport')
# weekHTML 紧跟在 calHTML 后面：FR['calHTML'] 里已带 weekHTML
# ---- ① 访客：启动、退出 ----
rep("""if(window.__TEST) shelf(); else if(!curUser()) authPage(Object.keys(ACC.users).length?'login':'reg'); else if(!PROF.qz) quizPage({first:true}); else shelf();""",
    """if(window.__TEST) shelf(); else if(!curUser()) homePage(); else if(!PROF.qz) quizPage({first:true}); else shelf();""")
# 问卷第一屏的 ‹ 回注册 → 回首页（已登录，不再回注册）；跳过/完成走 goAfter
rep("""  $('#flBack')?.addEventListener('click',()=>authPage('reg'));
  document.querySelectorAll('[data-edit]')""","""  $('#flBack')?.addEventListener('click',()=>{ ACC.cur=null; saveAcc(); homePage(); });
  document.querySelectorAll('[data-edit]')""")
rep("""$('#qzSkip')?.addEventListener('click',()=>{ PROF.qz={skipped:true,t:Date.now()}; setMode('light'); shelf(); });""",
    """$('#qzSkip')?.addEventListener('click',()=>{ PROF.qz={skipped:true,t:Date.now()}; setMode('light'); goAfter(); });""")
rep("""first?shelf():prefPage(); });""","""first?goAfter():prefPage(); });""")
# 访客点书：书籍详情（访客版：底部"登录后阅读"）
rep("""function bookInfo(k,prog,openList){""","""function bookInfo(k,prog,openList,guest){""")
rep("""<button class="btn" id="bOpen" style="margin-left:auto">${st.fin?'再读一遍':st.started?'继续阅读':'开始阅读'}</button></div>`,{tall:true});
  $('#bOpen')?.addEventListener('click',()=>{closeSheet();openBook(k);});""",
    """<button class="btn" id="bOpen" style="margin-left:auto">${guest?'登录后阅读':st.fin?'再读一遍':st.started?'继续阅读':'开始阅读'}</button></div>`,{tall:true});
  $('#bOpen')?.addEventListener('click',()=>{ closeSheet(); if(guest&&!curUser()){ AFTER_LOGIN=()=>openBook(k); AFTER_T=`登录后阅读《${b.t}》`; authPage('login'); } else openBook(k); });""")
# 访客看详情时不算进度、没有主线进度/伏笔数（没读过）——bookStat 对没记录的书本来就是"尚未开始"，无需改
# ---- ② 书架入口：导入 → 整页 ----
rep("""<label class="linkbtn" id="impBtn">导入<input type="file" id="impFile" hidden accept="${SRV.formats.map(x=>'.'+x).join(',')}"></label>""","""<button class="linkbtn" id="impBtn">导入</button>""")
rep("""  $('#shLib')?.addEventListener('click',()=>findPage());
  $('#shMe').onclick=()=>mePage();""","""  $('#shLib')?.addEventListener('click',()=>findPage());
  $('#impBtn')?.addEventListener('click',()=>importPage());
  $('#shMe').onclick=()=>mePage();""")
# 访客首页调用的 bookInfo(...,true)：openBook 里没登录也拦一下（防从别处直接调用）
rep("""function openBook(k){ dropBookTips(); setBook(k); reader(true); }""","""function openBook(k){ if((!window.__TEST||window.__GUESTCHK)&&!curUser()){ AFTER_LOGIN=()=>openBook(k); AFTER_T='登录后阅读'; return authPage('login'); } dropBookTips(); setBook(k); reader(true); }""")
# ---- CSS ----
rep('</style>',FR['css']+'</style>')
# ---- 测试钩子 ----
rep("if(window.__TEST) setTimeout(()=>window.__TEST({","if(window.__TEST) setTimeout(()=>window.__TEST({homePage,importPage,weekHTML,goAfter,setAfter:(f,t)=>{AFTER_LOGIN=f;AFTER_T=t||'';},")
# 10-30 自测发现：旧的 .week .d / .cal .d 圆角底色规则会和统一后的格子打架，删掉
s=s.replace(".week .d{border-radius:6px;background:var(--sheet)}\n.cal .d{border-radius:4px}\n","")
open(P,'w',encoding='utf-8').write(s); print('ok')
